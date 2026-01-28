# Hardware Requirements

## Minimum Setup

| Component | Specification | Approx. Cost |
|-----------|--------------|-------------|
| **Raspberry Pi 5** | 2GB RAM minimum | $50 |
| **Power Supply** | 27W USB-C (official recommended) | $12 |
| **microSD Card** | 32GB+ Class 10 / A2 | $10 |
| **USB Microphone** | Any USB mic or webcam with mic | $10-30 |
| **Speaker** | 3.5mm, USB, HDMI, or Bluetooth | $10-50 |

**Total minimum: ~$90-150**

## Recommended Setup

| Component | Specification | Notes |
|-----------|--------------|-------|
| **Raspberry Pi 5** | 4GB RAM | More headroom for VAD model |
| **Power Supply** | 27W USB-C (official) | Don't skimp — under-voltage causes issues |
| **microSD Card** | 64GB A2 (Samsung EVO Select) | Faster I/O |
| **Bluetooth Speaker w/ Mic** | JBL Flip, Anker Soundcore, etc. | All-in-one audio I/O |
| **Case** | Official Pi 5 case w/ fan | Keeps the Pi cool |

## Audio Options

### Option 1: Bluetooth Speaker with Built-in Mic (Recommended)

Best for a clean, wireless setup. Many portable Bluetooth speakers have built-in microphones.

**Pros:** No wires, good audio quality, portable
**Cons:** Mic quality varies, slight latency, needs charging

Setup: `./scripts/bluetooth_setup.sh`

### Option 2: USB Speakerphone

Conference speakerphones like the Jabra Speak series have excellent mics and speakers in one device.

**Pros:** Excellent mic quality, echo cancellation, plug-and-play
**Cons:** Not wireless, more expensive

### Option 3: USB Mic + 3.5mm Speaker

Separate mic and speaker. Use the Pi's 3.5mm headphone jack for output.

**Pros:** Cheap, simple, no Bluetooth issues
**Cons:** More wires, 3.5mm audio quality is mediocre

### Option 4: ReSpeaker HAT

The [ReSpeaker 2-Mics Pi HAT](https://wiki.seeedstudio.com/ReSpeaker_2_Mics_Pi_HAT/) adds a microphone array directly to the Pi.

**Pros:** Far-field voice capture, LED ring, compact
**Cons:** Requires I2S driver setup, Pi HAT form factor

## Power Considerations

- **Always use the official 27W USB-C power supply** for Pi 5
- Under-voltage causes audio glitches, USB device disconnects, and SD card corruption
- If using a powered USB hub, ensure it doesn't backfeed power to the Pi

## Network

- **WiFi:** Built-in 802.11ac on Pi 5 — sufficient for API calls
- **Ethernet:** More reliable for always-on operation
- **Bandwidth:** Minimal — only STT audio upload (~32KB/s) and API text responses

## Storage

- Voice model: ~65MB (en_US-lessac-medium)
- Silero VAD model: ~4MB
- Porcupine: ~5MB
- Python venv: ~500MB (mostly PyTorch)
- **Total: ~1GB** — a 32GB card is plenty

## Optional Extras

| Component | Purpose |
|-----------|---------|
| LED ring (NeoPixel) | Visual feedback (listening/thinking/speaking) |
| Button (GPIO) | Manual wake trigger |
| Camera module | Future: visual understanding |
| UPS HAT | Graceful shutdown on power loss |
