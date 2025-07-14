import os
import subprocess
import time

class Config:
    # Ollama Configuration
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1") 
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))
    
    # Speech Configuration
    TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "id")  # Indonesian
    STT_LANGUAGE = os.getenv("STT_LANGUAGE", "id")  # Indonesian
    
    # Enhanced TTS Configuration
    TTS_ENGINE = os.getenv("TTS_ENGINE", "edge")  # edge, piper, festival, gtts
    TTS_VOICE = os.getenv("TTS_VOICE", "id-ID-ArdiNeural")  # Voice for Edge TTS
    TTS_RATE = os.getenv("TTS_RATE", "-10%")  # Speaking rate (slower for clarity)
    TTS_VOLUME = os.getenv("TTS_VOLUME", "+10%")  # Volume (slightly louder)
    TTS_PITCH = os.getenv("TTS_PITCH", "-2Hz")  # Pitch (slightly lower for warmth)
    
    # Audio Configuration
    RECORDING_DURATION = int(os.getenv("RECORDING_DURATION", "5"))  # seconds
    SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
    
    # Whisper Configuration
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # tiny, base, small, medium, large
    
    # Audio Player
    AUDIO_PLAYER = os.getenv("AUDIO_PLAYER", "mpv")  # mpv, vlc, etc
    
    @classmethod
    def get_recording_settings(cls):
        """Get audio recording settings"""
        return {
            'duration': cls.RECORDING_DURATION,
            'sample_rate': cls.SAMPLE_RATE
        }
    
    @classmethod
    def get_ollama_settings(cls):
        """Get Ollama API settings"""
        return {
            'url': cls.OLLAMA_URL,
            'model': cls.OLLAMA_MODEL,
            'timeout': cls.OLLAMA_TIMEOUT
        }
    
    @classmethod
    def get_speech_settings(cls):
        """Get speech processing settings with natural human-like voice"""
        return {
            'tts_language': cls.TTS_LANGUAGE,
            'stt_language': cls.STT_LANGUAGE,
            'whisper_model': cls.WHISPER_MODEL,
            'tts_engine': cls.TTS_ENGINE,
            'tts_voice': cls.TTS_VOICE,
            'tts_rate': '+5%',  # Slightly faster for natural conversation
            'tts_volume': '+15%',  # Comfortable volume
            'tts_pitch': '+0Hz',  # Natural pitch
            'edge_voice': cls.TTS_VOICE,
            'piper_model': 'id_ID-fajri-medium',
            
            # NATURAL HUMAN-LIKE SETTINGS
            'max_segment_length': 200,  # Shorter segments for natural pauses
            'max_workers': 4,  # Balanced processing
            'enable_parallel_processing': True,
            'enable_natural_pauses': True,  # Natural breathing pauses
            'pause_between_segments': 0.3,  # Natural pause 300ms
            'enable_audio_streaming': False,  # Disable streaming for stability
            'fast_cleanup': True,
            
            # AUDIO PROCESSING
            'audio_buffer_size': 0.5,  # Reasonable buffer for stability
            'audio_normalization': True,
            'audio_timeout': 30,  # Longer timeout to avoid cutting off
            'use_fallback_player': True,  # Use aplay as fallback
            
            # NATURAL SPEECH SETTINGS
            'natural_speed': True,  # Human-like speaking speed
            'add_breathing_pauses': True,  # Add natural breathing
            'emotional_tone': 'conversational',  # Natural conversation tone
            'prosody_enhancement': True,  # Better intonation
            
            # FALLBACK SETTINGS
            'fallback_engine': 'gtts',
            'fallback_on_error': True,
            'max_retries': 2,
            'timeout_per_segment': 25,  # Longer timeout for natural speech
            
            # QUALITY SETTINGS
            'quality_mode': 'natural',  # 'fast', 'balanced', 'natural'
            'enable_pronunciation_fix': True,
            'enable_text_preprocessing': True,
            'optimize_for_conversation': True,  # Optimize for natural conversation
        }
    
    @classmethod
    def start_ollama_model(cls):
        """Start ollama with configured model"""
        model = cls.OLLAMA_MODEL
        print(f"Starting Ollama with model: {model}")
        
        try:
            # Check if ollama is running
            result = subprocess.run(['ollama', 'ps'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Check if model is already loaded
                if model in result.stdout:
                    print(f"Model {model} is already running")
                    return True
                else:
                    print(f"Loading model {model}...")
            else:
                print("Starting Ollama service...")
            
            # Run ollama with model
            cmd = ['ollama', 'run', model]
            process = subprocess.Popen(cmd, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            
            # Wait for model loading
            print("Waiting for model to load...")
            time.sleep(3)
            
            # Check if process is still running (good sign)
            if process.poll() is None:
                print(f"Model {model} loaded successfully!")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"Error starting model: {stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("Ollama startup timeout, but may still be loading...")
            return True
        except FileNotFoundError:
            print("Ollama not found. Install first: https://ollama.ai/")
            return False
        except Exception as e:
            print(f"Error starting Ollama: {e}")
            return False
