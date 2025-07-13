import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os
from shared.config import Config

def record_audio(filename="input.wav"):
    """Record audio dari microphone"""
    settings = Config.get_recording_settings()
    duration = settings['duration']
    fs = settings['sample_rate']
    
    print(f"Merekam suara selama {duration} detik...")
    try:
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
        wav.write(filename, fs, (audio * 32767).astype(np.int16))
        print("Recording selesai")
        return filename
    except Exception as e:
        print(f"Error recording: {e}")
        return None

def transcribe_audio():
    """Convert speech to text menggunakan Whisper"""
    try:
        speech_settings = Config.get_speech_settings()
        print(f"Loading Whisper model: {speech_settings['whisper_model']}...")
        
        model = whisper.load_model(speech_settings['whisper_model'])
        
        file = record_audio()
        if not file:
            return None
            
        print("Transcribing audio...")
        result = model.transcribe(file, language=speech_settings['stt_language'])
        
        # Cleanup
        if os.path.exists(file):
            os.remove(file)
            
        return result["text"]
    except Exception as e:
        print(f"Error transcribing: {e}")
        return None
