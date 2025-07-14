import os
import subprocess
import time

class Config:
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1") 
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))
    
    TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "id")
    STT_LANGUAGE = os.getenv("STT_LANGUAGE", "id")
    
    TTS_ENGINE = os.getenv("TTS_ENGINE", "edge")
    TTS_VOICE = os.getenv("TTS_VOICE", "id-ID-ArdiNeural")
    TTS_RATE = os.getenv("TTS_RATE", "-10%")
    TTS_VOLUME = os.getenv("TTS_VOLUME", "+10%")
    TTS_PITCH = os.getenv("TTS_PITCH", "-2Hz")
    
    RECORDING_DURATION = int(os.getenv("RECORDING_DURATION", "5"))
    SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
    
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
    
    AUDIO_PLAYER = os.getenv("AUDIO_PLAYER", "mpv")
    
    @classmethod
    def get_recording_settings(cls):
        return {
            'duration': cls.RECORDING_DURATION,
            'sample_rate': cls.SAMPLE_RATE
        }
    
    @classmethod
    def get_ollama_settings(cls):
        return {
            'url': cls.OLLAMA_URL,
            'model': cls.OLLAMA_MODEL,
            'timeout': cls.OLLAMA_TIMEOUT
        }
    
    @classmethod
    def get_speech_settings(cls):
        return {
            'tts_language': cls.TTS_LANGUAGE,
            'stt_language': cls.STT_LANGUAGE,
            'whisper_model': cls.WHISPER_MODEL,
            'tts_engine': cls.TTS_ENGINE,
            'tts_voice': cls.TTS_VOICE,
            'tts_rate': '+5%',
            'tts_volume': '+15%',
            'tts_pitch': '+0Hz',
            'edge_voice': cls.TTS_VOICE,
            'piper_model': 'id_ID-fajri-medium',
            'max_segment_length': 200,
            'max_workers': 4,
            'enable_parallel_processing': True,
            'enable_natural_pauses': True,
            'pause_between_segments': 0.3,
            'enable_audio_streaming': False,
            'fast_cleanup': True,
            'audio_buffer_size': 0.5,
            'audio_normalization': True,
            'audio_timeout': 30,
            'use_fallback_player': True,
            'natural_speed': True,
            'add_breathing_pauses': True,
            'emotional_tone': 'conversational',
            'prosody_enhancement': True,
            'fallback_engine': 'gtts',
            'fallback_on_error': True,
            'max_retries': 2,
            'timeout_per_segment': 25,
            'quality_mode': 'natural',
            'enable_pronunciation_fix': True,
            'enable_text_preprocessing': True,
            'optimize_for_conversation': True,
        }
    
    @classmethod
    def start_ollama_model(cls):
        model = cls.OLLAMA_MODEL
        print(f"Starting Ollama with model: {model}")
        
        try:
            result = subprocess.run(['ollama', 'ps'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                if model in result.stdout:
                    print(f"Model {model} is already running")
                    return True
                else:
                    print(f"Loading model {model}...")
            else:
                print("Starting Ollama service...")
            
            cmd = ['ollama', 'run', model]
            process = subprocess.Popen(cmd, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            
            print("Waiting for model to load...")
            time.sleep(3)
            
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
