import multiprocessing as mp
import subprocess
import tempfile
import os
import time
import re
from typing import Dict, Any, Optional, List
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

from shared.config import Config
from .multiprocess_base import (
    ServiceFactory, MultiprocessSingletonMixin, ProcessPool, 
    ProcessSafeQueue, resource_manager, process_worker_initializer
)

def synthesize_text_worker(args: tuple) -> tuple:
    text, engine, config, worker_id = args
    
    try:
        if engine == 'gtts':
            return _synthesize_gtts_worker(text, config, worker_id)
        elif engine == 'edge':
            return _synthesize_edge_worker(text, config, worker_id)
        else:
            return worker_id, None, f"Unsupported TTS engine: {engine}"
            
    except Exception as e:
        return worker_id, None, str(e)

def _synthesize_gtts_worker(text: str, config: Dict, worker_id: int) -> tuple:
    try:
        from gtts import gTTS
        
        tts = gTTS(text, lang=config['tts_language'])
        
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.mp3',
            dir=tempfile.gettempdir()
        )
        
        temp_path = temp_file.name
        temp_file.close()
        
        tts.save(temp_path)
        
        return worker_id, temp_path, None
        
    except Exception as e:
        return worker_id, None, str(e)

def _synthesize_edge_worker(text: str, config: Dict, worker_id: int) -> tuple:
    try:
        import edge_tts
        import asyncio
        
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.mp3',
            dir=tempfile.gettempdir()
        )
        
        temp_path = temp_file.name
        temp_file.close()
        
        voice = config.get('edge_voice', 'id-ID-ArdiNeural')
        
        async def _synthesize():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(temp_path)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_synthesize())
        loop.close()
        
        return worker_id, temp_path, None
        
    except ImportError:
        return worker_id, None, "edge-tts not installed. Install with: pip install edge-tts"
    except Exception as e:
        return worker_id, None, str(e)

def play_audio_worker(args: tuple) -> tuple:
    audio_file, player_cmd, worker_id = args
    
    try:
        result = subprocess.run(
            player_cmd + [audio_file],
            check=False,
            capture_output=True,
            timeout=30
        )
        
        success = result.returncode == 0
        error_msg = result.stderr.decode() if result.stderr else None
        
        return worker_id, success, error_msg
        
    except subprocess.TimeoutExpired:
        return worker_id, False, "Audio playback timeout"
    except Exception as e:
        return worker_id, False, str(e)

