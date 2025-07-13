# 🤖 Zorglub AI - Voice Assistant CLI

Aplikasi CLI Voice Assistant dengan Clean Architecture yang menggunakan Ollama untuk AI, Whisper untuk Speech-to-Text, dan gTTS untuk Text-to-Speech.

## 🏗️ Clean Architecture

Project ini menggunakan Clean Architecture dengan separation of concerns yang jelas:

```
zorglub-ai/
├── app.py                    # � Main entry point
├── core/                     # 🧠 Business Logic Layer
│   ├── interfaces/           # 📋 Contracts/Abstractions
│   │   ├── ai_service.py
│   │   ├── speech_input.py
│   │   └── speech_output.py
│   └── use_cases/           # 🎯 Application Business Rules
│       └── voice_assistant.py
├── infrastructure/          # 🔌 External Concerns
│   ├── dependency_injection.py  # 🏭 DI Container
│   ├── ollama_client.py     # 🤖 AI Integration
│   ├── stt_whisper.py       # 🎤 Speech-to-Text
│   └── tts_gtts.py          # 🔊 Text-to-Speech
└── shared/                  # ⚙️ Cross-cutting Concerns
    └── config.py            # 📝 Configuration
```

## �🚀 Features

- ✅ **Voice Input**: Record suara untuk input ke AI
- ✅ **Voice Response**: AI merespons dengan suara Indonesia  
- ✅ **Text Input**: Alternative text input mode
- ✅ **WSL Compatible**: Bekerja di Windows Subsystem for Linux
- ✅ **Clean Architecture**: Modular, testable, maintainable
- ✅ **Dependency Injection**: Loose coupling antar components
- ✅ **Configurable**: Environment-based configuration

## 📋 Requirements

- Python 3.8+
- Ollama server running di localhost:11434
- Model AI (mistral atau deepseek-r1) sudah ter-download di Ollama
- Audio support (mpv, pulseaudio untuk WSL)

## 🛠️ Installation

1. **Clone dan setup environment:**
```bash
cd zorglub-ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Install audio packages (untuk WSL):**
```bash
sudo apt install -y pulseaudio mpv alsa-utils
```

3. **Setup Ollama dan download model:**
```bash
# Install Ollama jika belum ada
curl -fsSL https://ollama.ai/install.sh | sh

# Download model
ollama pull mistral
# atau
ollama pull deepseek-r1
```

## 🎯 Usage

### Command Line Options

```bash
# Interactive mode (default)
python app.py

# Single voice interaction
python app.py --single

# Text chat mode
python app.py --text

# Voice chat mode  
python app.py --voice

# Check dependencies
python app.py --check

# Show help
python app.py --help
```

### Interactive Menu

Ketika menjalankan `python app.py`, Anda akan melihat menu:

```
� Interactive Mode
Choose your interaction style:
1. Single Voice (one-shot)
2. Text Chat (continuous)
3. Voice Chat (continuous)
4. Exit
```

## ⚙️ Configuration

Edit environment variables atau langsung di `shared/config.py`:

```python
# Ollama Configuration
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "mistral"  # atau "deepseek-r1"
OLLAMA_TIMEOUT = 60

# Speech Configuration  
TTS_LANGUAGE = "id"  # Bahasa Indonesia
STT_LANGUAGE = "id" 
WHISPER_MODEL = "base"

# Audio Configuration
RECORDING_DURATION = 5  # detik
SAMPLE_RATE = 16000
AUDIO_PLAYER = "mpv"
```

## 🏗️ Architecture Benefits

### 1. **Separation of Concerns**
- **Core**: Business logic, tidak tahu tentang implementation details
- **Infrastructure**: External services (Ollama, Whisper, gTTS)
- **App**: Entry point, orchestration

### 2. **Dependency Inversion**
- High-level modules tidak depend on low-level modules
- Semua depend on abstractions (interfaces)

### 3. **Testability**
- Easy mocking dengan dependency injection
- Unit tests untuk setiap layer

### 4. **Maintainability**  
- Changes di satu layer tidak affect layer lain
- Easy to add new features atau ganti implementation

## 🐛 Troubleshooting

### Audio tidak bekerja di WSL:
```bash
pactl list short sinks
pulseaudio --start
mpv /path/to/test.mp3
```

### Ollama timeout:
```bash
curl http://localhost:11434/api/version
systemctl restart ollama
```

### Import errors:
```bash
# Make sure you're in the project root
cd zorglub-ai
python app.py
```

## 📝 Dependencies

Core dependencies di `requirements.txt`:
- **whisper**: Speech-to-Text
- **sounddevice**: Audio recording
- **gtts**: Google Text-to-Speech  
- **requests**: HTTP client untuk Ollama

## 🌟 Tips

1. **Development**: Use `python app.py --check` untuk verify setup
2. **Performance**: Model `base` whisper balance antara speed & accuracy
3. **Voice Quality**: Bicara jelas, hindari background noise
4. **WSL Audio**: Pastikan Windows audio driver up to date

---

**Enjoy your Clean Architecture Voice AI Assistant! 🎉**
