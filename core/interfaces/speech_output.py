from abc import ABC, abstractmethod

class SpeechOutputInterface(ABC):
    @abstractmethod
    def speak(self, text: str) -> None:
        pass

class SpeechOutput(SpeechOutputInterface):
    def speak(self, text: str) -> None:
        from infrastructure.tts_human import speak_text
        speak_text(text)

# Alias untuk backward compatibility
TextToSpeech = SpeechOutput
