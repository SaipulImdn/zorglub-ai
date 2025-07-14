import whisper
import multiprocessing as mp
import time
import os
import tempfile
import pickle
from typing import Dict, Any, Optional, List
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

from shared.config import Config
from .multiprocess_base import (
    ServiceFactory, MultiprocessSingletonMixin, ProcessPool, 
    resource_manager, process_worker_initializer
)

def load_whisper_model(model_name: str) -> Any:
    try:
        return whisper.load_model(model_name)
    except Exception as e:
        raise RuntimeError(f"Failed to load Whisper model {model_name}: {e}")

def transcribe_audio_worker(args: tuple) -> tuple:
    audio_file, model_name, language, worker_id = args
    
    try:
        model = whisper.load_model(model_name)
        result = model.transcribe(
            audio_file,
            language=language,
            fp16=False,
            verbose=False
        )
        return worker_id, result["text"].strip(), None
    except Exception as e:
        return worker_id, None, str(e)

def record_audio_worker(args: tuple) -> tuple:
    duration, sample_rate, device, worker_id = args
    
    try:
        import sounddevice as sd
        import numpy as np
        import scipy.io.wavfile as wav
        audio = sd.rec(
            int(duration * sample_rate), 
            samplerate=sample_rate, 
            channels=1,
            blocking=True,
            device=device
        )
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix='.wav',
            dir=tempfile.gettempdir()
        )
        temp_path = temp_file.name
        temp_file.close()
        wav.write(temp_path, sample_rate, (audio * 32767).astype(np.int16))
        return worker_id, temp_path, None
    except Exception as e:
        return worker_id, None, str(e)

class MultiprocessModelCache:
    def __init__(self):
        self._manager = mp.Manager()
        self._models = self._manager.dict()
        self._model_loading = self._manager.dict()
        self._lock = self._manager.Lock()
    
    def get_model(self, model_name: str):
        with self._lock:
            if model_name in self._models:
                pass
            if model_name in self._model_loading:
                while self._model_loading.get(model_name, False):
                    time.sleep(0.1)
            else:
                self._model_loading[model_name] = True
        try:
            print(f"Loading Whisper model: {model_name} in process {os.getpid()}")
            model = whisper.load_model(model_name)
            with self._lock:
                self._models[model_name] = True
                self._model_loading[model_name] = False
            return model
        except Exception as e:
            with self._lock:
                self._model_loading[model_name] = False
            raise e
    
    def clear_cache(self):
        with self._lock:
            self._models.clear()
            self._model_loading.clear()

