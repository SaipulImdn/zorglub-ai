# Audio Filter Module

This folder contains the C++ and Python code for the audio filter used in the Zorglub AI project.

## Files
- `audio_filter.cpp`: C++ implementation of a simple gain filter for PCM audio.
- `audio_filter.py`: Python ctypes wrapper for the filter, providing an easy interface for applying gain to audio samples.
- `libaudiofilter.so`: Compiled shared library (build instructions below).

## Build Instructions
To build the shared library:

```bash
g++ -O3 -Wall -shared -std=c++11 -fPIC audio_filter.cpp -o libaudiofilter.so
```

Place the resulting `libaudiofilter.so` in this folder. The Python wrapper will load it automatically.

## Usage
The filter is automatically applied to WAV audio output in the TTS pipeline. You can also use it directly:

```python
from audio_filter.audio_filter import AudioFilter
import numpy as np
samples = np.array([...], dtype=np.int16)
filtered = AudioFilter().apply_gain(samples, 1.5)
```
