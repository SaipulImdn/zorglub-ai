from abc import ABC, abstractmethod

class TextToSpeechInterface(ABC):
    @abstractmethod
    def speak(self, text: str):
        pass
    
    @abstractmethod
    def generate_audio_file(self, text: str):
        pass

class TextToSpeech(TextToSpeechInterface):
    def speak(self, text: str):
        from infrastructure.tts_gtts import speak_text
        speak_text(text)
    
    def generate_audio_file(self, text: str):
        from infrastructure.tts_gtts import generate_audio_file
        return generate_audio_file(text)
