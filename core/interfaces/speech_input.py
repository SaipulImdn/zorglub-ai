from abc import ABC, abstractmethod

class SpeechInputInterface(ABC):
    @abstractmethod
    def listen(self) -> str:
        pass

class SpeechInput(SpeechInputInterface):
    def listen(self) -> str:
        from infrastructure.stt_whisper import transcribe_audio
        return transcribe_audio()

# Alias untuk backward compatibility
SpeechToText = SpeechInput
