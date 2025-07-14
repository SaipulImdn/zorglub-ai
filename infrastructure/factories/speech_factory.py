import whisper
import threading
import time
import os
import tempfile
from typing import Dict, Any, Optional, Union
from pathlib import Path

from shared.config import Config
from .base_factory import ServiceFactory, SingletonMixin, resource_manager

class ModelCache:
    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._model_loading = set()
    
    def get_model(self, model_name: str):
        with self._lock:
            if model_name in self._models:
                return self._models[model_name]
            
            # Prevent multiple threads loading same model
            if model_name in self._model_loading:
                # Wait for other thread to finish loading
                while model_name in self._model_loading:
                    time.sleep(0.1)
                return self._models.get(model_name)
            
            # Mark as loading
            self._model_loading.add(model_name)
        
        try:
            print(f"Loading Whisper model: {model_name}...")
            model = whisper.load_model(model_name)
            
            with self._lock:
                self._models[model_name] = model
                self._model_loading.discard(model_name)
            
            # Register for cleanup
            resource_manager.register_resource(model)
            
            return model
            
        except Exception as e:
            with self._lock:
                self._model_loading.discard(model_name)
            raise e
    
    def clear_cache(self):
        with self._lock:
            self._models.clear()

class AudioProcessor:
    def __init__(self):
        self.config = Config.get_recording_settings()
        self._temp_files = []
        self._lock = threading.Lock()
    
    def record_audio(self, duration: Optional[int] = None) -> Optional[str]:
        import sounddevice as sd
        import numpy as np
        import scipy.io.wavfile as wav
        
        duration = duration or self.config['duration']
        fs = self.config['sample_rate']
        
        print(f"Recording audio for {duration} seconds...")
        
        try:
            # Record with optimized buffer size
            audio = sd.rec(
                int(duration * fs), 
                samplerate=fs, 
                channels=1,
                blocking=True,
                device=None  # Use default device
            )
            
            # Create temporary file
            temp_file = self._create_temp_file()
            
            # Save with proper format
            wav.write(temp_file, fs, (audio * 32767).astype(np.int16))
            
            print("Recording completed")
            return temp_file
            
        except Exception as e:
            print(f"Error recording: {e}")
            return None
    
    def _create_temp_file(self) -> str:
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix='.wav',
            dir=tempfile.gettempdir()
        )
        
        temp_path = temp_file.name
        temp_file.close()
        
        with self._lock:
            self._temp_files.append(temp_path)
        
        return temp_path
    
    def cleanup_temp_files(self):
        with self._lock:
            for temp_file in self._temp_files[:]:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                    self._temp_files.remove(temp_file)
                except Exception as e:
                    print(f"Error cleaning up {temp_file}: {e}")

class WhisperSTT:
    def __init__(self):
        self.config = Config.get_speech_settings()
        self.model_cache = ModelCache()
        self.audio_processor = AudioProcessor()
        
        # Register cleanup
        resource_manager.register_resource(
            self.audio_processor, 
            self.audio_processor.cleanup_temp_files
        )
    
    def transcribe_audio(self, audio_file: Optional[str] = None) -> Optional[str]:
        try:
            # Use provided file atau record new
            if audio_file is None:
                audio_file = self.audio_processor.record_audio()
                if audio_file is None:
                    return None
            
            # Get cached model
            model = self.model_cache.get_model(self.config['whisper_model'])
            
            print("Transcribing audio...")
            
            # Transcribe dengan optimized options
            result = model.transcribe(
                audio_file,
                language=self.config['stt_language'],
                fp16=False,  # Better compatibility
                verbose=False
            )
            
            # Cleanup if we created the file
            if audio_file and audio_file in self.audio_processor._temp_files:
                try:
                    os.remove(audio_file)
                    self.audio_processor._temp_files.remove(audio_file)
                except Exception:
                    pass
            
            return result["text"].strip()
            
        except Exception as e:
            print(f"Error transcribing: {e}")
            return None
    
    def listen(self) -> Optional[str]:
        return self.transcribe_audio()

class SpeechServiceFactory(ServiceFactory[WhisperSTT], SingletonMixin):
    def create(self, **kwargs) -> WhisperSTT:
        return WhisperSTT()
    
    def validate_dependencies(self) -> bool:
        try:
            import sounddevice as sd
            import whisper
            import scipy
            import numpy
            
            # Check audio devices
            devices = sd.query_devices()
            if len(devices) == 0:
                return False
            
            return True
            
        except ImportError:
            return False
        except Exception:
            return False

# Global instances
_stt_service: Optional[WhisperSTT] = None
_factory: Optional[SpeechServiceFactory] = None

def get_stt_service() -> WhisperSTT:
    global _stt_service, _factory
    
    if _stt_service is None:
        if _factory is None:
            _factory = SpeechServiceFactory()
        _stt_service = _factory.create()
    
    return _stt_service