class MultiprocessAudioProcessor:
    def __init__(self, max_workers: Optional[int] = None):
        self.config = Config.get_recording_settings()
        self.max_workers = max_workers or min(2, mp.cpu_count())
        self._manager = mp.Manager()
        self._temp_files = self._manager.list()
        self._stats = self._manager.dict({
            'recordings': 0,
            'successful_recordings': 0,
            'failed_recordings': 0
        })
    
    def record_audio_parallel(self, count: int = 1, duration: Optional[int] = None) -> List[Optional[str]]:
        duration = duration or self.config['duration']
        sample_rate = self.config['sample_rate']
        if count == 1:
            return [self.record_audio_single(duration)]
        worker_args = [
            (duration, sample_rate, None, i) 
            for i in range(count)
        ]
        results = [None] * count
        with ProcessPool(
            max_workers=min(self.max_workers, count),
            initializer=process_worker_initializer
        ) as pool:
            futures = {}
            for args in worker_args:
                future = pool.submit(record_audio_worker, args)
                futures[future] = args[3]
            for future in as_completed(futures.keys(), timeout=duration + 10):
                worker_id = futures[future]
                try:
                    worker_id, temp_path, error = future.result()
                    if error:
                        print(f"Recording failed in worker {worker_id}: {error}")
                        self._stats['failed_recordings'] += 1
                        results[worker_id] = None
                    else:
                        self._stats['successful_recordings'] += 1
                        results[worker_id] = temp_path
                        self._temp_files.append(temp_path)
                except Exception as e:
                    print(f"Worker {worker_id} failed: {e}")
                    self._stats['failed_recordings'] += 1
                    results[worker_id] = None
        self._stats['recordings'] += count
        return results
    
    def record_audio_single(self, duration: Optional[int] = None) -> Optional[str]:
        duration = duration or self.config['duration']
        sample_rate = self.config['sample_rate']
        try:
            import sounddevice as sd
            import numpy as np
            import scipy.io.wavfile as wav
            print(f"Recording audio for {duration} seconds...")
            audio = sd.rec(
                int(duration * sample_rate), 
                samplerate=sample_rate, 
                channels=1,
                blocking=True,
                device=None
            )
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix='.wav',
                dir=tempfile.gettempdir()
            )
            temp_path = temp_file.name
            temp_file.close()
            wav.write(temp_path, sample_rate, (audio * 32767).astype(np.int16))
            self._temp_files.append(temp_path)
            print("Recording completed")
            return temp_path
        except Exception as e:
            print(f"Error recording: {e}")
            return None
    
    def cleanup_temp_files(self):
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                self._temp_files.remove(temp_file)
            except Exception as e:
                print(f"Error cleaning up {temp_file}: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        return dict(self._stats)

class MultiprocessWhisperSTT:
    def __init__(self, max_workers: Optional[int] = None):
        self.config = Config.get_speech_settings()
        self.max_workers = max_workers or min(2, mp.cpu_count())
        self.model_cache = MultiprocessModelCache()
        self.audio_processor = MultiprocessAudioProcessor(max_workers)
        self._manager = mp.Manager()
        self._stats = self._manager.dict({
            'transcriptions': 0,
            'successful_transcriptions': 0,
            'failed_transcriptions': 0,
            'cache_hits': 0
        })
        resource_manager.register_resource(
            self.audio_processor, 
            self.audio_processor.cleanup_temp_files
        )
    
    def transcribe_audio(self, audio_file: Optional[str] = None) -> Optional[str]:
        if audio_file is None:
            audio_file = self.audio_processor.record_audio_single()
            if audio_file is None:
                return None
        self._stats['transcriptions'] += 1
        try:
            model = self.model_cache.get_model(self.config['whisper_model'])
            print("Transcribing audio...")
            result = model.transcribe(
                audio_file,
                language=self.config['stt_language'],
                fp16=False,
                verbose=False
            )
            if audio_file in self.audio_processor._temp_files:
                try:
                    os.remove(audio_file)
                    self.audio_processor._temp_files.remove(audio_file)
                except Exception:
                    pass
            self._stats['successful_transcriptions'] += 1
            return result["text"].strip()
        except Exception as e:
            self._stats['failed_transcriptions'] += 1
            print(f"Error transcribing: {e}")
            return None
    
    def transcribe_batch(self, audio_files: List[str]) -> List[Optional[str]]:
        if not audio_files:
            return []
        self._stats['transcriptions'] += len(audio_files)
        worker_args = [
            (audio_file, self.config['whisper_model'], self.config['stt_language'], i)
            for i, audio_file in enumerate(audio_files)
        ]
        results = [None] * len(audio_files)
        with ProcessPool(
            max_workers=min(self.max_workers, len(audio_files)),
            initializer=process_worker_initializer
        ) as pool:
            futures = {}
            for args in worker_args:
                future = pool.submit(transcribe_audio_worker, args)
                futures[future] = args[3]
            for future in as_completed(futures.keys(), timeout=120):
                worker_id = futures[future]
                try:
                    worker_id, text, error = future.result()
                    if error:
                        print(f"Transcription failed in worker {worker_id}: {error}")
                        self._stats['failed_transcriptions'] += 1
                        results[worker_id] = None
                    else:
                        self._stats['successful_transcriptions'] += 1
                        results[worker_id] = text
                except Exception as e:
                    print(f"Worker {worker_id} failed: {e}")
                    self._stats['failed_transcriptions'] += 1
                    results[worker_id] = None
        return results
    
    def listen(self) -> Optional[str]:
        return self.transcribe_audio()
    
    def listen_batch(self, count: int) -> List[Optional[str]]:
        audio_files = self.audio_processor.record_audio_parallel(count)
        valid_files = [f for f in audio_files if f is not None]
        if not valid_files:
            return [None] * count
        transcriptions = self.transcribe_batch(valid_files)
        result_map = {}
        valid_idx = 0
        for i, audio_file in enumerate(audio_files):
            if audio_file is not None:
                result_map[i] = transcriptions[valid_idx]
                valid_idx += 1
            else:
                result_map[i] = None
        return [result_map[i] for i in range(count)]
    
    def get_stats(self) -> Dict[str, Any]:
        transcription_stats = dict(self._stats)
        audio_stats = self.audio_processor.get_stats()
        total_transcriptions = max(transcription_stats['transcriptions'], 1)
        success_rate = (transcription_stats['successful_transcriptions'] / total_transcriptions) * 100
        return {
            'transcription': {
                **transcription_stats,
                'success_rate': f"{success_rate:.1f}%"
            },
            'audio': audio_stats
        }

class MultiprocessSpeechServiceFactory(ServiceFactory[MultiprocessWhisperSTT], MultiprocessSingletonMixin):
    def create(self, max_workers: Optional[int] = None, **kwargs) -> MultiprocessWhisperSTT:
        service = MultiprocessWhisperSTT(max_workers=max_workers)
        resource_manager.register_resource(service)
        return service
    
    def validate_dependencies(self) -> bool:
        try:
            import sounddevice as sd
            import whisper
            import scipy
            import numpy
            devices = sd.query_devices()
            if len(devices) == 0:
                return False
            return True
        except ImportError:
            return False
        except Exception:
            return False

_stt_service: Optional[MultiprocessWhisperSTT] = None
_factory: Optional[MultiprocessSpeechServiceFactory] = None

def get_multiprocess_stt_service(max_workers: Optional[int] = None) -> MultiprocessWhisperSTT:
    global _stt_service, _factory
    if _stt_service is None:
        if _factory is None:
            _factory = MultiprocessSpeechServiceFactory()
        _stt_service = _factory.create(max_workers=max_workers)
    return _stt_service

def shutdown_stt_service():
    global _stt_service
    if _stt_service:
        _stt_service.audio_processor.cleanup_temp_files()
        _stt_service = None
