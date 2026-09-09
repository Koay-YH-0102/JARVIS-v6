"""
jarvis_core.py - JARVIS v6 Core Integration (FINAL)
Unified system integrating ALL modules including smart features.
"""

import json
import os
import sys
import signal
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from biometric_auth    import DualAuthenticator,     BIOMETRIC_TOOLS
from voice_speech      import VoiceCommandProcessor, VOICE_SPEECH_TOOLS
from ai_integration    import DualAISystem,          AI_TOOLS
from phone_integration import PhoneManager,          PHONE_TOOLS
from system_control    import (ApplicationManager, FileManager,
                                SystemMonitor, TaskScheduler,
                                SYSTEM_CONTROL_TOOLS)
from smart_features    import SmartFeaturesManager,  SMART_TOOLS

CONFIG_FILE = Path(__file__).parent / "jarvis_config.json"
DEFAULT_CONFIG: Dict = {
    "system":  {"name": "J.A.R.V.I.S.", "version": "6.0", "mode": "hybrid"},
    "biometric": {"enabled": True, "face_recognition": True, "fingerprint": True},
    "voice":   {"enabled": True, "default_language": "en-US", "hotword": "jarvis",
                 "tts_gender": "female", "tts_rate": 150},
    "ai":      {"enabled": True, "primary": "groq",
                 "groq_api_key": "", "gemini_api_key": "",
                 "personality": "professional"},
    "phone":   {"enabled": True, "device_id": None},
    "web_interface": {"enabled": True, "host": "127.0.0.1", "port": 5000},
    "smart":   {"enabled": True, "emotion_detection": True, "proactive": True},
    "auto_start": {"enabled": False, "services": ["web_interface", "hotword_detection"]},
}


