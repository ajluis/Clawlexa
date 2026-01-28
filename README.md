<div align="center">

# 🦞 Clawlexa

**Personal voice assistant powered by Clawdbot on Raspberry Pi**

*"Hey Clawlexa!" → Listen → Think → Speak*

[![License: MIT](https://img.shields.io/badge/License-MIT-red.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-5-green.svg)](https://www.raspberrypi.com/)

</div>

---

## What is Clawlexa?

Clawlexa is an open-source, privacy-conscious voice assistant that runs on a Raspberry Pi 5 and uses [Clawdbot](https://github.com/clawdbot) as its brain. Think Alexa, but with Claude's intelligence and your own infrastructure.

## Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Wake Word  │───▶│     STT     │───▶│    Brain    │───▶│     TTS     │───▶│   Speaker   │
│ (Porcupine) │    │(Whisper API)│    │ (Clawdbot)  │    │   (Piper)   │    │ (Bluetooth) │
│   LOCAL     │    │    CLOUD    │    │   CLOUD     │    │   LOCAL     │    │   LOCAL     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

**How it works:**

1. 🎤 **Wake Word** — Porcupine listens locally for "picovoice" (customizable)
2. 🗣️ **Speech-to-Text** — OpenAI Whisper API transcribes your speech
3. 🧠 **Brain** — Clawdbot Gateway processes your request with Claude
4. 🔊 **Text-to-Speech** — Piper TTS generates audio locally
5. 📻 **Speaker** — Audio plays through your Bluetooth speaker

## Quick Start

### Prerequisites

- Raspberry Pi 5 (2GB+ RAM) with Raspberry Pi OS (64-bit)
- USB microphone or Bluetooth speaker with built-in mic
- Internet connection
- A running [Clawdbot](https://github.com/clawdbot) Gateway instance

### Install

```bash
git clone https://github.com/ajluis/Clawlexa.git
cd Clawlexa
chmod +x setup.sh
./setup.sh
```

### Configure

```bash
cp config.yaml.example config.yaml
nano config.yaml
# Set your Clawdbot gateway URL and token
# Set your OpenAI API key (for Whisper)
```

### Run

```bash
source venv/bin/activate
python src/main.py
```

### Run as a Service

```bash
sudo cp systemd/clawlexa.service /etc/systemd/system/
sudo systemctl enable clawlexa
sudo systemctl start clawlexa
```

## Hardware

| Component | Recommended | Minimum |
|-----------|-------------|---------|
| Board | Raspberry Pi 5 (4GB) | Raspberry Pi 5 (2GB) |
| Storage | 64GB microSD | 32GB microSD |
| Power | 27W USB-C PSU | 15W USB-C PSU |
| Audio In | ReSpeaker USB Mic Array | Any USB mic |
| Audio Out | Bluetooth speaker | 3.5mm speaker |

See [docs/HARDWARE.md](docs/HARDWARE.md) for full details.

## Documentation

- 📖 [Full Setup Guide](docs/SETUP.md)
- 🔧 [Hardware Requirements](docs/HARDWARE.md)
- 🐛 [Troubleshooting](docs/TROUBLESHOOTING.md)

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for Whisper STT | Yes |
| `CLAWDBOT_GATEWAY_TOKEN` | Clawdbot Gateway auth token | Yes |
| `PORCUPINE_ACCESS_KEY` | Picovoice access key (free tier) | Yes |

## Project Structure

```
clawlexa/
├── src/
│   ├── main.py          # Main orchestrator loop
│   ├── wake_word.py     # Porcupine wake word detection
│   ├── audio.py         # Mic capture + speaker output
│   ├── stt.py           # Speech-to-text (Whisper API)
│   ├── brain.py         # Clawdbot Gateway communication
│   ├── tts.py           # Text-to-speech (Piper)
│   └── vad.py           # Voice activity detection (Silero)
├── voices/              # Piper voice models
├── scripts/             # Installation helpers
├── systemd/             # systemd service file
├── docs/                # Documentation
├── config.yaml          # Configuration
├── setup.sh             # One-line setup
└── requirements.txt     # Python dependencies
```

## License

MIT © [ajluis](https://github.com/ajluis)

---

<div align="center">
<i>Built with 🦞 and Claude</i>
</div>
