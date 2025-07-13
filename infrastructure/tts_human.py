"""
Enhanced TTS with more human and natural voice
Supports multiple TTS engines for better voice quality
Handles long text with proper segmentation and FAST processing
"""

import os
import re
import tempfile
import subprocess
import requests
import asyncio
import concurrent.futures
import threading
import time
from typing import Optional, Dict, Any, List
from shared.config import Config

class HumanTTS:
    def __init__(self):
        self.config = Config.get_speech_settings()
        self.temp_dir = tempfile.gettempdir()
        self.max_segment_length = 300  # Maximum characters per segment
        self.max_workers = 4  # Parallel processing workers
        
    def speak(self, text: str, engine: str = None) -> bool:
        """
        FAST speak text dengan parallel processing
        Args:
            text: Text to speak
            engine: TTS engine ('edge', 'piper', 'gtts', 'festival')
        """
        if not engine:
            engine = self.config.get('tts_engine', 'edge')
        
        # Clean and prepare text
        text = self._clean_text(text)
        
        # Split long text into segments
        segments = self._split_text_intelligently(text)
        
        print(f"FAST speech generation with {engine} ({len(segments)} segments)...")
        
        try:
            if len(segments) == 1:
                # Single segment - direct processing
                return self._speak_single_segment_fast(segments[0], engine)
            else:
                # Multiple segments - PARALLEL processing
                return self._speak_multiple_segments_parallel(segments, engine)
                
        except Exception as e:
            print(f"Error with {engine}: {e}")
            # Fallback to gTTS
            return self._speak_gtts_fast(text)
    
    def _speak_multiple_segments_parallel(self, segments: List[str], engine: str) -> bool:
        """
        SUPER FAST parallel processing for multiple segments
        """
        print("Using parallel processing for SPEED...")
        
        try:
            if engine == 'edge':
                return self._speak_edge_parallel(segments)
            elif engine == 'gtts':
                return self._speak_gtts_parallel(segments)
            else:
                # For other engines, use sequential with minimal delay
                return self._speak_sequential_fast(segments, engine)
                
        except Exception as e:
            print(f"Parallel processing error: {e}")
            return False
    
    def _speak_edge_parallel(self, segments: List[str]) -> bool:
        """
        ULTRA FAST Edge TTS with async parallel processing
        """
        async def generate_all_audio():
            # Create all TTS tasks simultaneously
            tasks = []
            for i, segment in enumerate(segments):
                task = self._generate_edge_audio_async(segment, i)
                tasks.append(task)
            
            # Run ALL tasks in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter successful results
            audio_files = []
            for i, result in enumerate(results):
                if isinstance(result, str) and os.path.exists(result):
                    audio_files.append((i, result))
                else:
                    print(f"Segment {i+1} failed: {result}")
            
            # Sort by order
            audio_files.sort(key=lambda x: x[0])
            return [audio_file for _, audio_file in audio_files]
        
        try:
            # Generate ALL audio files in parallel
            start_time = time.time()
            audio_files = asyncio.run(generate_all_audio())
            generation_time = time.time() - start_time
            
            print(f"Generated {len(audio_files)} audio files in {generation_time:.2f}s")
            
            if not audio_files:
                return False
            
            # Play audio files in rapid sequence
            return self._play_audio_sequence_fast(audio_files)
            
        except Exception as e:
            print(f"Edge parallel error: {e}")
            return False
    
    async def _generate_edge_audio_async(self, text: str, index: int) -> str:
        """
        Async Edge TTS generation untuk natural human-like speech
        """
        try:
            import edge_tts
            
            # Natural voice configuration
            voice = self.config.get('tts_voice', 'id-ID-ArdiNeural')
            rate = self.config.get('tts_rate', '+5%')  # Natural conversation speed
            volume = self.config.get('tts_volume', '+15%')  # Comfortable volume
            pitch = self.config.get('tts_pitch', '+0Hz')  # Natural pitch
            
            # Create TTS dengan natural settings
            tts = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                volume=volume,
                pitch=pitch
            )
            
            # Generate to temporary file
            temp_file_path = os.path.join(self.temp_dir, f'tts_natural_{index}_{int(time.time())}.mp3')
            await tts.save(temp_file_path)
            
            return temp_file_path
            
        except Exception as e:
            print(f"Natural TTS generation error for segment {index}: {e}")
            return ""
    
    def _play_audio_sequence_fast(self, audio_files: List[str]) -> bool:
        """
        Natural audio playback dengan human-like speed dan tanpa timeout
        """
        try:
            print(f"🎵 Natural playback of {len(audio_files)} segments...")
            
            # Play audio files sequentially dengan natural timing
            for i, audio_file in enumerate(audio_files):
                try:
                    # Check if file exists
                    if not os.path.exists(audio_file):
                        print(f"Audio file {i+1} not found: {audio_file}")
                        continue
                    
                    print(f"Playing segment {i+1}/{len(audio_files)}...")
                    
                    # Natural mpv command tanpa timeout issues
                    cmd = [
                        'mpv',
                        '--no-video',
                        '--really-quiet',
                        '--no-terminal',  # No terminal output
                        '--audio-buffer=0.5',  # Reasonable buffer
                        '--speed=1.0',  # Normal human speed
                        '--volume=80',  # Comfortable volume
                        audio_file
                    ]
                    
                    # Run dengan timeout yang lebih reasonable
                    result = subprocess.run(cmd, capture_output=True, timeout=30)
                    
                    if result.returncode != 0:
                        print(f"Audio {i+1} playback issue, trying alternative...")
                        # Fallback to aplay if mpv has issues
                        subprocess.run(['aplay', audio_file], capture_output=True, timeout=20)
                    
                    # Natural pause antar segment (seperti manusia bernapas)
                    if i < len(audio_files) - 1:
                        time.sleep(0.3)  # Natural pause 300ms
                    
                except subprocess.TimeoutExpired:
                    print(f"Audio {i+1} timeout, skipping...")
                    continue
                except Exception as e:
                    print(f"Audio {i+1} error: {e}")
                    continue
            
            # Cleanup ALL files
            self._cleanup_files_fast(audio_files)
            
            print("✅ Natural playback completed!")
            return True
            
        except Exception as e:
            print(f"Natural playback error: {e}")
            return False
    
    def _cleanup_files_fast(self, audio_files: List[str]):
        """
        Fast cleanup dengan threading
        """
        def cleanup_file(file_path):
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except:
                pass
        
        # Cleanup files in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(cleanup_file, file_path) for file_path in audio_files]
            concurrent.futures.wait(futures, timeout=5)
    
    def _speak_single_segment_fast(self, text: str, engine: str) -> bool:
        """
        FAST single segment processing
        """
        if engine == 'edge':
            return self._speak_edge_tts_fast(text)
        elif engine == 'gtts':
            return self._speak_gtts_fast(text)
        else:
            return self._speak_gtts_fast(text)  # Fallback
    
    def _speak_edge_tts_fast(self, text: str) -> bool:
        """
        Natural Edge TTS untuk single segment
        """
        try:
            import edge_tts
            
            async def generate_natural_speech():
                voice = self.config.get('tts_voice', 'id-ID-ArdiNeural')
                rate = self.config.get('tts_rate', '+5%')  # Natural speed
                volume = self.config.get('tts_volume', '+15%')
                pitch = self.config.get('tts_pitch', '+0Hz')
                
                tts = edge_tts.Communicate(
                    text=text, 
                    voice=voice, 
                    rate=rate,
                    volume=volume,
                    pitch=pitch
                )
                temp_file_path = os.path.join(self.temp_dir, f'tts_natural_{int(time.time())}.mp3')
                await tts.save(temp_file_path)
                return temp_file_path
            
            # Generate natural speech
            audio_file = asyncio.run(generate_natural_speech())
            
            # Natural playback with fallback
            success = self._play_single_audio_natural(audio_file)
            
            # Cleanup
            try:
                os.unlink(audio_file)
            except Exception:
                pass
            
            return success
            
        except Exception as e:
            print(f"Natural Edge TTS error: {e}")
            return False
    
    def _play_single_audio_natural(self, audio_file: str) -> bool:
        """
        Natural audio playback dengan fallback player
        """
        try:
            if not os.path.exists(audio_file):
                print(f"Audio file not found: {audio_file}")
                return False
            
            # Try mpv first
            try:
                cmd = [
                    'mpv',
                    '--no-video',
                    '--really-quiet',
                    '--no-terminal',
                    '--audio-buffer=0.5',
                    '--speed=1.0',
                    '--volume=80',
                    audio_file
                ]
                
                result = subprocess.run(cmd, capture_output=True, timeout=30)
                
                if result.returncode == 0:
                    return True
                else:
                    print("mpv failed, trying fallback...")
                    
            except subprocess.TimeoutExpired:
                print("mpv timeout, trying fallback...")
            
            # Fallback to aplay
            try:
                result = subprocess.run(['aplay', audio_file], capture_output=True, timeout=25)
                if result.returncode == 0:
                    return True
                else:
                    print("aplay failed, trying paplay...")
            except subprocess.TimeoutExpired:
                print("aplay timeout, trying paplay...")
            
            # Final fallback to paplay (PulseAudio)
            try:
                result = subprocess.run(['paplay', audio_file], capture_output=True, timeout=25)
                return result.returncode == 0
            except subprocess.TimeoutExpired:
                print("All audio players timed out")
                return False
                
        except Exception as e:
            print(f"Audio playback error: {e}")
            return False
    
    def _speak_gtts_fast(self, text: str) -> bool:
        """
        FAST gTTS implementation
        """
        try:
            from gtts import gTTS
            
            # Fast gTTS generation
            tts = gTTS(text=text, lang=self.config['tts_language'], slow=False)
            temp_file_path = os.path.join(self.temp_dir, f'tts_gtts_{int(time.time())}.mp3')
            tts.save(temp_file_path)
            
            # Fast playback
            result = subprocess.run([
                'mpv', '--no-video', '--really-quiet', '--no-cache', temp_file_path
            ], check=False, capture_output=True, timeout=15)
            
            # Cleanup
            try:
                os.unlink(temp_file_path)
            except:
                pass
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"Fast gTTS error: {e}")
            return False
    
    def _speak_gtts_parallel(self, segments: List[str]) -> bool:
        """
        FAST gTTS dengan parallel processing
        """
        try:
            from gtts import gTTS
            
            def generate_gtts_audio(text, index):
                try:
                    tts = gTTS(text=text, lang=self.config['tts_language'], slow=False)
                    temp_file = os.path.join(self.temp_dir, f'tts_gtts_{index}_{int(time.time())}.mp3')
                    tts.save(temp_file)
                    return temp_file
                except Exception as e:
                    print(f"gTTS segment {index} error: {e}")
                    return None
            
            # Generate all audio files in parallel
            print("Generating gTTS audio in parallel...")
            start_time = time.time()
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [executor.submit(generate_gtts_audio, segment, i) 
                          for i, segment in enumerate(segments)]
                
                audio_files = []
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    result = future.result()
                    if result:
                        audio_files.append((i, result))
            
            generation_time = time.time() - start_time
            print(f"Generated {len(audio_files)} gTTS files in {generation_time:.2f}s")
            
            # Sort by order and play
            audio_files.sort(key=lambda x: x[0])
            ordered_files = [audio_file for _, audio_file in audio_files]
            
            return self._play_audio_sequence_fast(ordered_files)
            
        except Exception as e:
            print(f"gTTS parallel error: {e}")
            return False
    
    def _speak_sequential_fast(self, segments: List[str], engine: str) -> bool:
        """
        Fast sequential processing untuk engines lain
        """
        try:
            audio_files = []
            
            for i, segment in enumerate(segments):
                print(f"Processing segment {i+1}/{len(segments)}...")
                
                if engine == 'piper':
                    audio_file = self._generate_piper_audio_fast(segment, i)
                elif engine == 'festival':
                    audio_file = self._generate_festival_audio_fast(segment, i)
                else:
                    audio_file = self._generate_gtts_audio_fast(segment, i)
                
                if audio_file:
                    audio_files.append(audio_file)
            
            return self._play_audio_sequence_fast(audio_files)
            
        except Exception as e:
            print(f"Sequential fast error: {e}")
            return False
    
    def _generate_gtts_audio_fast(self, text: str, index: int) -> str:
        """
        Fast gTTS generation
        """
        try:
            from gtts import gTTS
            
            tts = gTTS(text=text, lang=self.config['tts_language'], slow=False)
            temp_file = os.path.join(self.temp_dir, f'tts_gtts_{index}_{int(time.time())}.mp3')
            tts.save(temp_file)
            return temp_file
            
        except Exception as e:
            print(f"Fast gTTS generation error: {e}")
            return ""
    
    def _generate_piper_audio_fast(self, text: str, index: int) -> str:
        """
        Fast Piper TTS generation
        """
        try:
            temp_file = os.path.join(self.temp_dir, f'tts_piper_{index}_{int(time.time())}.wav')
            
            # Piper command untuk Indonesian
            cmd = [
                'piper',
                '--model', 'id-ID-fajri-medium',
                '--output_file', temp_file
            ]
            
            # Run dengan input text
            process = subprocess.run(cmd, input=text, text=True, 
                                   capture_output=True, timeout=10)
            
            if process.returncode == 0 and os.path.exists(temp_file):
                return temp_file
            else:
                print(f"Piper generation failed: {process.stderr}")
                return ""
                
        except Exception as e:
            print(f"Fast Piper generation error: {e}")
            return ""
    
    def _generate_festival_audio_fast(self, text: str, index: int) -> str:
        """
        Fast Festival TTS generation
        """
        try:
            temp_file = os.path.join(self.temp_dir, f'tts_festival_{index}_{int(time.time())}.wav')
            
            # Festival command
            cmd = [
                'festival',
                '--tts',
                '--language', 'indonesian',
                '--output', temp_file
            ]
            
            # Run dengan input text
            process = subprocess.run(cmd, input=text, text=True, 
                                   capture_output=True, timeout=10)
            
            if process.returncode == 0 and os.path.exists(temp_file):
                return temp_file
            else:
                return ""
                
        except Exception as e:
            print(f"Fast Festival generation error: {e}")
            return ""
    
    def _clean_text(self, text: str) -> str:
        """Clean text untuk TTS yang lebih baik"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Fix common pronunciation issues
        replacements = {
            'PDIP': 'P D I P',
            'DKI': 'D K I',
            'SMP': 'S M P', 
            'SMA': 'S M A',
            'SD': 'S D',
            'TransJakarta': 'Trans Jakarta',
            'Busway': 'Bus Way',
            '1980-an': 'tahun delapan puluhan',
            'Jokowi': 'Joko Wi',
            'DPC': 'D P C',
            'RI': 'R I',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def _split_text_intelligently(self, text: str) -> List[str]:
        """Split text secara intelligent berdasarkan kalimat dan panjang"""
        if len(text) <= self.max_segment_length:
            return [text]
        
        # Split by sentences first
        sentences = re.split(r'[.!?]+', text)
        segments = []
        current_segment = ""
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Add period back
            if not sentence.endswith(('.', '!', '?')):
                sentence += '.'
            
            # Check if adding this sentence exceeds limit
            if len(current_segment + " " + sentence) > self.max_segment_length:
                if current_segment:
                    segments.append(current_segment.strip())
                    current_segment = sentence
                else:
                    # Single sentence too long, split by clauses
                    clauses = re.split(r'[,;]+', sentence)
                    for clause in clauses:
                        clause = clause.strip()
                        if clause:
                            if len(current_segment + " " + clause) > self.max_segment_length:
                                if current_segment:
                                    segments.append(current_segment.strip())
                                current_segment = clause
                            else:
                                current_segment += " " + clause if current_segment else clause
            else:
                current_segment += " " + sentence if current_segment else sentence
        
        if current_segment:
            segments.append(current_segment.strip())
        
        return segments
    
    def _speak_single_segment(self, text: str, engine: str) -> bool:
        """Speak single text segment"""
        if engine == 'edge':
            return self._speak_edge_tts(text)
        elif engine == 'piper':
            return self._speak_piper(text)
        elif engine == 'festival':
            return self._speak_festival(text)
        elif engine == 'gtts':
            return self._speak_gtts(text)
        else:
            return self._speak_gtts(text)
    
    def _speak_multiple_segments(self, segments: List[str], engine: str) -> bool:
        """Speak multiple segments with proper pacing"""
        audio_files = []
        
        try:
            # Generate audio for each segment
            for i, segment in enumerate(segments):
                print(f"Processing segment {i+1}/{len(segments)}...")
                
                if engine == 'edge':
                    audio_file = self._generate_edge_audio(segment)
                elif engine == 'gtts':
                    audio_file = self._generate_gtts_audio(segment)
                else:
                    # For other engines, use direct playback
                    success = self._speak_single_segment(segment, engine)
                    if not success:
                        return False
                    # Add small pause between segments
                    import time
                    time.sleep(0.5)
                    continue
                
                if audio_file:
                    audio_files.append(audio_file)
                else:
                    return False
            
            # Play audio files sequentially with proper pacing
            if audio_files:
                return self._play_audio_sequence(audio_files)
            
            return True
            
        except Exception as e:
            print(f"Error processing multiple segments: {e}")
            return False
        finally:
            # Cleanup temporary files
            for audio_file in audio_files:
                try:
                    if os.path.exists(audio_file):
                        os.unlink(audio_file)
                except:
                    pass
    
    def _generate_edge_audio(self, text: str) -> Optional[str]:
        """Generate audio file using Edge TTS"""
        try:
            import edge_tts
            
            # Enhanced voice configuration
            voice = self.config.get('tts_voice', 'id-ID-ArdiNeural')
            rate = self.config.get('tts_rate', '+0%')
            volume = self.config.get('tts_volume', '+0%')
            pitch = self.config.get('tts_pitch', '+0Hz')
            
            async def generate_audio():
                # Create TTS with enhanced settings
                tts = edge_tts.Communicate(
                    text=text,
                    voice=voice,
                    rate=rate,
                    volume=volume,
                    pitch=pitch
                )
                
                # Generate to temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                await tts.save(temp_file.name)
                return temp_file.name
            
            return asyncio.run(generate_audio())
            
        except Exception as e:
            print(f"Error generating Edge audio: {e}")
            return None
    
    def _generate_gtts_audio(self, text: str) -> Optional[str]:
        """Generate audio file using gTTS"""
        try:
            from gtts import gTTS
            
            # Enhanced gTTS settings
            tts = gTTS(
                text=text, 
                lang=self.config['tts_language'],
                slow=False,  # Normal speed
                tld='co.id'  # Indonesian domain for better pronunciation
            )
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            tts.save(temp_file.name)
            return temp_file.name
            
        except Exception as e:
            print(f"Error generating gTTS audio: {e}")
            return None
    
    def _play_audio_sequence(self, audio_files: List[str]) -> bool:
        """Play audio files in sequence with proper timing"""
        try:
            for i, audio_file in enumerate(audio_files):
                print(f"Playing segment {i+1}/{len(audio_files)}...")
                
                # Play audio
                result = subprocess.run(
                    ['mpv', '--no-video', '--really-quiet', audio_file],
                    check=False,
                    capture_output=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    print(f"Warning: Audio playback issue for segment {i+1}")
                
                # Small pause between segments for natural flow
                if i < len(audio_files) - 1:
                    import time
                    time.sleep(0.3)
            
            print("Audio playback completed")
            return True
            
        except Exception as e:
            print(f"Error playing audio sequence: {e}")
            return False
            if engine == 'edge':
                return self._speak_edge_tts(text)
            elif engine == 'piper':
                return self._speak_piper(text)
            elif engine == 'festival':
                return self._speak_festival(text)
            elif engine == 'gtts':
                return self._speak_gtts(text)
            else:
                print(f"Unknown TTS engine: {engine}")
                return self._speak_gtts(text)  # Fallback
                
        except Exception as e:
            print(f"Error with {engine}: {e}")
            # Fallback to gTTS
            return self._speak_gtts(text)
    
    def _speak_edge_tts(self, text: str) -> bool:
        """
        Microsoft Edge TTS - Enhanced for better quality and natural voice
        """
        try:
            import edge_tts
            
            # Enhanced voice configuration
            voice = self.config.get('tts_voice', 'id-ID-ArdiNeural')
            rate = self.config.get('tts_rate', '+0%')
            volume = self.config.get('tts_volume', '+0%')
            pitch = self.config.get('tts_pitch', '+0Hz')
            
            async def generate_speech():
                # Use enhanced settings for more natural speech
                tts = edge_tts.Communicate(
                    text=text,
                    voice=voice,
                    rate=rate,
                    volume=volume,
                    pitch=pitch
                )
                
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
                await tts.save(temp_file.name)
                return temp_file.name
            
            # Generate speech
            audio_file = asyncio.run(generate_speech())
            
            # Play audio with better quality settings
            return self._play_audio_enhanced(audio_file)
            
        except ImportError:
            print("edge-tts tidak terinstall. Install dengan: pip install edge-tts")
            return False
        except Exception as e:
            print(f"Edge TTS error: {e}")
            return False
            return False
        except Exception as e:
            print(f"Edge TTS error: {e}")
            return False
    
    def _speak_piper(self, text: str) -> bool:
        """
        Piper TTS - Local neural TTS dengan suara yang sangat natural
        """
        try:
            # Piper command
            piper_model = self.config.get('piper_model', 'id_ID-fajri-medium')
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
                cmd = [
                    'piper',
                    '--model', piper_model,
                    '--output_file', temp_file.name
                ]
                
                result = subprocess.run(
                    cmd,
                    input=text,
                    text=True,
                    capture_output=True
                )
                
                if result.returncode == 0:
                    return self._play_audio(temp_file.name)
                else:
                    print(f"Piper error: {result.stderr}")
                    return False
                    
        except FileNotFoundError:
            print("Piper tidak terinstall. Install dari: https://github.com/rhasspy/piper")
            return False
        except Exception as e:
            print(f"Piper error: {e}")
            return False
    
    def _speak_festival(self, text: str) -> bool:
        """
        Festival TTS - Classic TTS dengan customizable voice
        """
        try:
            # Festival command dengan voice configuration
            cmd = [
                'festival',
                '--tts',
                '--pipe'
            ]
            
            # Voice script untuk Indonesian-like pronunciation
            festival_script = f"""
            (voice_default)
            (Parameter.set 'Duration_Stretch 1.2)
            (Parameter.set 'Int_F0_Shift 0.8)
            (SayText "{text}")
            """
            
            result = subprocess.run(
                cmd,
                input=festival_script,
                text=True,
                capture_output=True
            )
            
            if result.returncode == 0:
                print("Festival TTS completed")
                return True
            else:
                print(f"Festival error: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("Festival tidak terinstall. Install dengan: sudo apt install festival")
            return False
        except Exception as e:
            print(f"Festival error: {e}")
            return False
    
    def _speak_gtts(self, text: str) -> bool:
        """
        Google TTS - Fallback option
        """
        try:
            from gtts import gTTS
            
            tts = gTTS(text, lang=self.config['tts_language'])
            
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                tts.save(temp_file.name)
                return self._play_audio(temp_file.name)
                
        except Exception as e:
            print(f"gTTS error: {e}")
            return False
    
    def _play_audio(self, audio_file: str) -> bool:
        """
        Play audio file dengan berbagai player
        """
        try:
            # Audio players in order of preference
            players = [
                ['mpv', '--no-video', '--really-quiet'],
                ['vlc', '--intf', 'dummy', '--play-and-exit'],
                ['aplay'],
                ['paplay']
            ]
            
            for player_cmd in players:
                try:
                    result = subprocess.run(
                        player_cmd + [audio_file],
                        check=False,
                        capture_output=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        print("Audio played successfully")
                        # Cleanup
                        os.unlink(audio_file)
                        return True
                        
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            
            print("No audio player found")
            return False
            
        except Exception as e:
            print(f"Audio playback error: {e}")
            return False
    
    def _play_audio_enhanced(self, audio_file: str) -> bool:
        """
        Play audio with enhanced quality settings for natural speech
        """
        try:
            # Enhanced mpv settings for better audio quality
            mpv_args = [
                'mpv',
                '--no-video',
                '--really-quiet',
                '--audio-normalize-downmix=yes',  # Normalize audio levels
                '--af=dynaudnorm',                # Dynamic audio normalization  
                '--volume=85',                    # Comfortable volume level
                '--speed=0.95',                   # Slightly slower for clarity
                audio_file
            ]
            
            result = subprocess.run(
                mpv_args,
                check=False,
                capture_output=True,
                timeout=60  # Increased timeout for long audio
            )
            
            if result.returncode == 0:
                print("High-quality audio playback completed")
                # Cleanup
                try:
                    os.unlink(audio_file)
                except:
                    pass
                return True
            else:
                print(f"Audio playback warning: {result.stderr.decode()}")
                # Try fallback without enhanced settings
                return self._play_audio_fallback(audio_file)
                
        except subprocess.TimeoutExpired:
            print("Audio playback timeout - audio may be too long")
            return False
        except Exception as e:
            print(f"Enhanced audio playback error: {e}")
            return self._play_audio_fallback(audio_file)
    
    def _play_audio_fallback(self, audio_file: str) -> bool:
        """
        Fallback audio player with basic settings
        """
        try:
            # Basic audio players in order of preference
            players = [
                ['mpv', '--no-video', '--really-quiet'],
                ['vlc', '--intf', 'dummy', '--play-and-exit'],
                ['aplay'],
                ['paplay']
            ]
            
            for player_cmd in players:
                try:
                    result = subprocess.run(
                        player_cmd + [audio_file],
                        check=False,
                        capture_output=True,
                        timeout=30
                    )
                    
                    if result.returncode == 0:
                        print("Fallback audio playback completed")
                        # Cleanup
                        try:
                            os.unlink(audio_file)
                        except:
                            pass
                        return True
                        
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    continue
            
            print("No audio player available")
            return False
            
        except Exception as e:
            print(f"Fallback audio playback error: {e}")
            return False
    
    def list_available_engines(self) -> Dict[str, Dict[str, Any]]:
        """
        List TTS engines yang tersedia
        """
        engines = {
            'edge': {
                'name': 'Microsoft Edge TTS',
                'quality': 'Excellent',
                'human_like': '95%',
                'languages': ['Indonesian', 'English', 'Many others'],
                'voices': ['id-ID-ArdiNeural', 'id-ID-GadisNeural'],
                'requirement': 'pip install edge-tts'
            },
            'piper': {
                'name': 'Piper Neural TTS',
                'quality': 'Very Good',
                'human_like': '90%',
                'languages': ['Indonesian', 'English', 'Many others'],
                'voices': ['id_ID-fajri-medium'],
                'requirement': 'Install from GitHub'
            },
            'festival': {
                'name': 'Festival TTS',
                'quality': 'Good',
                'human_like': '60%',
                'languages': ['English', 'Basic others'],
                'voices': ['Male', 'Female'],
                'requirement': 'sudo apt install festival'
            },
            'gtts': {
                'name': 'Google TTS',
                'quality': 'Good',
                'human_like': '70%',
                'languages': ['Indonesian', 'Many others'],
                'voices': ['Default'],
                'requirement': 'pip install gtts (already installed)'
            }
        }
        
        return engines
    
    def test_engines(self):
        """
        Test semua TTS engines yang tersedia
        """
        test_text = "Halo, ini adalah test suara dari Zorglub AI"
        
        engines = self.list_available_engines()
        
        print("🎤 Testing TTS Engines:")
        print("=" * 50)
        
        for engine_name, engine_info in engines.items():
            print(f"\n Testing {engine_info['name']}...")
            print(f"   Quality: {engine_info['quality']}")
            print(f"   Human-like: {engine_info['human_like']}")
            
            success = self.speak(test_text, engine_name)
            
            if success:
                print(f"{engine_name} works!")
            else:
                print(f"{engine_name} failed")
                print(f"Install with: {engine_info['requirement']}")
            
            input("   Press Enter untuk next engine...")

# Backward compatibility
def speak_text(text: str):
    """Wrapper untuk compatibility dengan kode existing"""
    tts = HumanTTS()
    return tts.speak(text)
