import whisper
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav

def record_audio(duration=5, fs=16000, filename="input.wav"):
    print("Merekam suara...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    wav.write(filename, fs, (audio * 32767).astype(np.int16))
    return filename

def transcribe_audio():
    file = record_audio()
    model = whisper.load_model("base")
    result = model.transcribe(file, language="id")
    return result["text"]

def transcribe_audio_file(file_path):
    """Transcribe audio from uploaded file"""
    try:
        model = whisper.load_model("base")
        result = model.transcribe(file_path, language="id")
        return result["text"]
    except Exception as e:
        print(f"Error transcribing audio file: {e}")
        return None
