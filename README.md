# Zorglub AI - Voice Assistant CLI

A professional CLI-based voice assistant application built with Clean Architecture principles, integrating Ollama for AI responses, Whisper for speech-to-text, and advanced TTS engines for text-to-speech.

## Architecture Overview

This project implements Clean Architecture with clear separation of concerns:

```
zorglub-ai/
├── app.py                    # Main entry point
├── core/                     # Business Logic Layer
│   ├── interfaces/           # Contracts and Abstractions
│   │   ├── ai_service.py
│   │   ├── speech_input.py
│   │   └── speech_output.py
│   ├── use_cases/           # Application Business Rules
│   │   └── voice_assistant.py
│   └── conversation_manager.py  # Conversation Context Management
├── infrastructure/          # External Dependencies
│   ├── dependency_injection.py  # Dependency Injection Container
│   ├── ollama_client.py     # AI Model Integration
│   ├── stt_whisper.py       # Speech-to-Text Implementation
│   ├── tts_gtts.py          # Google TTS Implementation
│   └── tts_human.py         # Advanced Human-like TTS
├── shared/                  # Cross-cutting Concerns
│   └── config.py            # Configuration Management
├── Dockerfile               # Docker build file
└── .github/
    └── workflows/
        └── docker-build.yml # GitHub Actions CI/CD workflow
```

## Key Features

- **Voice Input Processing**: Advanced speech recognition using OpenAI Whisper
- **Natural AI Responses**: Context-aware conversations with memory management
- **Human-like Voice Output**: Multiple TTS engines including Microsoft Edge TTS
- **Conversation Context**: Maintains conversation history for natural interactions
- **Cross-platform Compatibility**: Works on Linux, WSL, and other Unix-like systems
- **Clean Architecture**: Modular design with dependency injection
- **Configurable**: Environment-based configuration system
- **Auto-start Integration**: Automatic Ollama model initialization

    steps:


python app.py --single

# Zorglub AI - Voice Assistant CLI

A professional CLI-based voice assistant application built with Clean Architecture principles, integrating Ollama for AI responses, Whisper for speech-to-text, and advanced TTS engines for text-to-speech.

## Architecture Overview

This project implements Clean Architecture with clear separation of concerns:

```
zorglub-ai/
├── app.py                    # Main entry point
├── core/                     # Business Logic Layer
│   ├── interfaces/           # Contracts and Abstractions
│   │   ├── ai_service.py
│   │   ├── speech_input.py
│   │   └── speech_output.py
│   ├── use_cases/           # Application Business Rules
│   │   └── voice_assistant.py
│   └── conversation_manager.py  # Conversation Context Management
├── infrastructure/          # External Dependencies
│   ├── dependency_injection.py  # Dependency Injection Container
│   ├── ollama_client.py     # AI Model Integration
│   ├── stt_whisper.py       # Speech-to-Text Implementation
│   ├── tts_gtts.py          # Google TTS Implementation
│   └── tts_human.py         # Advanced Human-like TTS
├── shared/                  # Cross-cutting Concerns
│   └── config.py            # Configuration Management
├── Dockerfile               # Docker build file
└── .github/
    └── workflows/
        └── docker-build.yml # GitHub Actions CI/CD workflow
```

## Key Features

- **Voice Input Processing**: Advanced speech recognition using OpenAI Whisper
- **Natural AI Responses**: Context-aware conversations with memory management
- **Human-like Voice Output**: Multiple TTS engines including Microsoft Edge TTS
- **Conversation Context**: Maintains conversation history for natural interactions
- **Cross-platform Compatibility**: Works on Linux, WSL, and other Unix-like systems
- **Clean Architecture**: Modular design with dependency injection
- **Configurable**: Environment-based configuration system
- **Auto-start Integration**: Automatic Ollama model initialization
- **Dockerized & CI/CD Ready**: Build and deploy with Docker and GitHub Actions

## System Requirements

- Python 3.8 or higher
- Ollama server accessible at localhost:11434
- AI model (mistral, deepseek-r1, or compatible) installed in Ollama
- Audio system support (ALSA, PulseAudio, or equivalent)
- Media player (mpv recommended)
- Docker (for containerized deployment)

## Installation

### 1. Environment Setup (Manual)

```bash
# Clone repository
./run_with_model.sh mistral --voice
cd zorglub-ai

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. System Dependencies

```bash
# For Ubuntu/Debian systems
sudo apt update
sudo apt install -y pulseaudio mpv alsa-utils

# For audio support in WSL
sudo apt install -y pulseaudio-module-wsl
```

### 3. Ollama Setup

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download AI model
ollama pull mistral
# Alternative models
ollama pull deepseek-r1
ollama pull llama3.2
```

### 4. Enhanced TTS Setup (Optional)

```bash
# For Microsoft Edge TTS (highest quality)
./run_with_model.sh deepseek-r1 --text

# For Piper TTS (neural, local)
# Download from: https://github.com/rhasspy/piper

# For Festival TTS (classic)
```
```

### 5. Docker Build & Run

```bash
# Build Docker image


# Run the container
## Configuration
    -e OLLAMA_URL="http://host.docker.internal:11434/api/chat" \
    -e OLLAMA_MODEL="mistral" \
    zorglub-ai
