# J.A.R.V.I.S. v6.1 — Complete Setup Guide

## 📦 Files in This Pack

| File | Size | Purpose |
|---|---|---|
| `jarvis_core.py` | 21KB | Main entry point — run this |
| `biometric_auth.py` | 20KB | Face recognition + fingerprint (OpenCV/dlib) |
| `voice_speech.py` | 13KB | STT + TTS + hotword + multilingual |
| `ai_integration.py` | 15KB | 7 AI providers + fallback chain |
| `phone_integration.py` | 16KB | SMS / WhatsApp / call history via ADB |
| `gmail_integration.py` | 19KB | Full Gmail API (read/send/search/label) |
| `system_control.py` | 14KB | Apps / files / scheduler / monitoring |
| `smart_features.py` | 24KB | Emotion / suggestions / analytics / autostart |
| `web_interface.py` | 77KB | 15-tab glassmorphic web UI |
| `tools_v6_patch.py` | 23KB | 33 new tools → drops into existing tools.py |
| `jarvis_config.json` | 1.4KB | All configuration (edit to add API keys) |
| `requirements.txt` | 3.8KB | All Python dependencies |
| `setup_windows.bat` | 2.2KB | One-click Windows installer |
| `setup_unix.sh` | 2.1KB | One-click Linux/macOS installer |
| `README.md` | 8.1KB | Overview & quick-start |
| `SETUP_GUIDE.md` | this | Detailed setup per feature |

---

## 🚀 Install in 5 Minutes

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
python -m venv venv
source venv/bin/activate        # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python jarvis_core.py
```

---

## 🔑 API Keys — All Free

### 1. Groq (fastest free LLM)
- Sign up: **https://console.groq.com**
- Create key → copy
- Paste into `jarvis_config.json` → `ai.groq_api_key`

### 2. Google Gemini
- Go to: **https://makersuite.google.com/app/apikey**
- Create key → copy
- Paste into `jarvis_config.json` → `ai.gemini_api_key`

### 3. Mistral AI
- Sign up: **https://console.mistral.ai**
- Create key → copy
- Paste into `jarvis_config.json` → `ai.mistral_api_key`

### 4. NVIDIA NIM
- Sign up: **https://build.nvidia.com**
- Create key → copy
- Paste into `jarvis_config.json` → `ai.nvidia_api_key`

### 5. OpenRouter (multiple keys supported)
- Sign up: **https://openrouter.ai/keys**
- Create **multiple keys** for different models/quotas
- Paste as a JSON array:
```json
"openrouter_keys": ["sk-or-key1", "sk-or-key2", "sk-or-key3"]
```
JARVIS round-robins through them automatically — if one fails, the next is tried.

### 6. FreeLLMAPI (self-hosted aggregator)
```bash
pip install freellmapi
freellmapi serve   # runs on http://localhost:8000
```
No external key needed — wraps Groq, Gemini, Cerebras, NVIDIA, Mistral automatically.

### 7. Ollama (fully local, no internet)
- Download: **https://ollama.com**
- Pull a model:
```bash
ollama pull llama3.1
ollama pull mistral
```
- JARVIS connects automatically at `http://localhost:11434`

---

## 📧 Gmail Setup

Gmail uses **OAuth2** — one-time browser login, then JARVIS stores the token locally.

### Step 1: Create Google Cloud Project
1. Go to **https://console.cloud.google.com**
2. Create a new project (e.g. "JARVIS")
3. Enable the **Gmail API**: APIs & Services → Enable APIs → search "Gmail API" → Enable

### Step 2: Create OAuth Credentials
1. APIs & Services → **Credentials**
2. Create Credentials → **OAuth 2.0 Client ID**
3. Application type: **Desktop app**
4. Download JSON → rename to **`credentials.json`**
5. Place in the **`gmail_data/`** folder next to `jarvis_core.py`

### Step 3: Connect
- In JARVIS web UI → **Settings tab** → Gmail → **Connect Gmail**
- OR in CLI: the first time you use a Gmail tool, a browser window opens for login
- Click Allow → token saved as `gmail_data/token.pickle`
- **All future calls are automatic** — no re-login needed

### Gmail Scopes Granted
- Read emails (readonly)
- Send emails
- Modify emails (mark read, add labels)
- Manage labels

### Re-authenticate
```bash
rm gmail_data/token.pickle
# Next Gmail action triggers browser login again
```

