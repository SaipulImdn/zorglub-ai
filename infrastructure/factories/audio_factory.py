import asyncio
import concurrent.futures
import threading
import subprocess
import tempfile
import os
import time
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import re
from shared.config import Config
from .base_factory import ServiceFactory, SingletonMixin, resource_manager
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / 'audio_filter'))
from audio_filter.audio_filter import AudioFilter

class AudioQueue:
    def __init__(self):
        self._queue = asyncio.Queue()
        self._is_playing = False
        self._lock = threading.Lock()
    
    async def add_audio(self, audio_file: str):
        await self._queue.put(audio_file)
    
    async def play_queue(self):
        with self._lock:
            if self._is_playing:
                return
            self._is_playing = True
        
        try:
            while not self._queue.empty():
                audio_file = await self._queue.get()
                await self._play_audio_file(audio_file)
                self._queue.task_done()
        finally:
            with self._lock:
                self._is_playing = False
    
    async def _play_audio_file(self, audio_file: str):
        try:
            process = await asyncio.create_subprocess_exec(
                'mpv', '--no-video', '--really-quiet', audio_file,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await process.wait()
        except Exception as e:
            print(f"Error playing audio: {e}")
        finally:
            try:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            except Exception:
                pass

class TextSegmenter:
    @staticmethod
    def split_text_intelligently(text: str, max_length: int = 200) -> List[str]:
        if len(text) <= max_length:
            return [text]
        
        text = re.sub(r'\s+', ' ', text.strip())
        sentences = re.split(r'[.!?]+', text)
        return TextSegmenter._process_sentences(sentences, max_length)
    
    @staticmethod
    def _process_sentences(sentences: List[str], max_length: int) -> List[str]:
        segments = []
        current_segment = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(sentence) > max_length:
                clause_segments = TextSegmenter._split_long_sentence(sentence, max_length)
                segments.extend(clause_segments)
            else:
                if len(current_segment + sentence) <= max_length:
                    current_segment += sentence + ". "
                else:
                    if current_segment:
                        segments.append(current_segment.rstrip(". "))
                    current_segment = sentence + ". "
        
        if current_segment:
            segments.append(current_segment.rstrip(". "))
        
        return [seg for seg in segments if seg.strip()]
    
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

class TTSEngineManager:
    def __init__(self):
        self.config = Config.get_speech_settings()
        self._temp_files = []
        self._lock = threading.Lock()
    
    def synthesize_text(self, text: str, engine: str = None) -> Optional[str]:
        engine = engine or self.config.get('tts_engine', 'gtts')
        try:
            return self._synthesize_with_engine(text, engine)
        except Exception as e:
            print(f"Primary TTS engine {engine} failed: {e}")
            fallback = self.config.get('fallback_engine', 'gtts')
            if fallback != engine:
                try:
                    return self._synthesize_with_engine(text, fallback)
                except Exception as e:
                    print(f"Fallback TTS engine {fallback} failed: {e}")
        return None
    
    def _synthesize_with_engine(self, text: str, engine: str) -> str:
        if engine == 'gtts':
            return self._synthesize_gtts(text)
        elif engine == 'edge':
            return self._synthesize_edge(text)
        else:
            raise ValueError(f"Unsupported TTS engine: {engine}")
    
    def _synthesize_gtts(self, text: str) -> str:
        from gtts import gTTS
        tts = gTTS(text, lang=self.config['tts_language'])
        temp_file = self._create_temp_file('.mp3')
        tts.save(temp_file)
        return temp_file
    
    def _synthesize_edge(self, text: str) -> str:
        try:
            import edge_tts
            import os
            voice = self.config.get('edge_voice', 'id-ID-ArdiNeural')
            rate = self.config.get('edge_rate', '+0%')
            volume = self.config.get('edge_volume', '+0%')
            ext = self.config.get('edge_format', 'mp3')
            if ext not in ('mp3', 'wav'):
                ext = 'mp3'
            temp_file = self._create_temp_file(f'.{ext}')
            async def _synthesize():
                communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
                await communicate.save(temp_file)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(_synthesize())
            loop.close()
            for _ in range(10):
                if os.path.exists(temp_file) and os.path.getsize(temp_file) > 1024:
                    break
                time.sleep(0.1)
            return temp_file
        except ImportError:
            raise ImportError("edge-tts not installed. Install with: pip install edge-tts")
    
    def _create_temp_file(self, suffix: str) -> str:
        temp_file = tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
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
                except Exception:
                    pass

class OptimizedTTS:
    def __init__(self):
        self.config = Config.get_speech_settings()
        self.engine_manager = TTSEngineManager()
        self.audio_queue = AudioQueue()
        self.text_segmenter = TextSegmenter()
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.audio_filter = AudioFilter()
        resource_manager.register_resource(
            self.engine_manager,
            self.engine_manager.cleanup_temp_files
        )
    
    def speak(self, text: str, engine: str = None, async_mode: bool = False) -> bool:
        if not text or not text.strip():
            return False
        try:
            segments = self.text_segmenter.split_text_intelligently(
                text.strip(),
                self.config.get('max_segment_length', 200)
            )
            if len(segments) == 1:
                return self._speak_single_segment(segments[0], engine)
            else:
                if async_mode:
                    return self._speak_segments_async(segments, engine)
                else:
                    return self._speak_segments_sequential(segments, engine)
        except Exception as e:
            print(f"Error in TTS: {e}")
            return False
    
    def _speak_single_segment(self, text: str, engine: str = None) -> bool:
        try:
            audio_file = self.engine_manager.synthesize_text(text, engine)
            if audio_file:
                self._play_audio_sync(audio_file)
                return True
        except Exception as e:
            print(f"Error speaking segment: {e}")
        return False
    
    def _speak_segments_sequential(self, segments: List[str], engine: str = None) -> bool:
        success_count = 0
        for i, segment in enumerate(segments):
            try:
                print(f"Speaking segment {i+1}/{len(segments)}")
                audio_file = self.engine_manager.synthesize_text(segment, engine)
                if audio_file:
                    self._play_audio_sync(audio_file)
                    success_count += 1
                pause = self.config.get('pause_between_segments', 0.3)
                if pause > 0 and i < len(segments) - 1:
                    time.sleep(pause)
            except Exception as e:
                print(f"Error speaking segment {i+1}: {e}")
        return success_count > 0
    
    def _speak_segments_async(self, segments: List[str], engine: str = None) -> bool:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            tasks = [
                self._synthesize_segment_async(segment, engine) 
                for segment in segments
            ]
            audio_files = loop.run_until_complete(asyncio.gather(*tasks))
            for audio_file in audio_files:
                if audio_file:
                    loop.run_until_complete(self.audio_queue.add_audio(audio_file))
            loop.run_until_complete(self.audio_queue.play_queue())
            loop.close()
            return True
        except Exception as e:
            print(f"Error in async speech: {e}")
            return False
    
    async def _synthesize_segment_async(self, text: str, engine: str = None) -> Optional[str]:
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(
                self._executor,
                self.engine_manager.synthesize_text,
                text,
                engine
            )
        except Exception as e:
            print(f"Error synthesizing segment: {e}")
            return None
    
    def _play_audio_sync(self, audio_file: str):
        try:
            if audio_file.endswith('.wav'):
                import wave
                import numpy as np
                with wave.open(audio_file, 'rb') as wf:
                    params = wf.getparams()
                    frames = wf.readframes(wf.getnframes())
                    samples = np.frombuffer(frames, dtype=np.int16)
                filtered = self.audio_filter.apply_gain(samples, 1.5)
                filtered_file = audio_file.replace('.wav', '_filtered.wav')
                with wave.open(filtered_file, 'wb') as wf:
                    wf.setparams(params)
                    wf.writeframes(filtered.tobytes())
                play_file = filtered_file
            else:
                play_file = audio_file
            subprocess.run(
                ['mpv', '--no-video', '--really-quiet', play_file],
                check=False,
                capture_output=True
            )
        except FileNotFoundError:
            print("mpv not found. Install with: sudo apt install mpv")
        except Exception as e:
            print(f"Error playing audio: {e}")
        finally:
            try:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                filtered_file = audio_file.replace('.wav', '_filtered.wav')
                if os.path.exists(filtered_file):
                    os.remove(filtered_file)
            except Exception:
                pass

class AudioServiceFactory(ServiceFactory[OptimizedTTS], SingletonMixin):
    def create(self, **kwargs) -> OptimizedTTS:
        return OptimizedTTS()
    
    def validate_dependencies(self) -> bool:
        try:
            subprocess.run(
                ['mpv', '--version'],
                capture_output=True,
                check=True
            )
            try:
                import gtts
                return True
            except ImportError:
                return False
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
        except Exception:
            return False

_tts_service: Optional[OptimizedTTS] = None
_factory: Optional[AudioServiceFactory] = None

def get_tts_service() -> OptimizedTTS:
    global _tts_service, _factory
    if _tts_service is None:
        if _factory is None:
            _factory = AudioServiceFactory()
        _tts_service = _factory.create()
    return _tts_service
