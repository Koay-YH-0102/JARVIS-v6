"""
smart_features.py - JARVIS v6 Smart Features
Emotion detection, proactive suggestions, adaptive learning, command analytics
100% FREE using open-source libraries
"""

import json
import re
import time
import math
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import Counter, defaultdict

try:
    import numpy as np
    NUMPY_OK = True
except ImportError:
    NUMPY_OK = False

SMART_DIR = Path(__file__).parent / "smart_data"
SMART_DIR.mkdir(exist_ok=True)

LEARNING_FILE   = SMART_DIR / "learning_data.json"
ANALYTICS_FILE  = SMART_DIR / "analytics.json"
EMOTIONS_FILE   = SMART_DIR / "emotion_log.json"


# ─────────────────────────────────────────────────────────────
# Emotion Detection (voice tone / text sentiment)
# ─────────────────────────────────────────────────────────────

class EmotionDetector:
    """
    Analyse user emotion from:
      1. Text sentiment (keyword-based, no external model needed)
      2. Voice prosody via pyaudio amplitude variance (optional)
    """

    EMOTION_KEYWORDS = {
        "happy":   ["great", "awesome", "love", "excellent", "fantastic", "wonderful",
                    "happy", "excited", "perfect", "brilliant", "amazing", "joy"],
        "sad":     ["sad", "depressed", "unhappy", "terrible", "horrible", "awful",
                    "cry", "grief", "miss", "alone", "hopeless", "down"],
        "angry":   ["angry", "furious", "hate", "rage", "mad", "frustrated",
                    "annoyed", "irritated", "disgusted", "outraged"],
        "anxious": ["worried", "anxious", "nervous", "scared", "afraid", "stress",
                    "panic", "fear", "uncertain", "overwhelmed"],
        "neutral": [],
    }

    def __init__(self):
        self.emotion_log: List[Dict] = self._load_log()

    def _load_log(self):
        if EMOTIONS_FILE.exists():
            with open(EMOTIONS_FILE) as f:
                return json.load(f)
        return []

    def _save_log(self):
        with open(EMOTIONS_FILE, "w") as f:
            json.dump(self.emotion_log[-500:], f, indent=2)

    def detect_from_text(self, text: str) -> Dict:
        """Return detected emotion + confidence from plain text."""
        text_lower = text.lower()
        words = re.findall(r"[a-z']+", text_lower)

        scores: Dict[str, float] = {e: 0.0 for e in self.EMOTION_KEYWORDS}
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            for kw in keywords:
                if kw in words:
                    scores[emotion] += 1.0
                elif kw in text_lower:          # partial match
                    scores[emotion] += 0.5

        # Exclamation marks → amplify happiness / anger
        excl_count = text.count("!")
        scores["happy"]  += excl_count * 0.3
        scores["angry"]  += excl_count * 0.2

        # Question marks → amplify anxious
        q_count = text.count("?")
        scores["anxious"] += q_count * 0.2

        total = sum(scores.values())
        if total == 0:
            top_emotion, confidence = "neutral", 1.0
        else:
            top_emotion = max(scores, key=scores.get)
            confidence  = round(scores[top_emotion] / total, 2)

        entry = {
            "timestamp": datetime.now().isoformat(),
            "text_snippet": text[:80],
            "emotion": top_emotion,
            "confidence": confidence,
            "scores": {k: round(v, 2) for k, v in scores.items()},
        }
        self.emotion_log.append(entry)
        self._save_log()

        return {
            "ok": True,
            "emotion": top_emotion,
            "confidence": confidence,
            "scores": entry["scores"],
        }

    def detect_from_audio_energy(self, energy_values: List[float]) -> Dict:
        """
        Rough emotion from microphone energy variance.
        high variance + high mean → excited/angry
        low variance + low mean  → sad/calm
        """
        if not energy_values:
            return {"ok": False, "error": "No audio data"}

        mean_e  = sum(energy_values) / len(energy_values)
        variance = sum((e - mean_e) ** 2 for e in energy_values) / len(energy_values)
        std_e   = math.sqrt(variance)

        if mean_e > 0.7 and std_e > 0.3:
            emotion, confidence = "excited", 0.7
        elif mean_e > 0.6:
            emotion, confidence = "happy",   0.6
        elif mean_e < 0.2 and std_e < 0.1:
            emotion, confidence = "sad",     0.6
        elif std_e > 0.4:
            emotion, confidence = "anxious", 0.55
        else:
            emotion, confidence = "neutral", 0.5

        return {"ok": True, "emotion": emotion, "confidence": confidence,
                "mean_energy": round(mean_e, 3), "std_energy": round(std_e, 3)}

    def recent_emotions(self, n: int = 10) -> Dict:
        """Return the last N detected emotions."""
        return {"ok": True, "emotions": self.emotion_log[-n:], "total_logged": len(self.emotion_log)}


