"""
Configuration settings untuk Zorglub AI
Centralized configuration management
"""

import os
import subprocess
import time

class Config:
    # Ollama Configuration
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral") 
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))
    
    # Speech Configuration
    TTS_LANGUAGE = os.getenv("TTS_LANGUAGE", "id")  # Bahasa Indonesia
    STT_LANGUAGE = os.getenv("STT_LANGUAGE", "id")  # Bahasa Indonesia
    
    # Audio Configuration
    RECORDING_DURATION = int(os.getenv("RECORDING_DURATION", "5"))  # detik
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
        """Get speech processing settings"""
        return {
            'tts_language': cls.TTS_LANGUAGE,
            'stt_language': cls.STT_LANGUAGE,
            'whisper_model': cls.WHISPER_MODEL
        }
    
    @classmethod
    def start_ollama_model(cls):
        """Start ollama dengan model yang dikonfigurasi"""
        model = cls.OLLAMA_MODEL
        print(f"Starting Ollama with model: {model}")
        
        try:
            # Check if ollama is running
            result = subprocess.run(['ollama', 'ps'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Check if model is already loaded
                if model in result.stdout:
                    print(f"Model {model} sudah berjalan")
                    return True
                else:
                    print(f"Loading model {model}...")
            else:
                print("Starting Ollama service...")
            
            # Run ollama dengan model
            cmd = ['ollama', 'run', model]
            process = subprocess.Popen(cmd, 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            
            # Wait a bit untuk model loading
            print("Waiting for model to load...")
            time.sleep(3)
            
            # Check if process is still running (good sign)
            if process.poll() is None:
                print(f"Model {model} berhasil dimuat!")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"Error starting model: {stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("Ollama startup timeout, but may still be loading...")
            return True
        except FileNotFoundError:
            print("Ollama tidak ditemukan. Install dulu: https://ollama.ai/")
            return False
        except Exception as e:
            print(f"Error starting Ollama: {e}")
            return False