---

## 🤖 AI Provider Setup Details

### Setting Primary Provider
In `jarvis_config.json`:
```json
"ai": { "primary": "groq" }
```
Options: `groq`, `gemini`, `mistral`, `nvidia`, `openrouter`, `freellmapi`, `ollama`

### Fallback Chain
JARVIS tries providers in this order (skipping unconfigured ones):
```
Primary → Groq → Gemini → Mistral → NVIDIA → OpenRouter → FreeLLMAPI → Ollama
```

### Per-Provider Model Selection
```json
"ai": {
  "groq_model":        "mixtral-8x7b-32768",
  "gemini_model":      "gemini-1.5-flash",
  "mistral_model":     "mistral-small-latest",
  "nvidia_model":      "meta/llama-3.1-70b-instruct",
  "openrouter_model":  "openai/gpt-4o-mini",
  "freellmapi_model":  "gemini-2.0-flash",
  "ollama_model":      "llama3.1"
}
```

### Change Model at Runtime
```
JARVIS> chat set my openrouter model to anthropic/claude-3.5-sonnet
```
Or via CLI: `set_ai_model("openrouter", "anthropic/claude-3.5-sonnet")`

---

## 🔐 Biometric Setup

### Windows / Linux / macOS — Face Recognition

**Install prerequisites:**
```bash
# Windows — install Visual Studio C++ Build Tools first
# Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
# Select: "Desktop development with C++"
pip install cmake dlib face_recognition

# Linux
sudo apt-get install build-essential cmake libopencv-dev
pip install dlib face_recognition

# macOS
brew install cmake opencv
pip install dlib face_recognition
```

**Register face:**
```
JARVIS> register kim
# Webcam opens → look at camera → press SPACE to capture
```

**Authenticate:**
```
JARVIS> auth
# Face camera opens → match found → "Welcome back, kim!"
```

### Android Fingerprint (via ADB)

1. Enable **Developer Options**: Settings → About Phone → tap Build Number 7 times
2. Enable **USB Debugging**: Settings → Developer Options → USB Debugging ON
3. Connect phone via USB, accept RSA key prompt
4. Verify: `adb devices` → should show your device
5. Register: `JARVIS> register kim` → opens fingerprint enrollment on phone

---

## 🎤 Voice Setup

### PyAudio (required for microphone)
```bash
# Windows
pip install pipwin && pipwin install pyaudio

# Linux
sudo apt-get install portaudio19-dev python3-pyaudio

# macOS
brew install portaudio && pip install pyaudio
```

### Supported Languages

| Code | Language |
|---|---|
| `en-US` | English (US) — default |
| `en-GB` | English (UK) |
| `es-ES` | Spanish |
| `fr-FR` | French |
| `de-DE` | German |
| `it-IT` | Italian |
| `pt-BR` | Portuguese (Brazil) |
| `zh-CN` | Chinese (Simplified) |
| `ja-JP` | Japanese |
| `ko-KR` | Korean |

Change language: `JARVIS> lang es-ES`

### Hotword Detection
```
JARVIS> hotword
# Now say "Hey Jarvis" → JARVIS activates, listens, responds by voice
```

---

## 📱 Android Phone Setup

```bash
# 1. Install Android SDK Platform Tools
#    Windows: https://developer.android.com/tools/releases/platform-tools
#    Linux: sudo apt-get install adb
#    macOS: brew install android-platform-tools

# 2. Enable USB Debugging on phone
#    Settings → Developer Options → USB Debugging ON

# 3. Connect USB & verify
adb devices
# Should show: <serial>   device

# 4. (Optional) Set device ID in config if multiple phones
#    "phone": { "device_id": "YOUR_SERIAL_HERE" }
```

---

## 🌐 Web Interface

```
JARVIS> web
# Opens http://127.0.0.1:5000
```

All 15 tabs are accessible from the top navigation bar.
The UI updates system stats every 6 seconds via WebSocket.

**Change port** (if 5000 is taken):
```json
"web_interface": { "port": 5001 }
```

---

## 🧩 Patching Existing v5 `tools.py`

Add **4 lines** to your existing `tools.py`:

