"""
ai_integration.py - JARVIS v6.1 AI Module
7 providers · full fallback chain · multi-key OpenRouter · personality manager
All FREE tiers: Groq, Gemini, Mistral, NVIDIA NIM, OpenRouter, FreeLLMAPI, Ollama
"""

import json
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

CFG_FILE = Path(__file__).parent / "jarvis_config.json"

def _load_cfg() -> dict:
    if CFG_FILE.exists():
        with open(CFG_FILE) as f:
            return json.load(f)
    return {}


class OpenAICompatProvider:
    """Generic OpenAI-compatible /v1/chat/completions provider."""
    def __init__(self, name, base_url, api_key, model, extra_headers=None):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.extra_headers = extra_headers or {}

    def available(self):
        return bool(self.api_key and self.model)

    def chat(self, messages, system="", max_tokens=1024, tools=None, tool_choice="auto"):
        headers = {"Authorization": f"Bearer {self.api_key}",
                   "Content-Type": "application/json", **self.extra_headers}
        msgs = ([{"role": "system", "content": system}] if system else []) + messages
        payload = {"model": self.model, "messages": msgs, "max_tokens": max_tokens}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = tool_choice
            print(f"[DEBUG] Sending {len(tools)} tools to {self.name}")
        else:
            print(f"[DEBUG] No tools sent to {self.name}")

        print(f"[DEBUG] Payload model: {self.model}")
        print(f"[DEBUG] Payload keys: {list(payload.keys())}")

        try:
            r = requests.post(f"{self.base_url}/v1/chat/completions",
                              headers=headers,
                              json=payload,
                              timeout=60)
            r.raise_for_status()
            d = r.json()
            print(f"[DEBUG] === RAW GROQ RESPONSE ===")
            print(json.dumps(d, indent=2)[:1500])
            print(f"[DEBUG] ===========================")

            choice = d["choices"][0]
            response = choice["message"].get("content")
            tool_calls = choice["message"].get("tool_calls")
            print(f"[DEBUG] tool_calls is None? {tool_calls is None}")
            return {"ok": True, "response": response, "tool_calls": tool_calls,
                    "provider": self.name, "model": self.model,
                    "tokens": d.get("usage", {}).get("total_tokens", 0)}
        except Exception as e:
            print(f"[DEBUG] EXCEPTION in {self.name}: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"[DEBUG] Response text: {e.response.text}")
            return {"ok": False, "error": str(e), "provider": self.name}


class GroqProvider(OpenAICompatProvider):
    def __init__(self, api_key, model="mixtral-8x7b-32768"):
        super().__init__("groq", "https://api.groq.com/openai", api_key, model)


class GeminiProvider:
    name = "gemini"
    def __init__(self, api_key, model="gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model

    def available(self):
        return bool(self.api_key and self.model)

    def chat(self, messages, system="", max_tokens=1024):
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{self.model}:generateContent?key={self.api_key}")
        contents = []
        if system:
            contents += [{"role":"user","parts":[{"text":f"[System]: {system}"}]},
                         {"role":"model","parts":[{"text":"Understood."}]}]
        for m in messages:
            role = "model" if m["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
        try:
            r = requests.post(url, json={"contents": contents,
                              "generationConfig": {"maxOutputTokens": max_tokens,
                                                   "temperature": 0.7}}, timeout=60)
            r.raise_for_status()
            reply = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            return {"ok": True, "response": reply, "provider": "gemini", "model": self.model}
        except Exception as e:
            return {"ok": False, "error": str(e), "provider": "gemini"}


class MistralProvider(OpenAICompatProvider):
    def __init__(self, api_key, model="mistral-small-latest"):
        super().__init__("mistral", "https://api.mistral.ai", api_key, model)


class NvidiaProvider(OpenAICompatProvider):
    def __init__(self, api_key, model="meta/llama-3.1-70b-instruct"):
        super().__init__("nvidia", "https://integrate.api.nvidia.com", api_key, model)


class OpenRouterProvider(OpenAICompatProvider):
    """Supports multiple API keys — round-robin on failure."""
    def __init__(self, api_keys: List[str], model="openai/gpt-4o-mini"):
        self._keys = [k for k in api_keys if k]
        self._idx  = 0
        key = self._keys[0] if self._keys else ""
        super().__init__("openrouter", "https://openrouter.ai/api", key, model,
                         extra_headers={"HTTP-Referer": "http://127.0.0.1:5000",
                                        "X-Title": "JARVIS v6"})
    def available(self):
        return bool(self._keys and self.model)

    def _rotate(self):
        if len(self._keys) > 1:
            self._idx = (self._idx + 1) % len(self._keys)
            self.api_key = self._keys[self._idx]

    def chat(self, messages, system="", max_tokens=1024):
        for _ in range(len(self._keys) or 1):
            result = super().chat(messages, system, max_tokens)
            if result["ok"]:
                return result
            self._rotate()
        return result


class FreeLLMAPIProvider(OpenAICompatProvider):
    def __init__(self, api_key, base_url="http://localhost:8000",
                 model="gemini-2.0-flash"):
        super().__init__("freellmapi", base_url, api_key, model)


class OllamaProvider:
    name = "ollama"
    def __init__(self, base_url="http://localhost:11434", model="llama3.1"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = "ollama"

    def available(self):
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return r.status_code == 200 and bool(self.model)
        except Exception:
            return False

    def chat(self, messages, system="", max_tokens=1024):
        msgs = ([{"role":"system","content":system}] if system else []) + messages
        try:
            r = requests.post(f"{self.base_url}/v1/chat/completions",
                              json={"model": self.model, "messages": msgs, "stream": False},
                              timeout=120)
            r.raise_for_status()
            reply = r.json()["choices"][0]["message"]["content"]
            return {"ok": True, "response": reply, "provider": "ollama", "model": self.model}
        except Exception as e:
            return {"ok": False, "error": str(e), "provider": "ollama"}


class PersonalityManager:
    PERSONALITIES = {
        "jarvis":       ("You are J.A.R.V.I.S. (Just A Really Virtuous Intelligent System), "
                         "a sophisticated AI assistant. Be helpful, intelligent, slightly formal, "
                         "occasionally witty. Address the user respectfully."),
        "professional": "You are J.A.R.V.I.S., a professional AI assistant. Be concise and accurate.",
        "friendly":     "You are J.A.R.V.I.S., a warm friendly AI assistant. Be conversational.",
        "technical":    "You are J.A.R.V.I.S., a technical AI expert. Be detailed and precise.",
        "creative":     "You are J.A.R.V.I.S., a creative AI assistant. Be imaginative.",
    }

    def __init__(self, personality="jarvis"):
        self.current = personality

    def set_personality(self, name):
        if name not in self.PERSONALITIES:
            return {"ok": False, "error": f"Unknown: {name}. Options: {list(self.PERSONALITIES)}"}
        self.current = name
        return {"ok": True, "personality": name}

    def get_system_prompt(self):
        return self.PERSONALITIES.get(self.current, self.PERSONALITIES["jarvis"])

    def list_personalities(self):
        return {"ok": True, "personalities": list(self.PERSONALITIES), "current": self.current}


class ContextManager:
    def __init__(self, max_turns=20):
        self.history: List[Dict] = []
        self.preferences: Dict = {}
        self.max_turns = max_turns

    def add(self, role, content):
        self.history.append({"role": role, "content": content,
                             "ts": datetime.now().isoformat()})
        if len(self.history) > self.max_turns * 2:
            self.history = self.history[-(self.max_turns * 2):]

    def get_messages(self):
        return [{"role": m["role"], "content": m["content"]} for m in self.history]

    def get_context(self):
        return {"ok": True, "turns": len(self.history) // 2,
                "recent": self.history[-6:], "preferences": self.preferences}

    def clear(self):
        self.history = []
        return {"ok": True, "message": "Context cleared"}


class DualAISystem:
    """7-provider AI: Groq→Gemini→Mistral→NVIDIA→OpenRouter→FreeLLMAPI→Ollama fallback."""

    FALLBACK_ORDER = ["groq","gemini","mistral","nvidia","openrouter","freellmapi","ollama"]


    def __init__(self, groq_key="", gemini_key="", mistral_key="",
                 nvidia_key="", openrouter_keys=None, freellmapi_key="",
                 freellmapi_url="", ollama_url="", ollama_model="", **kwargs):

        cfg = _load_cfg().get("ai", {})

        def k(val, cfg_key): return val or cfg.get(cfg_key, "")

        or_keys = (openrouter_keys or
                   cfg.get("openrouter_keys") or
                   ([cfg["openrouter_key"]] if cfg.get("openrouter_key") else []))

        self.providers = {
            "groq":       GroqProvider(k(groq_key,"groq_api_key"), cfg.get("groq_model","mixtral-8x7b-32768")),
            "gemini":     GeminiProvider(k(gemini_key,"gemini_api_key"), cfg.get("gemini_model","gemini-1.5-flash")),
            "mistral":    MistralProvider(k(mistral_key,"mistral_api_key"), cfg.get("mistral_model","mistral-small-latest")),
            "nvidia":     NvidiaProvider(k(nvidia_key,"nvidia_api_key"), cfg.get("nvidia_model","meta/llama-3.1-70b-instruct")),
            "openrouter": OpenRouterProvider(or_keys, cfg.get("openrouter_model","openai/gpt-4o-mini")),
            "freellmapi": FreeLLMAPIProvider(k(freellmapi_key,"freellmapi_key"),
                                             k(freellmapi_url,"freellmapi_url") or "http://localhost:8000",
                                             cfg.get("freellmapi_model","gemini-2.0-flash")),
            "ollama":     OllamaProvider(k(ollama_url,"ollama_url") or "http://localhost:11434",
                                         k(ollama_model,"ollama_model") or "llama3.1"),
        }
        self.personality_manager = PersonalityManager(cfg.get("personality","jarvis"))
        self.context_manager     = ContextManager()
        self.primary             = cfg.get("primary","groq")
        self.last_provider       = None

    def chat(self, message, preferred_ai=None, max_tokens=1024, tools=None, tool_choice="auto"):
        self.context_manager.add("user", message)
        messages = self.context_manager.get_messages()
        system   = self.personality_manager.get_system_prompt()
        pref     = preferred_ai or self.primary
        order    = [pref] + [p for p in self.FALLBACK_ORDER if p != pref]
        errors   = []

        for name in order:
            p = self.providers.get(name)
            if not p or not p.available():
                errors.append(f"{name}: not configured")
                continue
            # Only OpenAI-compatible providers support tools
            print(f"[DEBUG] Calling {name} with tools: {tools is not None}")
            if name in ["groq", "mistral", "nvidia", "openrouter"]:
                result = p.chat(messages, system, max_tokens, tools=tools, tool_choice=tool_choice)
            else:
                result = p.chat(messages, system, max_tokens)
            if result.get("ok"):
                self.context_manager.add("assistant", result.get("response") or "")
                self.last_provider = name
                result["fallback_tried"] = errors
                return result
            errors.append(f"{name}: {result.get('error','failed')}")

        return {"ok": False, "error": "All AI providers failed.", "details": errors}

    def add_openrouter_key(self, api_key):
        p = self.providers["openrouter"]
        if api_key not in p._keys:
            p._keys.append(api_key)
        return {"ok": True, "message": f"Key added. Pool: {len(p._keys)} keys"}

    def set_model(self, provider, model):
        if provider not in self.providers:
            return {"ok": False, "error": f"Unknown provider: {provider}"}
        self.providers[provider].model = model
        return {"ok": True, "provider": provider, "model": model}

    def get_provider_status(self):
        status = {}
        for name, p in self.providers.items():
            status[name] = {"available": p.available(),
                            "model": getattr(p,"model",""),
                            "key_set": bool(getattr(p,"api_key","") and
                                           getattr(p,"api_key") not in ("","ollama"))}
            if name == "openrouter":
                status[name]["key_count"] = len(getattr(p,"_keys",[]))
        return {"ok": True, "providers": status,
                "last_used": self.last_provider, "primary": self.primary}

    def clear_context(self): return self.context_manager.clear()
    def get_context(self):   return self.context_manager.get_context()


AI_TOOLS = [
    {"type":"function","function":{
        "name":"chat_with_ai",
        "description":"Chat with JARVIS AI (Groq→Gemini→Mistral→NVIDIA→OpenRouter→FreeLLMAPI→Ollama fallback).",
        "parameters":{"type":"object","properties":{
            "message":{"type":"string"},
            "preferred_ai":{"type":"string","enum":["groq","gemini","mistral","nvidia","openrouter","freellmapi","ollama"]},
        },"required":["message"]}}},
    {"type":"function","function":{
        "name":"set_ai_personality",
        "description":"Set JARVIS personality.",
        "parameters":{"type":"object","properties":{
            "personality":{"type":"string","enum":["jarvis","professional","friendly","technical","creative"]},
        },"required":["personality"]}}},
    {"type":"function","function":{
        "name":"get_ai_context",
        "description":"Get current conversation context and history.",
        "parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{
        "name":"get_ai_provider_status",
        "description":"Get status of all 7 AI providers.",
        "parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{
        "name":"add_openrouter_key",
        "description":"Add an OpenRouter API key to the round-robin pool.",
        "parameters":{"type":"object","properties":{
            "api_key":{"type":"string"}
        },"required":["api_key"]}}},
    {"type":"function","function":{
        "name":"set_ai_model",
        "description":"Change model for a specific AI provider.",
        "parameters":{"type":"object","properties":{
            "provider":{"type":"string","enum":["groq","gemini","mistral","nvidia","openrouter","freellmapi","ollama"]},
            "model":{"type":"string"},
        },"required":["provider","model"]}}},
]
