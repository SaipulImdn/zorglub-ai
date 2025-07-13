from abc import ABC, abstractmethod

class SpeechToTextInterface(ABC):
    @abstractmethod
    def listen(self) -> str:
        pass
    
    @abstractmethod
    def transcribe_file(self, file_path: str) -> str:
        pass

class SpeechToText(SpeechToTextInterface):
    def listen(self) -> str:
        from infrastructure.stt_whisper import transcribe_audio
        return transcribe_audio()
    
    def transcribe_file(self, file_path: str) -> str:
        from infrastructure.stt_whisper import transcribe_audio_file
        return transcribe_audio_file(file_path)
