# 🤖 J.A.R.V.I.S. v6.1 — Complete AI Personal Assistant

> *Just A Really Virtuous Intelligent System*  
> 100% free · 100% local · fully open-source

---

## ✨ What's Inside

| Feature | Tools | Notes |
|---|---|---|
| 🔐 **Biometric** — face + fingerprint | 3 | OpenCV/dlib + ADB |
| 🎤 **Voice & Speech** — STT/TTS/hotword/multilingual | 5 | SpeechRecognition + pyttsx3 |
| 🤖 **7-Provider AI** — full fallback chain | 6 | All free tiers |
| 📱 **Phone** — SMS/WhatsApp/calls via ADB | 5 | Android USB Debugging |
| 📧 **Gmail** — read/send/search/label | 7 | Google OAuth2 (free) |
| 🧠 **Smart** — emotion/suggestions/analytics/autostart | 7 | Fully local |
| 🌐 **Web UI** — 15 tabs, glassmorphic, real-time | — | Flask + Socket.IO |
| 🌐 **Browser** — Selenium automation (v5) | 10 | |
| 📞 **Calling** — Teams/Zoom/Discord (v5) | 5 | |
| 🖥️ **System Control** — 31 original tools | 31 | |
| **Total** | **79 tools** | |

---

## 🚀 Quick Start

### Windows
```bat
setup_windows.bat
```

### Linux / macOS
```bash
bash setup_unix.sh
```

### Manual
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python jarvis_core.py
```

Then open **http://127.0.0.1:5000** for the web UI.

---

## 🔑 Free API Keys

| Provider | Get Key | Free Tier |
|---|---|---|
| **Groq** | console.groq.com | 30 req/min, fast |
| **Google Gemini** | makersuite.google.com/app/apikey | 60 req/min |
| **Mistral** | console.mistral.ai | Free tier |
| **NVIDIA NIM** | build.nvidia.com | Free tier |
| **OpenRouter** | openrouter.ai/keys | Multiple keys supported |
| **FreeLLMAPI** | (self-hosted) | pip install freellmapi |
| **Ollama** | ollama.com | Fully local, no key |

Paste keys into `jarvis_config.json` → `ai` section.  
**OpenRouter**: add multiple keys as a list — JARVIS round-robins through them automatically.

---

## 📧 Gmail Setup (OAuth2)

1. Go to **https://console.cloud.google.com**
2. Create a project → Enable **Gmail API**
3. Create **OAuth 2.0 Client ID** (Desktop App)
4. Download JSON → save as **`gmail_data/credentials.json`**
5. In JARVIS Settings → Gmail → **Connect Gmail** (opens browser for one-time auth)
6. Done — token saved, no re-auth needed

---

## 🤖 7-Provider AI Fallback Chain

```
User asks something
        ↓
   Groq (primary)   ← fastest
        ↓ (if fails)
   Google Gemini
        ↓ (if fails)
   Mistral AI
        ↓ (if fails)
   NVIDIA NIM
        ↓ (if fails)
   OpenRouter        ← rotates through multiple keys
        ↓ (if fails)
   FreeLLMAPI
        ↓ (if fails)
   Ollama (local)    ← always available if installed
