"""
voice_speech.py - JARVIS v6 Voice & Speech Module
Speech Recognition, Text-to-Speech, Multilingual Support, Hotword Detection
100% FREE using: SpeechRecognition, pyttsx3, Google Speech API
"""

import speech_recognition as sr
import pyttsx3
import json
from pathlib import Path
from typing import Optional, Callable
import threading
import time

try:
    from pydub import AudioSegment
    import pyaudio
    AUDIO_OK = True
except:
    AUDIO_OK = False

# ─────────────────────────────────────────────────────────────
# Speech Recognition
# ─────────────────────────────────────────────────────────────

class SpeechRecognizer:
    """Real-time speech recognition using Google API (free tier)"""
    
    def __init__(self, language: str = "en-US"):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.language = language
        self.supported_languages = {
            "en-US": "English (US)",
            "en-GB": "English (UK)",
            "es-ES": "Spanish",
            "fr-FR": "French",
            "de-DE": "German",
            "it-IT": "Italian",
            "pt-BR": "Portuguese",
            "zh-CN": "Chinese",
            "ja-JP": "Japanese",
            "ko-KR": "Korean",
        }
    
    def listen(self, timeout: int = 10, phrase_time_limit: int = None):
        """Listen for speech and convert to text"""
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                print("Listening...")
                audio = self.recognizer.listen(source, timeout=timeout, 
                                              phrase_time_limit=phrase_time_limit)
            
            try:
                text = self.recognizer.recognize_google(audio, language=self.language)
                return {"ok": True, "text": text, "language": self.language}
            except sr.UnknownValueError:
                return {"ok": False, "error": "Could not understand audio"}
            except sr.RequestError as e:
                return {"ok": False, "error": f"API error: {e}"}
        
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def set_language(self, language: str):
        """Set recognition language"""
        if language in self.supported_languages:
            self.language = language
            return {"ok": True, "language": language}
        return {"ok": False, "error": f"Unsupported language: {language}"}
    
    def get_status(self):
        """Get speech recognition status"""
        return {
            "ok": True,
            "current_language": self.language,
            "supported_languages": self.supported_languages,
        }


# ─────────────────────────────────────────────────────────────
# Text-to-Speech
# ─────────────────────────────────────────────────────────────

