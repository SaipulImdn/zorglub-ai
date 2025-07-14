#include <cstddef>
extern "C" {
    void apply_gain(short* samples, size_t length, float gain) {
        for (size_t i = 0; i < length; ++i) {
            int sample = static_cast<int>(samples[i] * gain);
            if (sample > 32767) sample = 32767;
            if (sample < -32768) sample = -32768;
            samples[i] = static_cast<short>(sample);
        }
    }
}