class MultiprocessTextSegmenter:    
    @staticmethod
    def split_text_parallel(texts: List[str], max_length: int = 200, max_workers: int = 2) -> List[List[str]]:
        if not texts:
            return []
        
        if len(texts) == 1:
            return [MultiprocessTextSegmenter.split_text_single(texts[0], max_length)]
        
        if len(texts) > 4:
            with ProcessPool(
                max_workers=min(max_workers, len(texts)),
                initializer=process_worker_initializer
            ) as pool:
                futures = {}
                for i, text in enumerate(texts):
                    future = pool.submit(
                        MultiprocessTextSegmenter.split_text_single, 
                        text, max_length
                    )
                    futures[future] = i
                
                results = [None] * len(texts)
                for future in as_completed(futures.keys()):
                    index = futures[future]
                    try:
                        results[index] = future.result()
                    except Exception as e:
                        print(f"Text segmentation failed for text {index}: {e}")
                        results[index] = [texts[index]]
                
                return results
        else:
            return [
                MultiprocessTextSegmenter.split_text_single(text, max_length)
                for text in texts
            ]
    
    @staticmethod
    def split_text_single(text: str, max_length: int = 200) -> List[str]:
        if len(text) <= max_length:
            return [text]
        
        text = re.sub(r'\s+', ' ', text.strip())
        
        sentences = re.split(r'[.!?]+', text)
        
        return MultiprocessTextSegmenter._process_sentences(sentences, max_length)
    
    @staticmethod
    def _process_sentences(sentences: List[str], max_length: int) -> List[str]:
        segments = []
        current_segment = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(sentence) > max_length:
                segments.extend(
                    MultiprocessTextSegmenter._handle_long_sentence(
                        sentence, current_segment, max_length
                    )
                )
                current_segment = ""
            else:
                current_segment = MultiprocessTextSegmenter._handle_normal_sentence(
                    sentence, current_segment, segments, max_length
                )
        
        if current_segment:
            segments.append(current_segment.rstrip(". "))
        
        return [seg for seg in segments if seg.strip()]
    
    @staticmethod
    def _handle_long_sentence(sentence: str, current_segment: str, max_length: int) -> List[str]:
        segments = []
        
        if current_segment:
            segments.append(current_segment.strip())
        
        long_segments = MultiprocessTextSegmenter._split_long_sentence(sentence, max_length)
        segments.extend(long_segments)
        
        return segments
    
    @staticmethod
    def _handle_normal_sentence(sentence: str, current_segment: str, segments: List[str], max_length: int) -> str:
        if len(current_segment + sentence) <= max_length:
            return current_segment + sentence + ". "
        else:
            if current_segment:
                segments.append(current_segment.rstrip(". "))
            return sentence + ". "
    
    @staticmethod
    def _split_long_sentence(sentence: str, max_length: int) -> List[str]:
        clauses = re.split(r'[,;:]+', sentence)
        segments = []
        current_segment = ""
        
        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue
                
            if len(current_segment + clause) <= max_length:
                current_segment += clause + ", "
            else:
                if current_segment:
                    segments.append(current_segment.rstrip(", "))
                current_segment = clause + ", "
        
        if current_segment:
            segments.append(current_segment.rstrip(", "))
        
        return segments