class TextToSpeech:
    """Natural voice responses with gender/rate selection"""
    
    def __init__(self):
        self.engine = pyttsx3.init()
        self.voices = self.engine.getProperty('voices')
        self.rate = 150  # words per minute
        self.volume = 0.9  # 0.0 to 1.0
        self.language = "en-US"
        
        # Set default voice (usually index 0 = male, 1 = female if available)
        if len(self.voices) > 0:
            self.engine.setProperty('voice', self.voices[0].id)
    
    def speak(self, text: str, rate: Optional[int] = None, volume: Optional[float] = None,
              gender: str = "male"):
        """Speak text with options"""
        try:
            # Set rate
            if rate:
                self.engine.setProperty('rate', rate)
            else:
                self.engine.setProperty('rate', self.rate)
            
            # Set volume
            if volume:
                self.engine.setProperty('volume', volume)
            else:
                self.engine.setProperty('volume', self.volume)
            
            # Set gender (voice selection)
            if gender.lower() == "female" and len(self.voices) > 1:
                self.engine.setProperty('voice', self.voices[1].id)
            elif len(self.voices) > 0:
                self.engine.setProperty('voice', self.voices[0].id)
            
            self.engine.say(text)
            self.engine.runAndWait()
            
            return {"ok": True, "message": f"Spoke: {text[:50]}..."}
        
        except Exception as e:
            return {"ok": False, "error": str(e)}
    
    def set_rate(self, rate: int):
        """Set speaking rate (words per minute)"""
        self.rate = rate
        return {"ok": True, "rate": rate}
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)"""
        self.volume = max(0.0, min(1.0, volume))
        return {"ok": True, "volume": self.volume}
    
    def get_voices(self):
        """Get available voices"""
        return {
            "ok": True,
            "available_voices": len(self.voices),
            "voices": [
                {"id": v.id, "name": v.name, "gender": v.gender}
                for v in self.voices
            ]
        }
    
    def get_status(self):
        """Get TTS status"""
        return {
            "ok": True,
            "rate": self.rate,
            "volume": self.volume,
            "available_voices": len(self.voices),
            "language": self.language,
        }


# ─────────────────────────────────────────────────────────────
# Hotword Detection & Continuous Listening
# ─────────────────────────────────────────────────────────────

class HotwordDetector:
    """Wake word detection (Hey Jarvis, Hey Assistant, etc.)"""
    
    def __init__(self, hotwords: list = None):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.hotwords = hotwords or ["jarvis", "assistant", "alexa"]
        self.listening = False
        self.detection_thread = None
    
    def start_listening(self, callback: Callable = None):
        """Start continuous listening for hotword"""
        self.listening = True
        self.detection_thread = threading.Thread(
            target=self._listen_loop,
            args=(callback,),
            daemon=True
        )
        self.detection_thread.start()
        return {"ok": True, "message": "Listening for hotword..."}
    
    def _listen_loop(self, callback):
        """Continuous listening loop"""
        while self.listening:
            try:
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.1)
                    audio = self.recognizer.listen(source, timeout=1)
                
                try:
                    text = self.recognizer.recognize_google(audio).lower()
                    
                    # Check for hotwords
                    for hotword in self.hotwords:
                        if hotword in text:
                            if callback:
                                callback({"hotword": hotword, "text": text})
                            break
                
                except sr.UnknownValueValue:
                    pass
                except sr.RequestError:
                    pass
            
            except sr.RequestError:
                time.sleep(1)
            except Exception:
                pass
    
    def stop_listening(self):
        """Stop listening for hotword"""
        self.listening = False
        return {"ok": True, "message": "Hotword detection stopped"}
    
    def set_hotwords(self, hotwords: list):
        """Set new hotwords to listen for"""
        self.hotwords = hotwords
        return {"ok": True, "hotwords": hotwords}


# ─────────────────────────────────────────────────────────────
# Voice Command Processor
# ─────────────────────────────────────────────────────────────

class VoiceCommandProcessor:
    """Unified voice input/output system"""
    
    def __init__(self):
        self.recognizer = SpeechRecognizer()
        self.tts = TextToSpeech()
        self.hotword_detector = HotwordDetector()
        self.command_history = []
    
    def process_voice_command(self, timeout: int = 10):
        """Process complete voice command (listen + respond)"""
        # Listen
        result = self.recognizer.listen(timeout=timeout)
        if not result["ok"]:
            self.tts.speak(f"Error: {result['error']}")
            return result
        
        command_text = result["text"]
        self.command_history.append({
            "timestamp": time.time(),
            "command": command_text,
        })
        
        return {
            "ok": True,
            "command": command_text,
            "language": self.recognizer.language,
        }
    
    def respond(self, text: str, gender: str = "female"):
        """Respond with text-to-speech"""
        return self.tts.speak(text, gender=gender)
    
    def set_language(self, language: str):
        """Set input/output language"""
        result = self.recognizer.set_language(language)
        if result["ok"]:
            self.tts.language = language
        return result
    
    def get_command_history(self, limit: int = 10):
        """Get recent voice commands"""
        return {
            "ok": True,
            "commands": self.command_history[-limit:],
            "total": len(self.command_history),
        }


# ─────────────────────────────────────────────────────────────
# Tool Schemas for JARVIS integration
# ─────────────────────────────────────────────────────────────

VOICE_SPEECH_TOOLS = [
    {"type": "function", "function": {
        "name": "listen_voice_command",
        "description": "Listen to user voice input and convert to text",
        "parameters": {
            "type": "object",
            "properties": {
                "timeout": {"type": "integer", "description": "Listening timeout in seconds (default: 10)"},
                "language": {"type": "string", "description": "Language code (e.g., 'en-US', 'es-ES')"},
            },
        },
    }},
    {"type": "function", "function": {
        "name": "speak_response",
        "description": "Respond to user via text-to-speech",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to speak"},
                "gender": {"type": "string", "enum": ["male", "female"], "description": "Voice gender"},
                "rate": {"type": "integer", "description": "Speaking rate (words per minute)"},
            },
            "required": ["text"],
        },
    }},
    {"type": "function", "function": {
        "name": "set_voice_language",
        "description": "Set language for voice recognition and speech",
        "parameters": {
            "type": "object",
            "properties": {
                "language": {"type": "string", "description": "Language code (en-US, es-ES, fr-FR, etc.)"},
            },
            "required": ["language"],
        },
    }},
    {"type": "function", "function": {
        "name": "start_hotword_detection",
        "description": "Start listening for wake word (Hey Jarvis, etc.)",
        "parameters": {
            "type": "object",
            "properties": {
                "hotwords": {"type": "array", "items": {"type": "string"}, 
                            "description": "Wake words to listen for"},
            },
        },
    }},
    {"type": "function", "function": {
        "name": "get_voice_status",
        "description": "Get current voice system status",
        "parameters": {"type": "object", "properties": {}},
    }},
]
