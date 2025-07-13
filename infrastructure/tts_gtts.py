from gtts import gTTS
import os
import tempfile
import subprocess
from shared.config import Config

def speak_text(text: str):
    """Play text using TTS with mpv for WSL compatibility"""
    try:
        speech_settings = Config.get_speech_settings()
        print("Generating speech...")
        
        tts = gTTS(text, lang=speech_settings['tts_language'])
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            tts.save(temp_file.name)
            
            print("🎵 Playing audio...")
            # Play with mpv (works better in WSL)
            result = subprocess.run(
                [Config.AUDIO_PLAYER, '--no-video', '--really-quiet', temp_file.name], 
                check=False, 
                capture_output=True
            )
            
            if result.returncode != 0:
                print("Audio playback may have issues (normal in some environments)")
            
            # Cleanup
            os.unlink(temp_file.name)
            print("Speech completed")
            
    except FileNotFoundError:
        print(f"{Config.AUDIO_PLAYER} not found. Install with: sudo apt install {Config.AUDIO_PLAYER}")
        print(f"AI Response (text only): {text}")
    except Exception as e:
        print(f"Error speaking: {e}")
        print(f"AI Response (text only): {text}")