```

Every provider is both a primary and a fallback. Set `primary` in config or
say *"Use Gemini for this"* in chat.

**Multiple OpenRouter keys:**
```json
"openrouter_keys": ["sk-or-key1", "sk-or-key2", "sk-or-key3"]
```

---

## 🖥️ Web UI — 15 Tabs

| Tab | What it does |
|---|---|
| 💬 **Chat** | Talk to JARVIS, attach files, voice input, emotion badges |
| ✅ **Tasks** | To-do list — click Run to send to Chat |
| 📁 **Files** | Upload manager |
| 🧠 **Memory** | Index folders → searchable Knowledge Vaults (RAG) |
| ⚡ **Macros** | Save & replay multi-step action sequences |
| 🔔 **Alerts** | Risky actions pause here for approval |
| 🗂 **History** | Every chat auto-saved, click to reopen |
| 🌀 **Core** | Full-width "now talking" animated view |
| 🎤 **Voice** | Language, TTS gender, hotword settings |
| 📱 **Phone** | Send SMS/WhatsApp, read inbox, device info |
| 📧 **Gmail** | Read, search, compose, reply, trash emails |
| 🖥 **System** | Live CPU/RAM/Disk stats, open/close apps |
| 🧠 **Smart** | Emotion detector, suggestions, history search, analytics |
| 🔐 **Auth** | Register & authenticate via face/fingerprint |
| ⚙ **Settings** | All 7 AI providers, Gmail, feature toggles |

---

## 💬 CLI Commands

```
voice              Listen → transcribe → AI → speak
hotword            Start "Hey Jarvis" always-on detection
speak <text>       Speak text aloud
lang <code>        Set language (es-ES, fr-FR, zh-CN…)
chat <msg>         Chat with AI (uses full fallback chain)
persona <name>     Set personality (jarvis/professional/friendly/technical/creative)
auth               Authenticate (face or fingerprint)
register <id>      Register biometric for user
status             Full system status
stats              CPU / RAM / Disk snapshot
apps               List running apps
open <app>         Open application
close <app>        Close application
sms read           Read SMS from phone
sms send <nr> <m>  Send SMS
wa <nr> <msg>      Send WhatsApp message
phone info         Android device info
emotion <text>     Detect emotion in text
suggest            Get proactive suggestions
history <query>    Search command history
analytics          Usage statistics
prefs              Learned user preferences
autostart on|off   Toggle boot auto-start
web                Start web UI (http://127.0.0.1:5000)
config             Show current configuration
help               Show all commands
exit               Exit JARVIS
(anything else)    Sent directly to AI
```

---

## 📦 File List

```
jarvis_v6.1/
├── jarvis_core.py        ← Entry point
├── biometric_auth.py     ← Face + fingerprint
├── voice_speech.py       ← STT + TTS + hotword
├── ai_integration.py     ← 7 providers + fallback
├── phone_integration.py  ← SMS / WhatsApp / ADB
├── gmail_integration.py  ← Full Gmail API
├── system_control.py     ← Apps / files / scheduler
├── smart_features.py     ← Emotion / suggestions / analytics
├── web_interface.py      ← 15-tab glassmorphic UI
├── tools_v6_patch.py     ← Merge 33 tools into tools.py
├── jarvis_config.json    ← All configuration
├── requirements.txt      ← All pip deps
├── setup_windows.bat     ← Windows one-click setup
├── setup_unix.sh         ← Linux/macOS one-click setup
├── gmail_data/           ← Put credentials.json here
└── README.md             ← This file
```

---

## 🔧 Patching Existing v5 tools.py

Four lines in `tools.py`:

```python
from tools_v6_patch import V6_SAFE, V6_RISKY, V6_DISPATCH, V6_TOOL_SPECS

SAFE_ACTIONS  = { ...existing... , *V6_SAFE   }
RISKY_ACTIONS = { ...existing... , *V6_RISKY  }
DISPATCH      = { ...existing... , **V6_DISPATCH }
TOOL_SPECS   += V6_TOOL_SPECS
```

Result: **31 → 72 tools** with no other changes.

---

## 🛡️ Safety Model

| Tier | Tools | Behaviour |
|---|---|---|
| **SAFE** | 46 tools | Execute instantly, no approval |
| **RISKY** | 26 tools | Pause → Alerts tab → user approves |

Risky actions: send SMS/email, make calls, biometric register/auth,
speak aloud, hotword activation, autostart, Gmail send/reply/trash.

---

## 🐛 Common Fixes

```bash
# face_recognition won't install (Windows)
# Install Visual Studio C++ Build Tools first, then:
pip install cmake && pip install dlib && pip install face_recognition

# PyAudio (Windows)
pip install pipwin && pipwin install pyaudio

# No Android device
adb kill-server && adb start-server && adb devices

# Gmail auth error
rm gmail_data/token.pickle   # forces re-authentication

# Wrong port
# Edit jarvis_config.json → web_interface → port → 5001

# Verify install
python -c "import flask, psutil, requests, googleapiclient; print('OK')"
```

---

## 📊 Tool Count

| Category | Safe | Risky | Total |
|---|---|---|---|
| System Control (v5 original) | 22 | 9 | 31 |
| Browser automation (v5) | 7 | 3 | 10 |
| Calling — Teams/Zoom/Discord (v5) | 2 | 3 | 5 |
| Biometric — face + fingerprint (v6) | 1 | 2 | 3 |
| Voice — STT/TTS/hotword (v6) | 3 | 2 | 5 |
| AI — 7 providers + management (v6) | 4 | 2 | 6 |
| Phone — SMS/WhatsApp/ADB (v6) | 3 | 2 | 5 |
| Gmail — read/send/search (v6) | 4 | 3 | 7 |
| Smart — emotion/analytics/autostart (v6) | 5 | 2 | 7 |
| **Grand Total** | **51** | **28** | **79** |

---

## 📜 License

MIT — free to use, modify, and distribute.  
All dependencies are open-source (MIT, BSD, Apache 2.0).

---

*J.A.R.V.I.S. v6.1 — Your AI assistant. Your machine. Your rules.*