# ─────────────────────────────────────────────────────────────
# Command Analytics
# ─────────────────────────────────────────────────────────────

class CommandAnalytics:
    """Track, search, and analyse past commands."""

    def __init__(self):
        self.data: Dict = self._load()

    def _load(self) -> Dict:
        if ANALYTICS_FILE.exists():
            with open(ANALYTICS_FILE) as f:
                return json.load(f)
        return {"commands": [], "category_counts": {}, "hourly_counts": {}}

    def _save(self):
        # Trim commands list to last 5000
        self.data["commands"] = self.data["commands"][-5000:]
        with open(ANALYTICS_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    def _classify(self, text: str) -> str:
        """Simple rule-based classification."""
        t = text.lower()
        if any(w in t for w in ["open", "close", "launch", "start", "stop"]):
            return "app_control"
        if any(w in t for w in ["file", "folder", "copy", "move", "delete", "read"]):
            return "file_ops"
        if any(w in t for w in ["sms", "whatsapp", "call", "message", "text"]):
            return "phone"
        if any(w in t for w in ["volume", "brightness", "mute", "screenshot", "lock"]):
            return "system"
        if any(w in t for w in ["search", "find", "google", "navigate", "go to", "browse"]):
            return "browser"
        if any(w in t for w in ["schedule", "remind", "alarm", "task", "todo"]):
            return "automation"
        return "general"

    def record(self, text: str, result_ok: bool, source: str = "chat"):
        """Record a command."""
        hour = datetime.now().strftime("%H")
        category = self._classify(text)

        self.data["commands"].append({
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "category": category,
            "result_ok": result_ok,
            "source": source,
        })

        self.data["category_counts"][category] = self.data["category_counts"].get(category, 0) + 1
        self.data["hourly_counts"][hour]       = self.data["hourly_counts"].get(hour, 0) + 1
        self._save()

    def search(self, query: str, limit: int = 20) -> Dict:
        """Full-text search over command history."""
        q = query.lower()
        hits = [c for c in reversed(self.data["commands"]) if q in c["text"].lower()]
        return {"ok": True, "results": hits[:limit], "total": len(hits)}

    def summary(self) -> Dict:
        """Return analytics summary."""
        commands = self.data["commands"]
        total = len(commands)
        if total == 0:
            return {"ok": True, "total": 0}

        success_rate = sum(1 for c in commands if c.get("result_ok")) / total
        top_category = max(self.data["category_counts"], key=self.data["category_counts"].get) \
            if self.data["category_counts"] else "none"
        busiest_hour = max(self.data["hourly_counts"], key=self.data["hourly_counts"].get) \
            if self.data["hourly_counts"] else "00"

        return {
            "ok": True,
            "total_commands": total,
            "success_rate": round(success_rate, 2),
            "top_category": top_category,
            "category_breakdown": self.data["category_counts"],
            "busiest_hour": f"{busiest_hour}:00",
            "hourly_distribution": self.data["hourly_counts"],
        }


# ─────────────────────────────────────────────────────────────
# Learning System (Adaptive Behaviour)
# ─────────────────────────────────────────────────────────────

class LearningSystem:
    """
    Learn from usage patterns and adapt JARVIS behaviour:
    - Prefer faster AI provider at peak hours
    - Suggest frequently used apps
    - Learn preferred TTS voice/language
    """

    def __init__(self):
        self.data: Dict = self._load()

    def _load(self) -> Dict:
        if LEARNING_FILE.exists():
            with open(LEARNING_FILE) as f:
                return json.load(f)
        return {
            "app_opens": {},
            "preferred_language": "en-US",
            "preferred_voice": "female",
            "preferred_ai": "groq",
            "session_count": 0,
            "total_commands": 0,
            "last_seen": None,
            "custom_patterns": [],
        }

    def _save(self):
        with open(LEARNING_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    # ── event listeners ──────────────────────────────────────

    def on_app_open(self, app_name: str):
        counts = self.data.setdefault("app_opens", {})
        counts[app_name] = counts.get(app_name, 0) + 1
        self._save()

    def on_language_used(self, lang: str):
        self.data["preferred_language"] = lang
        self._save()

    def on_voice_used(self, gender: str):
        self.data["preferred_voice"] = gender
        self._save()

    def on_ai_used(self, provider: str, success: bool):
        if success:
            self.data["preferred_ai"] = provider
        self._save()

    def on_session_start(self):
        self.data["session_count"] = self.data.get("session_count", 0) + 1
        self.data["last_seen"] = datetime.now().isoformat()
        self._save()

    def on_command(self):
        self.data["total_commands"] = self.data.get("total_commands", 0) + 1
        self._save()

    # ── recommendations ──────────────────────────────────────

    def top_apps(self, n: int = 5) -> List[str]:
        apps = self.data.get("app_opens", {})
        return sorted(apps, key=apps.get, reverse=True)[:n]

    def get_preferences(self) -> Dict:
        return {
            "ok": True,
            "preferred_language": self.data.get("preferred_language", "en-US"),
            "preferred_voice":    self.data.get("preferred_voice",    "female"),
            "preferred_ai":       self.data.get("preferred_ai",       "groq"),
            "top_apps":           self.top_apps(),
            "session_count":      self.data.get("session_count", 0),
            "total_commands":     self.data.get("total_commands", 0),
            "last_seen":          self.data.get("last_seen"),
        }


# ─────────────────────────────────────────────────────────────
# Proactive Suggestions Engine
# ─────────────────────────────────────────────────────────────

class ProactiveSuggestions:
    """
    Generate contextual suggestions based on:
    - Time of day
    - Detected emotion
    - Recent commands
    - Learned usage patterns
    """

    MORNING_APPS   = ["spotify", "chrome", "outlook"]
    WORK_APPS      = ["vscode", "word", "excel", "teams", "slack"]
    EVENING_APPS   = ["netflix", "youtube", "spotify"]

    def __init__(self, analytics: CommandAnalytics, learner: LearningSystem):
        self.analytics = analytics
        self.learner   = learner

    def _time_context(self) -> str:
        h = datetime.now().hour
        if 5  <= h < 12:  return "morning"
        if 12 <= h < 18:  return "afternoon"
        if 18 <= h < 22:  return "evening"
        return "night"

    def get_suggestions(self, current_emotion: str = "neutral",
                        recent_commands: List[str] = None) -> Dict:
        """Return list of proactive suggestions."""
        suggestions = []
        ctx = self._time_context()
        prefs = self.learner.get_preferences()

        # Time-based
        if ctx == "morning":
            suggestions.append("Good morning! Would you like me to check your emails or play some music?")
            for app in self.MORNING_APPS[:2]:
                if app in prefs.get("top_apps", []):
                    suggestions.append(f"Open {app}? You usually use it in the morning.")
        elif ctx == "afternoon":
            suggestions.append("Good afternoon! Need help with any tasks?")
        elif ctx == "evening":
            suggestions.append("Good evening! Time to wind down?")
            for app in self.EVENING_APPS[:2]:
                if app in prefs.get("top_apps", []):
                    suggestions.append(f"Open {app} for some entertainment?")

        # Emotion-based
        if current_emotion == "sad":
            suggestions.append("You seem a bit down. Would you like me to play some uplifting music?")
        elif current_emotion == "anxious":
            suggestions.append("Taking a short break might help. Want me to set a 5-minute timer?")
        elif current_emotion == "happy":
            suggestions.append("Great energy! Anything exciting you're working on?")

        # Pattern-based (most used apps not opened today)
        top = prefs.get("top_apps", [])
        analytics_summary = self.analytics.summary()
        if top:
            suggestions.append(f"Your most-used apps: {', '.join(top[:3])}. Open one?")

        # Success rate tip
        sr = analytics_summary.get("success_rate", 1.0)
        if sr < 0.8:
            suggestions.append("I've had some errors recently. Would you like me to run a self-check?")

        return {
            "ok": True,
            "context": ctx,
            "emotion": current_emotion,
            "suggestions": suggestions[:5],
        }


# ─────────────────────────────────────────────────────────────
# Auto-start Registry (Windows Task Scheduler or Linux cron)
# ─────────────────────────────────────────────────────────────

class AutoStartManager:
    """Register JARVIS to start automatically at system boot."""

    def __init__(self):
        import platform
        self.platform = platform.system()

    def enable(self, script_path: str) -> Dict:
        """Enable auto-start"""
        script_path = Path(script_path).resolve()

        if self.platform == "Windows":
            return self._windows_enable(script_path)
        elif self.platform == "Linux":
            return self._linux_enable(script_path)
        elif self.platform == "Darwin":
            return self._macos_enable(script_path)
        return {"ok": False, "error": f"Unsupported platform: {self.platform}"}

    def _windows_enable(self, script_path: Path) -> Dict:
        import subprocess
        task_name = "JARVISv6"
        cmd = (
            f'schtasks /create /tn "{task_name}" '
            f'/tr "python {script_path}" '
            f'/sc onlogon /rl highest /f'
        )
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if r.returncode == 0:
            return {"ok": True, "message": f"Auto-start enabled (Task: {task_name})"}
        return {"ok": False, "error": r.stderr.strip()}

    def _linux_enable(self, script_path: Path) -> Dict:
        cron_line = f"@reboot python3 {script_path} &\n"
        cron_path = Path.home() / ".jarvis_cron"
        try:
            import subprocess
            r = subprocess.run("crontab -l", shell=True, capture_output=True, text=True)
            existing = r.stdout if r.returncode == 0 else ""
            if cron_line not in existing:
                new_cron = existing + cron_line
                cron_path.write_text(new_cron)
                subprocess.run(f"crontab {cron_path}", shell=True)
            return {"ok": True, "message": "Auto-start enabled via cron"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def _macos_enable(self, script_path: Path) -> Dict:
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>com.jarvis.v6</string>
    <key>ProgramArguments</key>
    <array><string>python3</string><string>{script_path}</string></array>
    <key>RunAtLoad</key><true/>
</dict>
</plist>"""
        plist_path = Path.home() / "Library/LaunchAgents/com.jarvis.v6.plist"
        try:
            plist_path.write_text(plist)
            import subprocess
            subprocess.run(f"launchctl load {plist_path}", shell=True)
            return {"ok": True, "message": "Auto-start enabled via launchd"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def disable(self) -> Dict:
        """Disable auto-start"""
        if self.platform == "Windows":
            import subprocess
            r = subprocess.run('schtasks /delete /tn "JARVISv6" /f',
                               shell=True, capture_output=True, text=True)
            if r.returncode == 0:
                return {"ok": True, "message": "Auto-start disabled"}
            return {"ok": False, "error": r.stderr.strip()}
        return {"ok": False, "error": "Manual removal needed on this platform"}


# ─────────────────────────────────────────────────────────────
# Unified Smart Features Manager
# ─────────────────────────────────────────────────────────────

class SmartFeaturesManager:
    """Single entry point for all smart features."""

    def __init__(self):
        self.emotions   = EmotionDetector()
        self.analytics  = CommandAnalytics()
        self.learner    = LearningSystem()
        self.suggestions = ProactiveSuggestions(self.analytics, self.learner)
        self.autostart  = AutoStartManager()
        self.learner.on_session_start()

    # Convenience wrappers

    def analyse_emotion(self, text: str) -> Dict:
        return self.emotions.detect_from_text(text)

    def record_command(self, text: str, result_ok: bool, source: str = "chat") -> None:
        self.analytics.record(text, result_ok, source)
        self.learner.on_command()

    def get_suggestions(self, text: str = "") -> Dict:
        emotion = "neutral"
        if text:
            e = self.emotions.detect_from_text(text)
            emotion = e.get("emotion", "neutral")
        return self.suggestions.get_suggestions(current_emotion=emotion)

    def get_analytics_summary(self) -> Dict:
        return self.analytics.summary()

    def get_preferences(self) -> Dict:
        return self.learner.get_preferences()

    def search_history(self, query: str, limit: int = 20) -> Dict:
        return self.analytics.search(query, limit)

    def enable_autostart(self, script_path: str) -> Dict:
        return self.autostart.enable(script_path)

    def disable_autostart(self) -> Dict:
        return self.autostart.disable()


# ─────────────────────────────────────────────────────────────
# Tool Schemas
# ─────────────────────────────────────────────────────────────

SMART_TOOLS = [
    {"type": "function", "function": {
        "name": "detect_emotion",
        "description": "Detect user emotion from text or recent voice input",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to analyse"},
            },
            "required": ["text"],
        },
    }},
    {"type": "function", "function": {
        "name": "get_proactive_suggestions",
        "description": "Get AI-powered proactive suggestions based on time, emotion and usage patterns",
        "parameters": {
            "type": "object",
            "properties": {
                "context_text": {"type": "string", "description": "Optional context or current input"},
            },
        },
    }},
    {"type": "function", "function": {
        "name": "get_analytics_summary",
        "description": "Get command history analytics — usage, success rate, top categories",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "search_command_history",
        "description": "Search through past commands and interactions",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results to return"},
            },
            "required": ["query"],
        },
    }},
    {"type": "function", "function": {
        "name": "get_user_preferences",
        "description": "Get learned user preferences (language, voice, AI provider, top apps)",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "enable_autostart",
        "description": "Enable JARVIS to start automatically at system boot",
        "parameters": {
            "type": "object",
            "properties": {
                "script_path": {"type": "string", "description": "Full path to jarvis_core.py"},
            },
            "required": ["script_path"],
        },
    }},
    {"type": "function", "function": {
        "name": "disable_autostart",
        "description": "Disable JARVIS auto-start at boot",
        "parameters": {"type": "object", "properties": {}},
    }},
]
