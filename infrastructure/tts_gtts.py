from gtts import gTTS
import simpleaudio as sa
import os
import tempfile
import io

TEMP_MP3_FILE = "temp.mp3"

def speak_text(text: str):
    tts = gTTS(text, lang='id')
    filename = "output.wav"
    tts.save(TEMP_MP3_FILE)

    # convert mp3 to wav (required by simpleaudio)
    from pydub import AudioSegment
    sound = AudioSegment.from_mp3(TEMP_MP3_FILE)
    sound.export(filename, format="wav")

    # play audio
    wave_obj = sa.WaveObject.from_wave_file(filename)
    play_obj = wave_obj.play()
    play_obj.wait_done()

    os.remove(TEMP_MP3_FILE)
    os.remove(filename)

def generate_audio_file(text: str):
    """Generate audio file for web API"""
    try:
        tts = gTTS(text, lang='id')
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        tts.save(temp_file.name)
        
        return temp_file.name
    except Exception as e:
        print(f"Error generating audio file: {e}")
        return None