```

> **Note:** Make sure Ollama and audio dependencies are available on the host or container as needed.

## CI/CD with GitHub Actions & Docker

This project is ready for automated CI/CD using Docker and GitHub Actions.

### 1. Workflow Structure

- Workflow file: `.github/workflows/docker-build.yml`
- Builds image on every push/pull request to the `main` branch
- Pushes image to DockerHub (requires secrets)

### 2. Setup DockerHub Secrets

1. Log in to GitHub and open your repository.
2. Go to **Settings** → **Secrets and variables** → **Actions**.
3. Add secrets:
   - `DOCKERHUB_USERNAME` (your DockerHub username)
   - `DOCKERHUB_TOKEN` (your DockerHub access token, get it from DockerHub > Account Settings > Security > New Access Token)

### 3. Example Workflow (`.github/workflows/docker-build.yml`)

```yaml
name: Build and Push Docker Image


  push:
    branches: [main]
  pull_request:
    branches: [main]

### Environment Variables
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to DockerHub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ secrets.DOCKERHUB_USERNAME }}/zorglub-ai:latest
```

### 4. Create DockerHub Access Token

- Log in to DockerHub
- Go to Account Settings → Security → New Access Token
- Choose permission: **Read, Write** (or **Delete** if needed)
- Copy the token and save it as `DOCKERHUB_TOKEN` in GitHub secrets

## Usage

```bash
# Ollama Configuration
export OLLAMA_URL="http://localhost:11434/api/chat"
export OLLAMA_MODEL="mistral"
export OLLAMA_TIMEOUT="60"

# Speech Configuration
export TTS_LANGUAGE="id"
export STT_LANGUAGE="id"
export WHISPER_MODEL="base"

# Enhanced TTS Configuration
export TTS_ENGINE="edge"
export TTS_VOICE="id-ID-ArdiNeural"
export TTS_RATE="+0%"
export TTS_VOLUME="+0%"
export TTS_PITCH="+0Hz"

# Audio Configuration
export RECORDING_DURATION="5"
export SAMPLE_RATE="16000"
export AUDIO_PLAYER="mpv"
```

### Configuration File

Alternatively, modify `shared/config.py` directly:

```python
class Config:
    OLLAMA_URL = "http://localhost:11434/api/chat"
    OLLAMA_MODEL = "mistral"
    TTS_ENGINE = "edge"  # edge, piper, festival, gtts
    TTS_VOICE = "id-ID-ArdiNeural"
    WHISPER_MODEL = "base"
```

## Advanced Features

### Conversation Context Management

The system maintains conversation history and context:

- **Memory Management**: Stores up to 15 previous messages
- **Context Detection**: Automatically detects conversation topics
- **Follow-up Recognition**: Identifies and handles follow-up questions
- **Natural Flow**: Maintains conversation continuity

### Available TTS Engines

1. **Microsoft Edge TTS** (Recommended)
   - Highest quality, most human-like voice
   - Supports Indonesian voices (id-ID-ArdiNeural, id-ID-GadisNeural)
   - Requires: `pip install edge-tts`

2. **Piper Neural TTS**
   - Local neural TTS with natural voice
   - Fast processing, good quality
   - Requires: Manual installation from GitHub

3. **Festival TTS**
   - Classic TTS engine
   - Reliable but robotic voice
   - Requires: `sudo apt install festival`

4. **Google TTS**
   - Fallback option
   - Good quality, cloud-based
   - Already included in requirements

### Conversation Commands

In text chat mode:
- `/help` - Display available commands
- `/clear` - Clear conversation history
- `/status` - Show conversation status
- `/quit` - Exit current mode

## Architecture Benefits

### Clean Architecture Principles

1. **Dependency Inversion**: High-level modules independent of low-level implementations
2. **Separation of Concerns**: Each layer has distinct responsibilities
3. **Testability**: Easy unit testing with dependency injection
4. **Maintainability**: Changes isolated to specific layers
5. **Extensibility**: Easy to add new features or replace implementations

### Layer Responsibilities

- **Core Layer**: Business logic and use cases
- **Infrastructure Layer**: External service integrations
- **Shared Layer**: Cross-cutting concerns and configuration
- **Application Layer**: Entry point and orchestration

## Testing

### Dependency Validation

```bash
# Check system dependencies
python app.py --check

# Test TTS engines
python test_human_tts.py

# Test conversation logic
python test_conversation.py
```

### Development Tools

```bash
# Clean architecture validation
python test_clean.py

# Conversation flow demonstration
python demo_conversation.py
```

## Troubleshooting

### Audio Issues

```bash
# Check audio devices
pactl list short sinks

# Restart audio service
pulseaudio --kill
pulseaudio --start

# Test audio output
mpv /path/to/test.mp3
```

### Ollama Connectivity

```bash
# Check Ollama status
curl http://localhost:11434/api/version

# List available models
ollama list

# Restart Ollama service
sudo systemctl restart ollama
```

### Common Issues

1. **ImportError**: Ensure virtual environment is activated
2. **Audio not working**: Check PulseAudio configuration
3. **Ollama timeout**: Increase timeout in configuration
4. **Whisper errors**: Verify model installation
5. **TTS failures**: Check selected engine availability

## Development

### Adding New Features

1. **New TTS Engine**: Implement in `infrastructure/tts_human.py`
2. **New AI Provider**: Create new client in `infrastructure/`
3. **New Input Method**: Extend `core/interfaces/speech_input.py`
4. **New Use Case**: Add to `core/use_cases/`

### Contributing

1. Follow Clean Architecture principles
2. Maintain dependency injection patterns
3. Add appropriate tests
4. Update documentation
5. Ensure cross-platform compatibility

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check troubleshooting section
- Review system requirements
- Validate configuration settings

---

**Professional Voice AI