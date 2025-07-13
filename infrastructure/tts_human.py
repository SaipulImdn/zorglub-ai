"""
Enhanced TTS with more human and natural voice
Supports multiple TTS engines for better voice quality
"""

import os
import tempfile
import subprocess
import requests
from typing import Optional, Dict, Any
from shared.config import Config

class HumanTTS:
    def __init__(self):
        self.config = Config.get_speech_settings()
        self.temp_dir = tempfile.gettempdir()
        
    def speak(self, text: str, engine: str = None) -> bool:
        """
        Speak text dengan berbagai engine TTS
        Args:
            text: Text untuk diucapkan
            engine: TTS engine ('edge', 'piper', 'gtts', 'festival')
        """
        if not engine:
            engine = self.config.get('tts_engine', 'edge')
        
        print(f"Generating speech dengan {engine}...")
        
        try:
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
            # Fallback ke gTTS
            return self._speak_gtts(text)
    
    def _speak_edge_tts(self, text: str) -> bool:
        """
        Microsoft Edge TTS - Suara paling natural dan human-like
        Menggunakan edge-tts library
        """
        try:
            # Import edge-tts
            import edge_tts
            import asyncio
            
            # Voice configuration untuk Indonesia
            voice_config = {
                'id': 'id-ID-ArdiNeural',  # Suara pria Indonesia
                'rate': '+0%',
                'volume': '+0%',
                'pitch': '+0Hz'
            }
            
            # Alternative voices
            voices = [
                'id-ID-ArdiNeural',    # Pria Indonesia
                'id-ID-GadisNeural',   # Wanita Indonesia
                'id-ID-ArdiNeural',    # Fallback
            ]
            
            # Select voice
            selected_voice = self.config.get('edge_voice', voices[0])
            
            async def generate_speech():
                tts = edge_tts.Communicate(text, selected_voice)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                    await tts.save(temp_file.name)
                    return temp_file.name
            
            # Generate speech
            audio_file = asyncio.run(generate_speech())
            
            # Play audio
            return self._play_audio(audio_file)
            
        except ImportError:
            print("edge-tts tidak terinstall. Install dengan: pip install edge-tts")
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
