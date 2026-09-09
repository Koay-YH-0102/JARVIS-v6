"""
tools_v6_patch.py  —  J.A.R.V.I.S. v6.1 tools extension
Adds 26 new tools (23 v6 + 3 Gmail) to the existing tools.py.

HOW TO INTEGRATE (4 lines in tools.py):

  from tools_v6_patch import V6_SAFE, V6_RISKY, V6_DISPATCH, V6_TOOL_SPECS

  SAFE_ACTIONS   = { ...existing... , *V6_SAFE   }
  RISKY_ACTIONS  = { ...existing... , *V6_RISKY  }
  DISPATCH       = { ...existing... , **V6_DISPATCH }
  TOOL_SPECS    += V6_TOOL_SPECS

Total after patch: 31 original + 10 browser + 5 calling + 26 v6 = 72 tools
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

CFG = Path(__file__).parent / "jarvis_config.json"

def _cfg():
    return json.loads(CFG.read_text()) if CFG.exists() else {}

# ── lazy singletons ──────────────────────────────────────────────

_smart = _ai = _phone = _bio = _gmail = None

def _get(name):
    global _smart, _ai, _phone, _bio, _gmail
    refs = {"smart": "_smart", "ai": "_ai", "phone": "_phone",
            "bio": "_bio", "gmail": "_gmail"}
    val = globals()[refs[name]]
    if val is not None:
        return val, None
    try:
        cfg = _cfg().get
        if name == "smart":
            from smart_features import SmartFeaturesManager
            _smart = SmartFeaturesManager(); return _smart, None
        elif name == "ai":
            from ai_integration import DualAISystem
            _ai = DualAISystem(); return _ai, None
        elif name == "phone":
            from phone_integration import PhoneManager
            _phone = PhoneManager(cfg("phone",{}).get("device_id"))
            return _phone, None
        elif name == "bio":
            from biometric_auth import DualAuthenticator
            _bio = DualAuthenticator(); return _bio, None
        elif name == "gmail":
            from gmail_integration import GmailClient
            _gmail = GmailClient(); return _gmail, None
    except Exception as e:
        return None, str(e)


# ─────────────────────────────────────────────────────────────
# Biometric
# ─────────────────────────────────────────────────────────────

def register_user_biometric(user_id: str, methods: list = None):
    g, e = _get("bio")
    if e: return {"ok": False, "error": e}
    return g.register_user(user_id, methods or ["face", "fingerprint"])

def authenticate_biometric(method: str = "any"):
    g, e = _get("bio")
    if e: return {"ok": False, "error": e}
    ok, detail = g.authenticate(method)
    return {"ok": ok, "detail": detail}

def get_biometric_status():
    g, e = _get("bio")
    if e: return {"ok": False, "error": e}
    return g.get_status()


# ─────────────────────────────────────────────────────────────
# Voice
# ─────────────────────────────────────────────────────────────

def listen_voice_command(timeout: int = 10, language: str = "en-US"):
    try:
        from voice_speech import SpeechRecognizer
        return SpeechRecognizer(language=language).listen(timeout=timeout)
    except Exception as e:
        return {"ok": False, "error": str(e)}

def speak_response(text: str, gender: str = "female", rate: int = 150):
    try:
        from voice_speech import TextToSpeech
        tts = TextToSpeech()
        tts.set_rate(rate)
        return tts.speak(text, gender=gender)
    except Exception as e:
        return {"ok": False, "error": str(e)}

def set_voice_language(language: str):
    return {"ok": True, "language": language,
            "message": f"Language set to {language}."}

def start_hotword_detection(hotwords: list = None):
    try:
        from voice_speech import HotwordDetector
        det = HotwordDetector(hotwords=hotwords or ["jarvis", "hey jarvis"])
        det.start_listening()
        return {"ok": True, "message": f"Hotword detection started."}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def get_voice_status():
    try:
        from voice_speech import VoiceCommandProcessor
        vcp = VoiceCommandProcessor()
        return {"ok": True, "speech": vcp.recognizer.get_status(), "tts": vcp.tts.get_status()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────
# AI
# ─────────────────────────────────────────────────────────────

def chat_with_ai(message: str, preferred_ai: str = None):
    g, e = _get("ai")
    if e: return {"ok": False, "error": e}
    return g.chat(message, preferred_ai)

def set_ai_personality(personality: str):
    g, e = _get("ai")
    if e: return {"ok": False, "error": e}
    return g.personality_manager.set_personality(personality)

def get_ai_context():
    g, e = _get("ai")
    if e: return {"ok": False, "error": e}
    return g.get_context()

def get_ai_provider_status():
    g, e = _get("ai")
    if e: return {"ok": False, "error": e}
    return g.get_provider_status()

def add_openrouter_key(api_key: str):
    g, e = _get("ai")
    if e: return {"ok": False, "error": e}
    return g.add_openrouter_key(api_key)

def set_ai_model(provider: str, model: str):
    g, e = _get("ai")
    if e: return {"ok": False, "error": e}
    return g.set_model(provider, model)


# ─────────────────────────────────────────────────────────────
# Phone
# ─────────────────────────────────────────────────────────────

def read_sms(limit: int = 10):
    g, e = _get("phone")
    if e: return {"ok": False, "error": e}
    return g.sms.read_sms(limit)

def send_sms(phone_number: str, message: str):
    g, e = _get("phone")
    if e: return {"ok": False, "error": e}
    return g.sms.send_sms(phone_number, message)

def send_whatsapp(phone_number: str, message: str):
    g, e = _get("phone")
    if e: return {"ok": False, "error": e}
    return g.whatsapp.send_whatsapp_message(phone_number, message)

def get_call_history(limit: int = 10):
    g, e = _get("phone")
    if e: return {"ok": False, "error": e}
    return g.calls.get_call_history(limit)

def get_device_info():
    g, e = _get("phone")
    if e: return {"ok": False, "error": e}
    return g.remote.get_device_info()


# ─────────────────────────────────────────────────────────────
# Gmail
# ─────────────────────────────────────────────────────────────

def gmail_list_emails(max_results: int = 10, label: str = "INBOX", query: str = ""):
    g, e = _get("gmail")
    if e: return {"ok": False, "error": e}
    return g.list_emails(max_results, label, query)

def gmail_search(query: str, max_results: int = 10):
    g, e = _get("gmail")
    if e: return {"ok": False, "error": e}
    return g.search_emails(query, max_results)

def gmail_send(to: str, subject: str, body: str, cc: str = "", bcc: str = ""):
    g, e = _get("gmail")
    if e: return {"ok": False, "error": e}
    return g.send_email(to, subject, body, cc=cc, bcc=bcc)

def gmail_reply(email_id: str, body: str):
    g, e = _get("gmail")
    if e: return {"ok": False, "error": e}
    return g.reply_email(email_id, body)

def gmail_trash(email_id: str):
    g, e = _get("gmail")
    if e: return {"ok": False, "error": e}
    return g.trash_email(email_id)

def gmail_get_profile():
    g, e = _get("gmail")
    if e: return {"ok": False, "error": e}
    return g.get_profile()

def gmail_unread_count():
    g, e = _get("gmail")
    if e: return {"ok": False, "error": e}
    return g.get_unread_count()


# ─────────────────────────────────────────────────────────────
# Smart
# ─────────────────────────────────────────────────────────────

def detect_emotion(text: str):
    g, e = _get("smart")
    if e: return {"ok": False, "error": e}
    return g.analyse_emotion(text)

def get_proactive_suggestions(context_text: str = ""):
    g, e = _get("smart")
    if e: return {"ok": False, "error": e}
    return g.get_suggestions(context_text)

def get_analytics_summary():
    g, e = _get("smart")
    if e: return {"ok": False, "error": e}
    return g.get_analytics_summary()

def search_command_history(query: str, limit: int = 20):
    g, e = _get("smart")
    if e: return {"ok": False, "error": e}
    return g.search_history(query, limit)

def get_user_preferences():
    g, e = _get("smart")
    if e: return {"ok": False, "error": e}
    return g.get_preferences()

def enable_autostart(script_path: str = None):
    g, e = _get("smart")
    if e: return {"ok": False, "error": e}
    return g.enable_autostart(script_path or str(Path(__file__).parent / "jarvis_core.py"))

def disable_autostart():
    g, e = _get("smart")
    if e: return {"ok": False, "error": e}
    return g.disable_autostart()


# ─────────────────────────────────────────────────────────────
# Safety sets
# ─────────────────────────────────────────────────────────────

V6_SAFE = {
    "get_biometric_status",
    "set_voice_language", "get_voice_status",
    "chat_with_ai", "set_ai_personality", "get_ai_context",
    "get_ai_provider_status", "set_ai_model",
    "read_sms", "get_call_history", "get_device_info",
    "gmail_list_emails", "gmail_search", "gmail_get_profile",
    "gmail_unread_count",
    "detect_emotion", "get_proactive_suggestions",
    "get_analytics_summary", "search_command_history",
    "get_user_preferences",
}

V6_RISKY = {
    "register_user_biometric", "authenticate_biometric",
    "listen_voice_command", "speak_response", "start_hotword_detection",
    "add_openrouter_key",
    "send_sms", "send_whatsapp",
    "gmail_send", "gmail_reply", "gmail_trash",
    "enable_autostart", "disable_autostart",
}

# ─────────────────────────────────────────────────────────────
# Dispatch
# ─────────────────────────────────────────────────────────────

V6_DISPATCH = {
    "register_user_biometric":  register_user_biometric,
    "authenticate_biometric":   authenticate_biometric,
    "get_biometric_status":     get_biometric_status,
    "listen_voice_command":     listen_voice_command,
    "speak_response":           speak_response,
    "set_voice_language":       set_voice_language,
    "start_hotword_detection":  start_hotword_detection,
    "get_voice_status":         get_voice_status,
    "chat_with_ai":             chat_with_ai,
    "set_ai_personality":       set_ai_personality,
    "get_ai_context":           get_ai_context,
    "get_ai_provider_status":   get_ai_provider_status,
    "add_openrouter_key":       add_openrouter_key,
    "set_ai_model":             set_ai_model,
    "read_sms":                 read_sms,
    "send_sms":                 send_sms,
    "send_whatsapp":            send_whatsapp,
    "get_call_history":         get_call_history,
    "get_device_info":          get_device_info,
    "gmail_list_emails":        gmail_list_emails,
    "gmail_search":             gmail_search,
    "gmail_send":               gmail_send,
    "gmail_reply":              gmail_reply,
    "gmail_trash":              gmail_trash,
    "gmail_get_profile":        gmail_get_profile,
    "gmail_unread_count":       gmail_unread_count,
    "detect_emotion":           detect_emotion,
    "get_proactive_suggestions":get_proactive_suggestions,
    "get_analytics_summary":    get_analytics_summary,
    "search_command_history":   search_command_history,
    "get_user_preferences":     get_user_preferences,
    "enable_autostart":         enable_autostart,
    "disable_autostart":        disable_autostart,
}

# ─────────────────────────────────────────────────────────────
# Tool schemas
# ─────────────────────────────────────────────────────────────

V6_TOOL_SPECS = [
    # Biometric
    {"type":"function","function":{"name":"register_user_biometric",
     "description":"RISKY: Register face/fingerprint for biometric auth.",
     "parameters":{"type":"object","properties":{
       "user_id":{"type":"string"},
       "methods":{"type":"array","items":{"type":"string"},"description":"['face'],['fingerprint'],or both"}
     },"required":["user_id"]}}},
    {"type":"function","function":{"name":"authenticate_biometric",
     "description":"RISKY: Authenticate via face or fingerprint.",
     "parameters":{"type":"object","properties":{
       "method":{"type":"string","enum":["face","fingerprint","any"]}
     }}}},
    {"type":"function","function":{"name":"get_biometric_status",
     "description":"Get biometric system status and registered users.",
     "parameters":{"type":"object","properties":{}}}},
    # Voice
    {"type":"function","function":{"name":"listen_voice_command",
     "description":"RISKY: Listen via microphone and transcribe speech.",
     "parameters":{"type":"object","properties":{
       "timeout":{"type":"integer"},
       "language":{"type":"string","description":"BCP-47 code e.g. en-US"}
     }}}},
    {"type":"function","function":{"name":"speak_response",
     "description":"RISKY: Speak text aloud via TTS.",
     "parameters":{"type":"object","properties":{
       "text":{"type":"string"},
       "gender":{"type":"string","enum":["male","female"]},
       "rate":{"type":"integer"}
     },"required":["text"]}}},
    {"type":"function","function":{"name":"set_voice_language",
     "description":"Set voice recognition and TTS language.",
     "parameters":{"type":"object","properties":{
       "language":{"type":"string"}
     },"required":["language"]}}},
    {"type":"function","function":{"name":"start_hotword_detection",
     "description":"RISKY: Start always-on wake-word detection ('Hey Jarvis').",
     "parameters":{"type":"object","properties":{
       "hotwords":{"type":"array","items":{"type":"string"}}
     }}}},
    {"type":"function","function":{"name":"get_voice_status",
     "description":"Get voice system status and available languages.",
     "parameters":{"type":"object","properties":{}}}},
    # AI
    {"type":"function","function":{"name":"chat_with_ai",
     "description":"Chat with AI — tries Groq→Gemini→Mistral→NVIDIA→OpenRouter→FreeLLMAPI→Ollama.",
     "parameters":{"type":"object","properties":{
       "message":{"type":"string"},
       "preferred_ai":{"type":"string","enum":["groq","gemini","mistral","nvidia","openrouter","freellmapi","ollama"]}
     },"required":["message"]}}},
    {"type":"function","function":{"name":"set_ai_personality",
     "description":"Set JARVIS AI personality.",
     "parameters":{"type":"object","properties":{
       "personality":{"type":"string","enum":["jarvis","professional","friendly","technical","creative"]}
     },"required":["personality"]}}},
    {"type":"function","function":{"name":"get_ai_context",
     "description":"Get current conversation context.",
     "parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{"name":"get_ai_provider_status",
     "description":"Get status of all 7 AI providers.",
     "parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{"name":"add_openrouter_key",
     "description":"RISKY: Add an OpenRouter API key to the round-robin pool.",
     "parameters":{"type":"object","properties":{
       "api_key":{"type":"string"}
     },"required":["api_key"]}}},
    {"type":"function","function":{"name":"set_ai_model",
     "description":"Change model for a specific AI provider.",
     "parameters":{"type":"object","properties":{
       "provider":{"type":"string","enum":["groq","gemini","mistral","nvidia","openrouter","freellmapi","ollama"]},
       "model":{"type":"string"}
     },"required":["provider","model"]}}},
    # Phone
    {"type":"function","function":{"name":"read_sms",
     "description":"Read recent SMS messages from Android device via ADB.",
     "parameters":{"type":"object","properties":{
       "limit":{"type":"integer"}
     }}}},
    {"type":"function","function":{"name":"send_sms",
     "description":"RISKY: Send SMS via Android device.",
     "parameters":{"type":"object","properties":{
       "phone_number":{"type":"string"},
       "message":{"type":"string"}
     },"required":["phone_number","message"]}}},
    {"type":"function","function":{"name":"send_whatsapp",
     "description":"RISKY: Open WhatsApp with a pre-filled message on Android device.",
     "parameters":{"type":"object","properties":{
       "phone_number":{"type":"string"},
       "message":{"type":"string"}
     },"required":["phone_number","message"]}}},
    {"type":"function","function":{"name":"get_call_history",
     "description":"Get call history from Android device.",
     "parameters":{"type":"object","properties":{
       "limit":{"type":"integer"}
     }}}},
    {"type":"function","function":{"name":"get_device_info",
     "description":"Get connected Android device info (model, Android version, battery).",
     "parameters":{"type":"object","properties":{}}}},
    # Gmail
    {"type":"function","function":{"name":"gmail_list_emails",
     "description":"List emails from Gmail inbox or any label.",
     "parameters":{"type":"object","properties":{
       "max_results":{"type":"integer"},
       "label":{"type":"string","description":"Gmail label (default INBOX)"},
       "query":{"type":"string","description":"Gmail search query"}
     }}}},
    {"type":"function","function":{"name":"gmail_search",
     "description":"Search Gmail using query syntax (from:, subject:, is:unread, after:, etc.)",
     "parameters":{"type":"object","properties":{
       "query":{"type":"string"},
       "max_results":{"type":"integer"}
     },"required":["query"]}}},
    {"type":"function","function":{"name":"gmail_send",
     "description":"RISKY: Send an email via Gmail.",
     "parameters":{"type":"object","properties":{
       "to":{"type":"string"},
       "subject":{"type":"string"},
       "body":{"type":"string"},
       "cc":{"type":"string"},
       "bcc":{"type":"string"}
     },"required":["to","subject","body"]}}},
    {"type":"function","function":{"name":"gmail_reply",
     "description":"RISKY: Reply to an email.",
     "parameters":{"type":"object","properties":{
       "email_id":{"type":"string"},
       "body":{"type":"string"}
     },"required":["email_id","body"]}}},
    {"type":"function","function":{"name":"gmail_trash",
     "description":"RISKY: Move an email to Gmail trash.",
     "parameters":{"type":"object","properties":{
       "email_id":{"type":"string"}
     },"required":["email_id"]}}},
    {"type":"function","function":{"name":"gmail_get_profile",
     "description":"Get connected Gmail account info and message counts.",
     "parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{"name":"gmail_unread_count",
     "description":"Get number of unread emails in Gmail.",
     "parameters":{"type":"object","properties":{}}}},
    # Smart
    {"type":"function","function":{"name":"detect_emotion",
     "description":"Detect user emotion from text (happy, sad, angry, anxious, neutral).",
     "parameters":{"type":"object","properties":{
       "text":{"type":"string"}
     },"required":["text"]}}},
    {"type":"function","function":{"name":"get_proactive_suggestions",
     "description":"Get context-aware proactive suggestions based on time, emotion, and usage.",
     "parameters":{"type":"object","properties":{
       "context_text":{"type":"string"}
     }}}},
    {"type":"function","function":{"name":"get_analytics_summary",
     "description":"Get command analytics: total, success rate, top categories.",
     "parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{"name":"search_command_history",
     "description":"Search past JARVIS commands.",
     "parameters":{"type":"object","properties":{
       "query":{"type":"string"},
       "limit":{"type":"integer"}
     },"required":["query"]}}},
    {"type":"function","function":{"name":"get_user_preferences",
     "description":"Get learned user preferences (language, voice, AI, top apps).",
     "parameters":{"type":"object","properties":{}}}},
    {"type":"function","function":{"name":"enable_autostart",
     "description":"RISKY: Register JARVIS to launch at system boot.",
     "parameters":{"type":"object","properties":{
       "script_path":{"type":"string"}
     }}}},
    {"type":"function","function":{"name":"disable_autostart",
     "description":"RISKY: Remove JARVIS from auto-start.",
     "parameters":{"type":"object","properties":{}}}},
]

# Sanity check
assert set(V6_DISPATCH) == V6_SAFE | V6_RISKY, (
    f"Mismatch — extra: {set(V6_DISPATCH)-(V6_SAFE|V6_RISKY)}, "
    f"missing: {(V6_SAFE|V6_RISKY)-set(V6_DISPATCH)}"
)
print(f"  tools_v6_patch: {len(V6_DISPATCH)} tools ({len(V6_SAFE)} safe, {len(V6_RISKY)} risky)")
