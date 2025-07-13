"""
Dependency Injection Container
Manages all dependencies dan service initialization
"""

import subprocess
import requests
import sounddevice as sd
from core.interfaces.ai_service import AIService
from core.interfaces.speech_input import SpeechToText
from core.interfaces.speech_output import TextToSpeech
from core.use_cases.voice_assistant import VoiceAssistant

class DependencyContainer:
    def __init__(self):
        self._ai_service = None
        self._speech_input = None
        self._speech_output = None
        self._voice_assistant = None

    def get_ai_service(self) -> AIService:
        """Get AI Service instance (singleton)"""
        if self._ai_service is None:
            self._ai_service = AIService()
        return self._ai_service

    def get_speech_input(self) -> SpeechToText:
        """Get Speech Input service (singleton)"""
        if self._speech_input is None:
            self._speech_input = SpeechToText()
        return self._speech_input

    def get_speech_output(self) -> TextToSpeech:
        """Get Speech Output service (singleton)"""
        if self._speech_output is None:
            self._speech_output = TextToSpeech()
        return self._speech_output

    def get_voice_assistant(self) -> VoiceAssistant:
        """Get Voice Assistant use case (singleton)"""
        if self._voice_assistant is None:
            self._voice_assistant = VoiceAssistant(
                ai_service=self.get_ai_service(),
                speech_input=self.get_speech_input(),
                speech_output=self.get_speech_output()
            )
        return self._voice_assistant

    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available"""
        errors = []
        
        # Check Ollama
        try:
            response = requests.get("http://localhost:11434/api/version", timeout=5)
            if response.status_code == 200:
                print("Ollama server is running")
            else:
                errors.append("Ollama server not responding properly")
        except Exception:
            errors.append("Ollama server not running (start with: ollama serve)")
        
        # Check mpv
        try:
            subprocess.run(['mpv', '--version'], capture_output=True, check=True)
            print("mpv found")
        except Exception:
            errors.append("mpv not found (install with: sudo apt install mpv)")
        
        # Check audio devices
        try:
            devices = sd.query_devices()
            if len(devices) > 0:
                print("Audio devices found")
            else:
                errors.append("No audio devices found")
        except Exception:
            errors.append("Audio system error")
        
        if errors:
            print("\n Issues found:")
            for error in errors:
                print(f"  - {error}")
            print("\n Fix these issues before using voice features")
            return False
        
        print("\n All dependencies are ready!")
        return True