```python
# Line 1 — top of file, after existing imports
from tools_v6_patch import V6_SAFE, V6_RISKY, V6_DISPATCH, V6_TOOL_SPECS

# Line 2 — extend SAFE_ACTIONS set
SAFE_ACTIONS = {
    # ... all your existing safe tools ...
    *V6_SAFE,
}

# Line 3 — extend RISKY_ACTIONS set
RISKY_ACTIONS = {
    # ... all your existing risky tools ...
    *V6_RISKY,
}

# Line 4 — extend DISPATCH dict
DISPATCH = {
    # ... all your existing tools ...
    **V6_DISPATCH,
}

# Line 5 — extend TOOL_SPECS list (find the closing ] and add before it)
    *V6_TOOL_SPECS,
]
```

The two `assert` statements at the bottom of `tools.py` will confirm correctness.

**Result: 31 → 72 tools** (+ existing browser/calling = 79 total)

---

## ⚙️ jarvis_config.json Reference

```json
{
  "system": {
    "name": "J.A.R.V.I.S.",
    "version": "6.1"
  },
  "biometric": {
    "enabled": true,         // master toggle
    "face_recognition": true,
    "fingerprint": true
  },
  "voice": {
    "enabled": true,
    "default_language": "en-US",
    "hotword": "jarvis",     // wake word
    "tts_gender": "female",  // "male" or "female"
    "tts_rate": 150          // words per minute
  },
  "ai": {
    "enabled": true,
    "primary": "groq",       // default provider
    "personality": "jarvis", // jarvis/professional/friendly/technical/creative
    "groq_api_key": "",
    "groq_model": "mixtral-8x7b-32768",
    "gemini_api_key": "",
    "gemini_model": "gemini-1.5-flash",
    "mistral_api_key": "",
    "mistral_model": "mistral-small-latest",
    "nvidia_api_key": "",
    "nvidia_model": "meta/llama-3.1-70b-instruct",
    "openrouter_keys": [],    // list of keys — round-robin
    "openrouter_model": "openai/gpt-4o-mini",
    "freellmapi_key": "",
    "freellmapi_url": "http://localhost:8000",
    "freellmapi_model": "gemini-2.0-flash",
    "ollama_url": "http://localhost:11434",
    "ollama_model": "llama3.1"
  },
  "gmail": {
    "enabled": true,
    "credentials_path": "gmail_data/credentials.json"
  },
  "phone": {
    "enabled": true,
    "device_id": null         // null = first connected device
  },
  "web_interface": {
    "enabled": true,
    "host": "127.0.0.1",
    "port": 5000
  },
  "smart": {
    "enabled": true,
    "emotion_detection": true,
    "proactive": true
  },
  "auto_start": {
    "enabled": false,
    "services": ["web_interface", "hotword_detection"]
  }
}
```

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| `No module named face_recognition` | Install C++ build tools first, then `pip install dlib face_recognition` |
| `No module named pyaudio` | Windows: `pipwin install pyaudio` · Linux: `apt install portaudio19-dev` |
| `No Android device found` | `adb kill-server && adb start-server && adb devices` |
| `Gmail auth failed` | `rm gmail_data/token.pickle` → re-authenticate |
| `Gmail credentials not found` | Put `credentials.json` in `gmail_data/` folder |
| `All AI providers failed` | Check API keys in config; try `JARVIS> chat` to see error details |
| `Port already in use` | Change `port` in config to `5001` |
| `Face not recognized` | Re-register in good lighting; one face only in frame |
| `Hotword not triggering` | Speak clearly; check mic permissions; try with `mic_btn` first |
| `OpenRouter key exhausted` | Add more keys to `openrouter_keys` array |

### Quick Diagnostic
```bash
python -c "
import flask, psutil, requests
print('Core: OK')
try: import cv2, face_recognition; print('Biometric: OK')
except: print('Biometric: MISSING — install C++ tools + dlib')
try: import speech_recognition, pyttsx3; print('Voice: OK')
except: print('Voice: MISSING — install pyaudio')
try: import googleapiclient; print('Gmail: OK')
except: print('Gmail: pip install google-api-python-client')
"
```

---

## 📞 Support

1. Run the diagnostic above
2. Check this guide for the specific feature
3. For ADB: `adb logcat` shows device-side errors
4. For Gmail: check `gmail_data/` for `credentials.json` and `token.pickle`
5. For AI: `JARVIS> chat get ai provider status` shows all 7 providers

---

*J.A.R.V.I.S. v6.1 — 100% free, 100% local, fully open-source.*
