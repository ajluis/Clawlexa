# Troubleshooting

## Audio Issues

### No audio input / microphone not detected

```bash
# List all audio input devices
arecord -l

# Test recording (Ctrl+C to stop)
arecord -d 5 -f S16_LE -r 16000 -c 1 test.wav
aplay test.wav
```

**Fixes:**
- Ensure your mic is plugged in before booting
- Check `config.yaml` → `audio.input_device` matches the device index
- For USB mics: try a different USB port
- Check PulseAudio: `pactl list sources short`

### No audio output / speaker not working

```bash
# List output devices
aplay -l

# Test speaker
speaker-test -t wav -c 2 -l 1

# Check PulseAudio sinks
pactl list sinks short
```

**Fixes:**
- Set default sink: `pactl set-default-sink <sink_name>`
- Check volume: `alsamixer` or `pactl set-sink-volume @DEFAULT_SINK@ 80%`
- For HDMI: `raspi-config` → Audio → Force HDMI

### Audio crackling or stuttering

- **Under-voltage:** Use the official 27W USB-C power supply
- **PulseAudio buffer:** Add to `/etc/pulse/daemon.conf`:
  ```
  default-fragment-size-msec = 25
  default-fragments = 4
  ```
- Restart PulseAudio: `pulseaudio -k && pulseaudio --start`

## Bluetooth Issues

### Speaker won't pair

```bash
# Reset Bluetooth
sudo systemctl restart bluetooth

# Remove and re-pair
bluetoothctl
> remove XX:XX:XX:XX:XX:XX
> scan on
> pair XX:XX:XX:XX:XX:XX
> trust XX:XX:XX:XX:XX:XX
> connect XX:XX:XX:XX:XX:XX
```

### Bluetooth connected but no audio

```bash
# Check if A2DP sink is available
pactl list sinks short | grep bluez

# If not, load the Bluetooth module
pactl load-module module-bluetooth-discover

# Restart PulseAudio
pulseaudio -k && pulseaudio --start
```

### Bluetooth disconnects randomly

- Ensure speaker is charged and in range
- Disable WiFi power management (can interfere):
  ```bash
  sudo iwconfig wlan0 power off
  ```
- Add to `/etc/bluetooth/main.conf`:
  ```
  [Policy]
  AutoEnable=true
  ```

## Wake Word Issues

### Wake word never triggers

- **Sensitivity:** Increase `wake_word.sensitivity` in config.yaml (try 0.7-0.8)
- **Microphone:** Test that the mic is recording: `arecord -d 3 test.wav && aplay test.wav`
- **Access key:** Verify your Picovoice access key is correct
- **Distance:** Speak clearly within 2-3 meters of the mic

### Too many false triggers

- **Sensitivity:** Decrease `wake_word.sensitivity` (try 0.3-0.4)
- **Background noise:** Move the mic away from speakers, fans, etc.
- **Try a different keyword:** Some keywords are more distinct than others

### "Porcupine access key invalid" error

1. Go to [console.picovoice.ai](https://console.picovoice.ai/)
2. Check that your key is active and not expired
3. Free tier has rate limits — ensure you're not exceeding them

## Network / API Issues

### "Whisper API error" or STT failures

- **Check internet:** `ping -c 3 api.openai.com`
- **API key:** Verify `OPENAI_API_KEY` in `.env`
- **Billing:** Ensure your OpenAI account has credits
- **Timeout:** Increase timeout or check network latency

### "Brain request timed out" / no Clawdbot response

- **Gateway running?** Check your Clawdbot Gateway is accessible:
  ```bash
  curl -s http://your-gateway:3000/health
  ```
- **Token:** Verify `CLAWDBOT_GATEWAY_TOKEN` in `.env`
- **URL:** Ensure `brain.gateway_url` in config.yaml is correct
- **Firewall:** Ensure the Pi can reach the gateway port

### Slow responses

- Check network latency: `ping your-gateway-server`
- Use Ethernet instead of WiFi for lower latency
- Gateway response time depends on Claude's processing

## Service Issues

### systemd service won't start

```bash
# Check status and logs
sudo systemctl status clawlexa
journalctl -u clawlexa -n 50

# Common fix: ensure paths are correct in the service file
cat /etc/systemd/system/clawlexa.service
```

### Service starts but immediately stops

- Usually a missing environment variable — check `journalctl -u clawlexa`
- Ensure `.env` file exists and has all required keys
- Try running manually first: `source venv/bin/activate && python src/main.py`

## TTS Issues

### "Piper TTS not found"

```bash
# Install via pip
source venv/bin/activate
pip install piper-tts

# Or install binary
./scripts/install_piper.sh
```

### "Voice model not found"

```bash
# Download the default voice
cd voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

### TTS audio sounds robotic

- Try a higher quality voice: change `tts.voice` to `en_US-lessac-high`
- Adjust speed: `tts.speed` in config.yaml

## General

### High CPU usage

- Porcupine is designed for low CPU — if CPU is high, check:
  - `htop` to identify the culprit
  - Silero VAD model loading (one-time, ~2s)
  - PyTorch may use significant memory on 2GB Pi

### Out of memory

- The 2GB Pi is tight with PyTorch loaded. Options:
  - Use a swap file: `sudo dphys-swapfile swapon`
  - Increase swap: edit `/etc/dphys-swapfile`, set `CONF_SWAPSIZE=1024`
  - Upgrade to 4GB Pi 5

### Permission errors

```bash
# Add user to audio and bluetooth groups
sudo usermod -a -G audio,bluetooth,pulse-access $USER
# Log out and back in for changes to take effect
```

## Getting Help

1. Check logs: `journalctl -u clawlexa -f` or run with `logging.level: DEBUG`
2. Open an issue: [github.com/ajluis/Clawlexa/issues](https://github.com/ajluis/Clawlexa/issues)
