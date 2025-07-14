import ctypes
import numpy as np
import os

LIB_PATH = os.path.join(os.path.dirname(__file__), 'libaudiofilter.so')

class AudioFilter:
    def __init__(self, lib_path=LIB_PATH):
        self.lib = ctypes.CDLL(lib_path)
        self.lib.apply_gain.argtypes = [ctypes.POINTER(ctypes.c_short), ctypes.c_size_t, ctypes.c_float]
        self.lib.apply_gain.restype = None

    def apply_gain(self, samples: np.ndarray, gain: float) -> np.ndarray:
        assert samples.dtype == np.int16, "Samples must be int16 (PCM)"
        arr = samples.copy()
        self.lib.apply_gain(arr.ctypes.data_as(ctypes.POINTER(ctypes.c_short)), arr.size, ctypes.c_float(gain))
        return arr

if __name__ == "__main__":
    import wave
    with wave.open("input.wav", "rb") as wf:
        frames = wf.readframes(wf.getnframes())
        samples = np.frombuffer(frames, dtype=np.int16)
    filtered = AudioFilter().apply_gain(samples, 2.0)
    with wave.open("output.wav", "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(filtered.tobytes())