class JARVISCore:
    VERSION = "6.0"

    def __init__(self, config_path: str = None):
        self.config       = self._load_config(config_path)
        self.startup_time = datetime.now()
        self._running     = True

        print(f"\n{'='*54}")
        print(f"  J.A.R.V.I.S. v{self.VERSION}  —  Booting...")
        print(f"{'='*54}")

        self.auth      = self._init("biometric",     self._boot_biometric)
        self.voice     = self._init("voice",         self._boot_voice)
        self.ai        = self._init("ai",            self._boot_ai)
        self.phone     = self._init("phone",         self._boot_phone)
        self.apps      = ApplicationManager()
        self.files     = FileManager()
        self.monitor   = SystemMonitor()
        self.scheduler = TaskScheduler()
        self.smart     = SmartFeaturesManager() if self.config["smart"]["enabled"] else None
        self.web       = self._init("web_interface", self._boot_web)

        if self.config["auto_start"]["enabled"]:
            self._auto_start()

        print(f"{'='*54}")
        print(f"  JARVIS v{self.VERSION} ready!\n")

    def set_personality(self, name: str) -> Dict:
        """Set JARVIS's AI personality."""
        if not self.ai:
            return {"ok": False, "error": "AI unavailable"}
        return self.ai.personality_manager.set_personality(name)

    def _execute_tool(self, tool_name, args):
        """Execute a tool based on its name and arguments."""
        tool_map = {
            "open_app": self.open_app,
            "close_app": self.close_app,
            "list_running_apps": self.list_apps,
            "get_system_stats": self.get_stats,
            "schedule_task": self.schedule_task,
            "send_sms": lambda phone_number, message: self.send_sms(phone_number, message),
            "read_sms": self.read_sms,
            "send_whatsapp": lambda phone_number, message: self.send_whatsapp(phone_number, message),
            "get_call_history": self.get_call_history,
            "get_device_info": self.get_device_info,
            "register_user_biometric": self.register_user,
            "authenticate_biometric": self.authenticate,
            "get_biometric_status": self.get_biometric_status,
            "listen_voice_command": lambda timeout=10, language="en-US": self.listen(timeout),
            "speak_response": self.speak,
            "set_voice_language": self.set_language,
            "start_hotword_detection": self.start_hotword,
            "set_ai_personality": self.set_personality,
            "get_ai_context": self.ai.context_manager.get_context if self.ai else None,
            "get_ai_provider_status": self.ai.get_provider_status if self.ai else None,
            "add_openrouter_key": self.ai.add_openrouter_key if self.ai else None,
            "set_ai_model": self.ai.set_model if self.ai else None,
            "detect_emotion": self.detect_emotion,
            "get_proactive_suggestions": self.get_suggestions,
            "get_analytics_summary": self.get_analytics,
            "search_command_history": self.search_history,
            "get_user_preferences": self.get_preferences,
            "enable_autostart": self.enable_autostart,
            "disable_autostart": self.disable_autostart,
            # Gmail tools
            "gmail_list_emails": self._gmail_wrapper("list_emails"),
            "gmail_search": self._gmail_wrapper("search_emails"),
            "gmail_send": self._gmail_wrapper("send_email"),
            "gmail_reply": self._gmail_wrapper("reply_email"),
            "gmail_trash": self._gmail_wrapper("trash_email"),
            "gmail_get_profile": self._gmail_wrapper("get_profile"),
            "gmail_unread_count": self._gmail_wrapper("get_unread_count"),
            "gmail_mark_read": self._gmail_wrapper("mark_as_read"),
            "gmail_add_label": self._gmail_wrapper("add_label"),
        }

        if tool_name not in tool_map:
            return {"ok": False, "error": f"Unknown tool: {tool_name}"}
        fn = tool_map[tool_name]
        if fn is None:
            return {"ok": False, "error": f"Tool {tool_name} not available"}
        try:
            result = fn(**args) if args else fn()
            if isinstance(result, dict):
                return result
            return {"ok": True, "message": str(result)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # --Gmail--
    def _gmail_wrapper(self, method_name):
        """Return a function that calls the Gmail API."""
        def wrapper(**kwargs):
            try:
                from gmail_integration import GmailClient
                g = GmailClient()
                result = getattr(g, method_name)(**kwargs)
                return result
            except Exception as e:
                return {"ok": False, "error": str(e)}
        return wrapper


    # -- Tool Calling --
    def _execute_tool(self, tool_name, args):
        """Execute a tool based on its name and arguments."""
        # Map tool names to core methods
        tool_map = {
            "open_app": self.open_app,
            "close_app": self.close_app,
            "list_running_apps": self.list_apps,
            "get_system_stats": self.get_stats,
            "schedule_task": self.schedule_task,
            "send_sms": self.send_sms,
            "read_sms": self.read_sms,
            "send_whatsapp": self.send_whatsapp,
            "get_call_history": self.get_call_history,
            "get_device_info": self.get_device_info,
            "register_user_biometric": self.register_user,
            "authenticate_biometric": self.authenticate,
            "get_biometric_status": self.get_biometric_status,
            "listen_voice_command": self.listen,
            "speak_response": self.speak,
            "set_voice_language": self.set_language,
            "start_hotword_detection": self.start_hotword,
            "set_ai_personality": self.set_personality,
            "get_ai_context": self.ai.context_manager.get_context if self.ai else None,
            "get_ai_provider_status": self.ai.get_provider_status if self.ai else None,
            "add_openrouter_key": self.ai.add_openrouter_key if self.ai else None,
            "set_ai_model": self.ai.set_model if self.ai else None,
            "detect_emotion": self.detect_emotion,
            "get_proactive_suggestions": self.get_suggestions,
            "get_analytics_summary": self.get_analytics,
            "search_command_history": self.search_history,
            "get_user_preferences": self.get_preferences,
            "enable_autostart": self.enable_autostart,
            "disable_autostart": self.disable_autostart,
            # Gmail tools
            "gmail_list_emails": self._gmail_wrapper("list_emails"),
            "gmail_search": self._gmail_wrapper("search_emails"),
            "gmail_send": self._gmail_wrapper("send_email"),
            "gmail_reply": self._gmail_wrapper("reply_email"),
            "gmail_trash": self._gmail_wrapper("trash_email"),
            "gmail_get_profile": self._gmail_wrapper("get_profile"),
            "gmail_unread_count": self._gmail_wrapper("get_unread_count"),
            "gmail_mark_read": self._gmail_wrapper("mark_as_read"),
            "gmail_add_label": self._gmail_wrapper("add_label"),
        }

        if tool_name not in tool_map:
            return {"ok": False, "error": f"Unknown tool: {tool_name}"}

        fn = tool_map[tool_name]
        if fn is None:
            return {"ok": False, "error": f"Tool {tool_name} not available"}

        try:
            result = fn(**args) if args else fn()
            if isinstance(result, dict):
                return result
            return {"ok": True, "message": str(result)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Config ─────────────────────────────────────────────────

    def _load_config(self, path=None) -> Dict:
        target = Path(path) if path else CONFIG_FILE
        if target.exists():
            with open(target) as f:
                user = json.load(f)
            merged = json.loads(json.dumps(DEFAULT_CONFIG))
            for k, v in user.items():
                if isinstance(v, dict):
                    merged.setdefault(k, {}).update(v)
                else:
                    merged[k] = v
            return merged
        self._save_config(DEFAULT_CONFIG)
        return json.loads(json.dumps(DEFAULT_CONFIG))

    def _save_config(self, cfg: Dict = None):
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg or self.config, f, indent=2)

    # ── Boot helpers ───────────────────────────────────────────

    def _init(self, key: str, boot_fn):
        try:
            obj = boot_fn()
            if obj is not None:
                return obj
        except Exception as e:
            print(f"  ✗  {key}: {e}")
        return None

    def _boot_biometric(self):
        if not self.config["biometric"]["enabled"]:
            return None
        obj = DualAuthenticator()
        print("  ✓  Biometric auth")
        return obj

    def _boot_voice(self):
        if not self.config["voice"]["enabled"]:
            return None
        obj = VoiceCommandProcessor()
        obj.set_language(self.config["voice"]["default_language"])
        obj.tts.set_rate(self.config["voice"]["tts_rate"])
        print("  ✓  Voice system")
        return obj

    def _boot_ai(self):
        if not self.config["ai"]["enabled"]:
            return None
        c = self.config["ai"]
        obj = DualAISystem(groq_key=c.get("groq_api_key",""),
                           gemini_key=c.get("gemini_api_key",""))
        obj.personality_manager.set_personality(c.get("personality","professional"))
        print("  ✓  AI system (Groq + Gemini)")
        return obj

    def _boot_phone(self):
        if not self.config["phone"]["enabled"]:
            return None
        obj = PhoneManager(self.config["phone"].get("device_id"))
        print("  ✓  Phone integration (ADB)")
        return obj

    def _boot_web(self):
        if not self.config["web_interface"]["enabled"]:
            return None
        from web_interface import JarvisWebInterface
        wc = self.config["web_interface"]
        obj = JarvisWebInterface(host=wc["host"], port=wc["port"], jarvis_core=self)
        print(f"  ✓  Web interface  http://{wc['host']}:{wc['port']}")
        return obj

    def _auto_start(self):
        svcs = self.config["auto_start"].get("services", [])
        if "web_interface"    in svcs and self.web:   self.start_web()
        if "hotword_detection" in svcs and self.voice: self.start_hotword()

    # ─────────────────────────────────────────────────────────
    # Voice
    # ─────────────────────────────────────────────────────────

    def listen(self, timeout: int = 10) -> Dict:
        if not self.voice:
            return {"ok": False, "error": "Voice unavailable"}
        result = self.voice.process_voice_command(timeout=timeout)
        if result["ok"] and self.smart:
            self.smart.record_command(result["command"], True, "voice")
        return result

    def speak(self, text: str, gender: str = None) -> Dict:
        if not self.voice:
            return {"ok": False, "error": "Voice unavailable"}
        g = gender or self.config["voice"].get("tts_gender", "female")
        return self.voice.respond(text, gender=g)

    def start_hotword(self) -> Dict:
        if not self.voice:
            return {"ok": False, "error": "Voice unavailable"}
        hw = self.config["voice"].get("hotword", "jarvis")
        self.voice.hotword_detector.set_hotwords([hw, f"hey {hw}"])
        return self.voice.hotword_detector.start_listening(
            callback=lambda e: self._on_hotword(e))

    def _on_hotword(self, event: Dict):
        print(f"\n  Hotword: {event.get('hotword')} — listening...")
        r = self.listen(timeout=8)
        if r["ok"]:
            ai = self.chat(r["command"])
            if ai["ok"]:
                self.speak(ai["response"])

    def set_language(self, lang: str) -> Dict:
        if not self.voice:
            return {"ok": False, "error": "Voice unavailable"}
        r = self.voice.set_language(lang)
        if r["ok"] and self.smart:
            self.smart.learner.on_language_used(lang)
        return r

    # ─────────────────────────────────────────────────────────
    # Biometric
    # ─────────────────────────────────────────────────────────

    def register_user(self, user_id: str, methods: List[str] = None) -> Dict:
        if not self.auth:
            return {"ok": False, "error": "Biometric unavailable"}
        return self.auth.register_user(user_id, methods or ["face","fingerprint"])

    def authenticate(self, method: str = "any") -> Dict:
        if not self.auth:
            return {"ok": False, "error": "Biometric unavailable"}
        ok, detail = self.auth.authenticate(method)
        return {"ok": ok, "detail": detail}

    def get_biometric_status(self) -> Dict:
        if not self.auth:
            return {"ok": False, "error": "Biometric unavailable"}
        return self.auth.get_status()

    # ─────────────────────────────────────────────────────────
    # AI
    # ─────────────────────────────────────────────────────────

    def chat(self, message, preferred_ai=None, tools_enabled=True):
        if not self.ai:
            return {"ok": False, "error": "AI unavailable"}

        # Gather all tool specs
        tool_specs = self.ALL_TOOL_SPECS if tools_enabled else None

        # Call AI with tools
        result = self.ai.chat(message, preferred_ai, tools=tool_specs, tool_choice="required")

        if not result.get("ok"):
            return result

        # Check for tool calls
        tool_calls = result.get("tool_calls")
        if tool_calls:
            executed = []
            for tc in tool_calls:
                fn_name = tc.get("function", {}).get("name")
                fn_args = json.loads(tc.get("function", {}).get("arguments", "{}"))
                exec_result = self._execute_tool(fn_name, fn_args)
                executed.append({"tool": fn_name, "result": exec_result})

            # Build response
            results_text = "\n".join([f"✓ {e['tool']}: {e['result'].get('message', 'done')}" for e in executed])
            return {
                "ok": True,
                "response": f"I executed these actions:\n{results_text}",
                "executed": executed,
            }
        else:
            # Normal text response
            self.ai.context_manager.add("assistant", result.get("response"))
            return {"ok": True, "response": result.get("response")}
        
        tool_specs = self.ALL_TOOL_SPECS if tools_enabled else None
        print(f"[DEBUG] tools_enabled={tools_enabled}, tool_specs count={len(tool_specs) if tool_specs else 0}")
        result = self.ai.chat(message, preferred_ai, tools=tool_specs)

    # ─────────────────────────────────────────────────────────
    # Phone
    # ─────────────────────────────────────────────────────────

    def send_sms(self, phone: str, msg: str) -> Dict:
        if not self.phone: return {"ok": False, "error": "Phone unavailable"}
        return self.phone.sms.send_sms(phone, msg)

    def read_sms(self, limit: int = 10) -> Dict:
        if not self.phone: return {"ok": False, "error": "Phone unavailable"}
        return self.phone.sms.read_sms(limit)

    def send_whatsapp(self, phone: str, msg: str) -> Dict:
        if not self.phone: return {"ok": False, "error": "Phone unavailable"}
        return self.phone.whatsapp.send_whatsapp_message(phone, msg)

    def get_call_history(self, limit: int = 10) -> Dict:
        if not self.phone: return {"ok": False, "error": "Phone unavailable"}
        return self.phone.calls.get_call_history(limit)

    def get_device_info(self) -> Dict:
        if not self.phone: return {"ok": False, "error": "Phone unavailable"}
        return self.phone.remote.get_device_info()

    # ─────────────────────────────────────────────────────────
    # System
    # ─────────────────────────────────────────────────────────

    def open_app(self, app_name: str) -> Dict:
        print(f"[DEBUG] open_app called with app_name: {app_name}")
        r = self.apps.open_application(app_name)
        print(f"[DEBUG] open_application result: {r}")
        if self.smart:
            self.smart.learner.on_app_open(app_name)
            self.smart.record_command(f"open {app_name}", r.get("ok", False))
        return r

    def close_app(self, app: str) -> Dict:
        return self.apps.close_application(app)

    def list_apps(self) -> Dict:
        return self.apps.list_running_apps()

    def get_stats(self) -> Dict:
        return self.monitor.get_system_stats()

    def schedule_task(self, name: str, cmd: str, interval: int = 60) -> Dict:
        return self.scheduler.schedule_task(name, cmd, interval)

    def create_reminder(self, text: str, minutes: int = 15) -> Dict:
        return self.scheduler.create_reminder(text, minutes)

    def list_tasks(self) -> Dict:
        return self.scheduler.get_tasks()

    def create_folder(self, path: str) -> Dict:
        return self.files.create_folder(path)

    def list_files(self, path: str) -> Dict:
        return self.files.list_files(path)

    def copy_file(self, src: str, dst: str) -> Dict:
        return self.files.copy_file(src, dst)

    def move_file(self, src: str, dst: str) -> Dict:
        return self.files.move_file(src, dst)

    # ─────────────────────────────────────────────────────────
    # Smart
    # ─────────────────────────────────────────────────────────

    def get_suggestions(self, ctx: str = "") -> Dict:
        if not self.smart: return {"ok": False, "error": "Smart unavailable"}
        return self.smart.get_suggestions(ctx)

    def detect_emotion(self, text: str) -> Dict:
        if not self.smart: return {"ok": False, "error": "Smart unavailable"}
        return self.smart.analyse_emotion(text)

    def search_history(self, q: str, limit: int = 20) -> Dict:
        if not self.smart: return {"ok": False, "error": "Smart unavailable"}
        return self.smart.search_history(q, limit)

    def get_analytics(self) -> Dict:
        if not self.smart: return {"ok": False, "error": "Smart unavailable"}
        return self.smart.get_analytics_summary()

    def get_preferences(self) -> Dict:
        if not self.smart: return {"ok": False, "error": "Smart unavailable"}
        return self.smart.get_preferences()

    def enable_autostart(self) -> Dict:
        if not self.smart: return {"ok": False, "error": "Smart unavailable"}
        return self.smart.enable_autostart(str(Path(__file__).resolve()))

    def disable_autostart(self) -> Dict:
        if not self.smart: return {"ok": False, "error": "Smart unavailable"}
        return self.smart.disable_autostart()

    # ─────────────────────────────────────────────────────────
    # Web
    # ─────────────────────────────────────────────────────────

    def start_web(self) -> Dict:
        if not self.web: return {"ok": False, "error": "Web unavailable"}
        self.web.start_threaded()
        wc = self.config["web_interface"]
        return {"ok": True, "url": f"http://{wc['host']}:{wc['port']}"}

    # ─────────────────────────────────────────────────────────
    # Meta
    # ─────────────────────────────────────────────────────────

    def status(self) -> Dict:
        uptime = (datetime.now() - self.startup_time).total_seconds()
        return {
            "ok": True,
            "name": self.config["system"]["name"],
            "version": self.VERSION,
            "uptime_s": round(uptime),
            "subsystems": {
                "biometric": self.auth  is not None,
                "voice":     self.voice is not None,
                "ai":        self.ai    is not None,
                "phone":     self.phone is not None,
                "smart":     self.smart is not None,
                "web":       self.web   is not None,
            },
        }

    def update_config(self, updates: Dict) -> Dict:
        for k, v in updates.items():
            if isinstance(v, dict) and k in self.config:
                self.config[k].update(v)
            else:
                self.config[k] = v
        self._save_config()
        return {"ok": True, "message": "Config updated"}

    @property
    def ALL_TOOL_SPECS(self):
        return (BIOMETRIC_TOOLS + VOICE_SPEECH_TOOLS + AI_TOOLS +
                PHONE_TOOLS + SYSTEM_CONTROL_TOOLS + SMART_TOOLS)


# ─────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────

HELP = """
Commands: voice | hotword | speak <text> | lang <code>
          chat <msg> | persona <name>
          auth | register <id>
          status | stats | apps | open <app> | close <app>
          sms read | sms send <nr> <msg> | wa <nr> <msg> | phone info
          emotion <text> | suggest | history <q> | analytics | prefs
          autostart on|off | web | config | help | exit
(Or just type naturally — JARVIS will chat with you.)
"""


def main():
    jarvis = JARVISCore()
    import app
    app.set_core(jarvis)

    def shutdown_handler(sig, frame):
        print("\n🛑 J.A.R.V.I.S. is shutting down... Goodbye, Master!")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    print(HELP)

    while True:
        try:
            raw = input("JARVIS> ").strip()
        except EOFError:
            break   # Ctrl+D / end of input
        if not raw:
            continue

        parts = raw.split(maxsplit=2)
        cmd   = parts[0].lower()

        # Voice & speech
        if   cmd == "voice":    r = jarvis.listen(); print(r)
        elif cmd == "hotword":  print(jarvis.start_hotword())
        elif cmd == "speak" and len(parts) > 1: jarvis.speak(" ".join(parts[1:]))
        elif cmd == "lang"  and len(parts) > 1: print(jarvis.set_language(parts[1]))

        # AI
        elif cmd == "chat" and len(parts) > 1:
            r = jarvis.chat(" ".join(parts[1:]))
            print(f"JARVIS: {r.get('response', r.get('error'))}")
        elif cmd == "persona" and len(parts) > 1: print(jarvis.set_personality(parts[1]))

        # Biometric
        elif cmd == "auth":                      print(jarvis.authenticate())
        elif cmd == "register" and len(parts) > 1: print(jarvis.register_user(parts[1]))

        # System
        elif cmd == "status": print(json.dumps(jarvis.status(), indent=2, default=str))
        elif cmd == "stats":
            s = jarvis.get_stats()
            print(f"CPU {s['cpu']['usage_percent']}%  RAM {s['memory']['used_percent']}%  Disk {s['disk']['used_percent']}%")
        elif cmd == "apps":
            for a in jarvis.list_apps().get("apps", [])[:15]:
                print(f"  {a['name']:35s} {a['memory_mb']:6.1f} MB")
        elif cmd == "open"  and len(parts) > 1: print(jarvis.open_app(parts[1]))
        elif cmd == "close" and len(parts) > 1: print(jarvis.close_app(parts[1]))
        elif cmd == "web":   print(jarvis.start_web())
        elif cmd == "config": print(json.dumps(jarvis.config, indent=2))

        # Phone
        elif cmd == "sms":
            sub = parts[1].lower() if len(parts) > 1 else ""
            if sub == "read":
                for m in jarvis.read_sms().get("messages", []): print(m)
            elif sub == "send" and len(parts) > 2:
                p2 = parts[2].split(maxsplit=1)
                if len(p2) == 2: print(jarvis.send_sms(p2[0], p2[1]))
        elif cmd == "wa" and len(parts) > 2:
            p2 = parts[2].split(maxsplit=1) if len(parts) > 2 else []
            if len(p2) == 2: print(jarvis.send_whatsapp(p2[0], p2[1]))
        elif cmd == "phone" and len(parts) > 1 and parts[1] == "info":
            print(json.dumps(jarvis.get_device_info(), indent=2))

        # Smart
        elif cmd == "emotion"   and len(parts) > 1:
            r = jarvis.detect_emotion(" ".join(parts[1:]))
            print(f"{r['emotion']}  ({r['confidence']})")
        elif cmd == "suggest":
            for s in jarvis.get_suggestions().get("suggestions", []): print(f"  • {s}")
        elif cmd == "history"   and len(parts) > 1:
            for h in jarvis.search_history(" ".join(parts[1:])).get("results", [])[:10]:
                print(f"  [{h.get('timestamp','')[:16]}] {h.get('text','')}")
        elif cmd == "analytics": print(json.dumps(jarvis.get_analytics(), indent=2))
        elif cmd == "prefs":     print(json.dumps(jarvis.get_preferences(), indent=2))
        elif cmd == "autostart":
            sub = parts[1].lower() if len(parts) > 1 else ""
            if   sub == "on":  print(jarvis.enable_autostart())
            elif sub == "off": print(jarvis.disable_autostart())

        elif cmd in ("help", "?"):  print(HELP)
        elif cmd == "exit": break
        else:
            # Natural language fallback
            r = jarvis.chat(raw)
            print(f"JARVIS: {r.get('response', r.get('error', 'Unknown command'))}")


if __name__ == "__main__":
    main()