class MultiprocessTTSEngineManager:
    def __init__(self, max_workers: Optional[int] = None):
        self.config = Config.get_speech_settings()
        self.max_workers = max_workers or min(4, mp.cpu_count())
        
        self._manager = mp.Manager()
        self._temp_files = self._manager.list()
        self._stats = self._manager.dict({
            'syntheses': 0,
            'successful_syntheses': 0,
            'failed_syntheses': 0
        })
    
    def synthesize_text_single(self, text: str, engine: str = None) -> Optional[str]:
        engine = engine or self.config.get('tts_engine', 'gtts')
        
        self._stats['syntheses'] += 1
        
        try:
            result = self._synthesize_with_engine(text, engine)
            if result:
                self._stats['successful_syntheses'] += 1
                return result
            
            fallback = self.config.get('fallback_engine', 'gtts')
            if fallback != engine:
                result = self._synthesize_with_engine(text, fallback)
                if result:
                    self._stats['successful_syntheses'] += 1
                    return result
            
            self._stats['failed_syntheses'] += 1
            return None
            
        except Exception as e:
            print(f"Synthesis failed: {e}")
            self._stats['failed_syntheses'] += 1
            return None
    
    def synthesize_batch(self, texts: List[str], engine: str = None) -> List[Optional[str]]:
        if not texts:
            return []
        
        engine = engine or self.config.get('tts_engine', 'gtts')
        
        self._stats['syntheses'] += len(texts)
        
        worker_args = [
            (text, engine, self.config, i)
            for i, text in enumerate(texts)
        ]
        
        results = [None] * len(texts)
        
        with ProcessPool(
            max_workers=min(self.max_workers, len(texts)),
            initializer=process_worker_initializer
        ) as pool:
            futures = {}
            for args in worker_args:
                future = pool.submit(synthesize_text_worker, args)
                futures[future] = args[3]
            
            for future in as_completed(futures.keys(), timeout=60):
                worker_id = futures[future]
                try:
                    worker_id, audio_file, error = future.result()
                    
                    if error:
                        print(f"Synthesis failed in worker {worker_id}: {error}")
                        self._stats['failed_syntheses'] += 1
                        results[worker_id] = None
                    else:
                        self._stats['successful_syntheses'] += 1
                        results[worker_id] = audio_file
                        
                        if audio_file:
                            self._temp_files.append(audio_file)
                
                except Exception as e:
                    print(f"Worker {worker_id} failed: {e}")
                    self._stats['failed_syntheses'] += 1
                    results[worker_id] = None
        
        return results
    
    def _synthesize_with_engine(self, text: str, engine: str) -> Optional[str]:
        _, result, error = synthesize_text_worker(
            (text, engine, self.config, 0)
        )
        
        if error:
            raise RuntimeError(f"TTS synthesis failed with engine {engine}: {error}")
        
        if result:
            self._temp_files.append(result)
        
        return result
    
    def cleanup_temp_files(self):
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                self._temp_files.remove(temp_file)
            except Exception as e:
                print(f"Error cleaning up {temp_file}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        stats_dict = dict(self._stats)
        total_syntheses = max(stats_dict['syntheses'], 1)
        success_rate = (stats_dict['successful_syntheses'] / total_syntheses) * 100
        
        return {
            **stats_dict,
            'success_rate': f"{success_rate:.1f}%"
        }

class MultiprocessOptimizedTTS:
    def __init__(self, max_workers: Optional[int] = None):
        self.config = Config.get_speech_settings()
        self.max_workers = max_workers or min(4, mp.cpu_count())
        self.engine_manager = MultiprocessTTSEngineManager(max_workers)
        self.text_segmenter = MultiprocessTextSegmenter()
        
        self.audio_queue = ProcessSafeQueue(maxsize=50)
        
        self._manager = mp.Manager()
        self._stats = self._manager.dict({
            'speak_requests': 0,
            'successful_speaks': 0,
            'failed_speaks': 0
        })
        
        resource_manager.register_resource(
            self.engine_manager,
            self.engine_manager.cleanup_temp_files
        )
    
    def speak(self, text: str, engine: str = None, parallel_mode: bool = True) -> bool:
        if not text or not text.strip():
            return False
        
        self._stats['speak_requests'] += 1
        
        try:
            segments = self.text_segmenter.split_text_single(
                text.strip(),
                self.config.get('max_segment_length', 200)
            )
            
            if len(segments) == 1:
                success = self._speak_single_segment(segments[0], engine)
            else:
                if parallel_mode and len(segments) > 1:
                    success = self._speak_segments_parallel(segments, engine)
                else:
                    success = self._speak_segments_sequential(segments, engine)
            
            if success:
                self._stats['successful_speaks'] += 1
            else:
                self._stats['failed_speaks'] += 1
            
            return success
        
        except Exception as e:
            print(f"Error in TTS: {e}")
            self._stats['failed_speaks'] += 1
            return False
    
    def speak_batch(self, texts: List[str], engine: str = None) -> List[bool]:
        if not texts:
            return []
        
        self._stats['speak_requests'] += len(texts)
        
        all_segments = self.text_segmenter.split_text_parallel(
            texts,
            self.config.get('max_segment_length', 200),
            self.max_workers
        )
        
        flat_segments = []
        segment_to_text_map = []
        
        for text_idx, segments in enumerate(all_segments):
            for segment in segments:
                flat_segments.append(segment)
                segment_to_text_map.append(text_idx)
        
        audio_files = self.engine_manager.synthesize_batch(flat_segments, engine)
        
        results = []
        current_text_idx = 0
        current_text_files = []
        
        for i, audio_file in enumerate(audio_files):
            text_idx = segment_to_text_map[i]
            
            if text_idx != current_text_idx:
                if current_text_files:
                    success = self._play_audio_files_sequential(current_text_files)
                    results.append(success)
                
                current_text_idx = text_idx
                current_text_files = []
            
            if audio_file:
                current_text_files.append(audio_file)
        
        if current_text_files:
            success = self._play_audio_files_sequential(current_text_files)
            results.append(success)
        
        successful_count = sum(results)
        self._stats['successful_speaks'] += successful_count
        self._stats['failed_speaks'] += len(texts) - successful_count
        
        return results
    
    def _speak_single_segment(self, text: str, engine: str = None) -> bool:
        audio_file = self.engine_manager.synthesize_text_single(text, engine)
        if audio_file:
            return self._play_audio_file(audio_file)
        return False
    
    def _speak_segments_sequential(self, segments: List[str], engine: str = None) -> bool:
        success_count = 0
        
        for i, segment in enumerate(segments):
            audio_file = self.engine_manager.synthesize_text_single(segment, engine)
            if audio_file:
                if self._play_audio_file(audio_file):
                    success_count += 1
                
                pause = self.config.get('pause_between_segments', 0.3)
                if pause > 0 and i < len(segments) - 1:
                    time.sleep(pause)
        
        return success_count > 0
    
    def _speak_segments_parallel(self, segments: List[str], engine: str = None) -> bool:
        audio_files = self.engine_manager.synthesize_batch(segments, engine)
        
        return self._play_audio_files_sequential(audio_files)
    
    def _play_audio_files_sequential(self, audio_files: List[Optional[str]]) -> bool:
        success_count = 0
        
        for i, audio_file in enumerate(audio_files):
            if audio_file and self._play_audio_file(audio_file):
                success_count += 1
                
                pause = self.config.get('pause_between_segments', 0.3)
                if pause > 0 and i < len(audio_files) - 1:
                    time.sleep(pause)
        
        return success_count > 0
    
    def _play_audio_file(self, audio_file: str) -> bool:
        try:
            player_cmd = ['mpv', '--no-video', '--really-quiet']
            
            subprocess.run(
                player_cmd + [audio_file],
                check=False,
                capture_output=True,
                timeout=30
            )
            
            return True
            
        except Exception as e:
            print(f"Error playing audio: {e}")
            return False
        finally:
            try:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            except Exception:
                pass
    
    def get_stats(self) -> Dict[str, Any]:
        tts_stats = dict(self._stats)
        engine_stats = self.engine_manager.get_stats()
        
        total_requests = max(tts_stats['speak_requests'], 1)
        success_rate = (tts_stats['successful_speaks'] / total_requests) * 100
        
        return {
            'tts': {
                **tts_stats,
                'success_rate': f"{success_rate:.1f}%"
            },
            'synthesis': engine_stats
        }

class MultiprocessAudioServiceFactory(ServiceFactory[MultiprocessOptimizedTTS], MultiprocessSingletonMixin):
    def create(self, max_workers: Optional[int] = None, **kwargs) -> MultiprocessOptimizedTTS:
        service = MultiprocessOptimizedTTS(max_workers=max_workers)
        
        resource_manager.register_resource(service)
        
        return service
    
    def validate_dependencies(self) -> bool:
        try:
            subprocess.run(
                ['mpv', '--version'],
                capture_output=True,
                check=True,
                timeout=5
            )
            
            try:
                import gtts
                return True
            except ImportError:
                return False
                
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
        except Exception:
            return False

_tts_service: Optional[MultiprocessOptimizedTTS] = None
_factory: Optional[MultiprocessAudioServiceFactory] = None

def get_multiprocess_tts_service(max_workers: Optional[int] = None) -> MultiprocessOptimizedTTS:
    global _tts_service, _factory
    
    if _tts_service is None:
        if _factory is None:
            _factory = MultiprocessAudioServiceFactory()
        _tts_service = _factory.create(max_workers=max_workers)
    
    return _tts_service

def shutdown_tts_service():
    global _tts_service
    if _tts_service:
        _tts_service.engine_manager.cleanup_temp_files()
        _tts_service = None
