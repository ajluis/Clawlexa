# Clawlexa Setup Guide

Complete step-by-step guide to set up Clawlexa on your Raspberry Pi.

## 1. Prepare Your Raspberry Pi

### Flash the OS

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Choose **Raspberry Pi OS (64-bit)** — the Lite version works fine
3. Click the gear icon to pre-configure:
   - Set hostname: `clawlexa`
   - Enable SSH
   - Set username/password
   - Configure WiFi
4. Flash to your microSD card (32GB+)
5. Insert the card and boot the Pi

### Connect via SSH

```bash
ssh pi@clawlexa.local
```

### Update the System

```bash
sudo apt update && sudo apt upgrade -y
```

## 2. Hardware Setup

### USB Microphone / Speaker

Plug in your USB mic or speaker-with-mic. Verify it's detected:

```bash
arecord -l   # List recording devices
aplay -l     # List playback devices
```

### Bluetooth Speaker

If using Bluetooth:

```bash
chmod +x scripts/bluetooth_setup.sh
./scripts/bluetooth_setup.sh
```

Or manually:

```bash
bluetoothctl
> power on
> agent on
> scan on
# Wait for your speaker to appear
> pair XX:XX:XX:XX:XX:XX
> trust XX:XX:XX:XX:XX:XX
> connect XX:XX:XX:XX:XX:XX
> exit
```

## 3. Install Clawlexa

```bash
git clone https://github.com/ajluis/Clawlexa.git
cd Clawlexa
chmod +x setup.sh scripts/*.sh
./setup.sh
```

This installs all system dependencies, creates a Python virtual environment,
downloads the default Piper voice model, and optionally sets up the systemd service.

## 4. Get Your API Keys

You need three keys:

### Picovoice (Wake Word) — Free

1. Go to [console.picovoice.ai](https://console.picovoice.ai/)
2. Sign up (free tier: 3 wake word detections/second)
3. Copy your **Access Key**

### OpenAI (Whisper STT) — Paid

1. Go to [platform.openai.com](https://platform.openai.com/)
2. Create an API key
3. Whisper costs ~$0.006/minute of audio

### Clawdbot Gateway — Self-hosted

1. Set up a [Clawdbot](https://github.com/clawdbot) Gateway instance
2. Get your gateway URL and authentication token

## 5. Configure

Edit `.env` with your API keys:

```bash
nano .env
```

```env
PORCUPINE_ACCESS_KEY=your-picovoice-key
OPENAI_API_KEY=sk-your-openai-key
CLAWDBOT_GATEWAY_TOKEN=your-gateway-token
```

Edit `config.yaml` for your setup:

```bash
nano config.yaml
```

Key settings:
- `brain.gateway_url` — Your Clawdbot Gateway URL
- `audio.input_device` / `audio.output_device` — Device indices if not using defaults
- `wake_word.keyword` — Change wake word (see `scripts/install_porcupine.sh` for options)
- `tts.voice` — Change the voice model

## 6. Test Each Component

### Test Microphone

```bash
source venv/bin/activate
python -c "
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    d = p.get_device_info_by_index(i)
    if d['maxInputChannels'] > 0:
        print(f'[{i}] {d[\"name\"]}')
p.terminate()
"
```

### Test Speaker

```bash
speaker-test -t wav -c 2 -l 1
```

### Test Wake Word

```bash
python -c "
import pvporcupine, os, struct, pyaudio

key = os.getenv('PORCUPINE_ACCESS_KEY')
porcupine = pvporcupine.create(access_key=key, keywords=['picovoice'])
pa = pyaudio.PyAudio()
stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True,
                 frames_per_buffer=porcupine.frame_length)
print('Say \"picovoice\"...')
while True:
    data = stream.read(porcupine.frame_length)
    pcm = struct.unpack_from(f'{porcupine.frame_length}h', data)
    if porcupine.process(pcm) >= 0:
        print('Detected!')
        break
"
```

### Test TTS

```bash
echo "Hello, I am Clawlexa!" | piper --model voices/en_US-lessac-medium.onnx --output_file test.wav
aplay test.wav
```

## 7. Run Clawlexa

### Manual Run

```bash
source venv/bin/activate
python src/main.py
```

### Run as a Service

```bash
sudo systemctl start clawlexa
sudo systemctl status clawlexa

# View logs
journalctl -u clawlexa -f
```

### Enable Auto-Start

```bash
sudo systemctl enable clawlexa
```

## 8. Verify Everything Works

1. Wait for "Listening for wake word..." in the logs
2. Say "picovoice" (or your configured wake word)
3. You should hear a chime
4. Say your question
5. Wait for the response

If anything doesn't work, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
