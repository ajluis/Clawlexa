#!/usr/bin/env bash
#
# Clawlexa Setup Script
# One-line setup for Raspberry Pi 5
#
# Usage: ./setup.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
VOICE_DIR="$SCRIPT_DIR/voices"
DEFAULT_VOICE="en_US-lessac-medium"

echo "🦞 Clawlexa Setup"
echo "=================="
echo ""

# ─── System Dependencies ───────────────────────────────────────────

echo "📦 Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    portaudio19-dev \
    libsndfile1 \
    pulseaudio \
    pulseaudio-module-bluetooth \
    bluez \
    bluez-tools \
    alsa-utils \
    ffmpeg \
    curl \
    wget \
    git

echo "✅ System dependencies installed."

# ─── Python Virtual Environment ────────────────────────────────────

echo ""
echo "🐍 Setting up Python virtual environment..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

pip install --upgrade pip setuptools wheel -q
pip install -r "$SCRIPT_DIR/requirements.txt" -q

echo "✅ Python environment ready."

# ─── Piper TTS Voice Model ─────────────────────────────────────────

echo ""
echo "🔊 Downloading Piper voice model ($DEFAULT_VOICE)..."
mkdir -p "$VOICE_DIR"

VOICE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
VOICE_JSON_URL="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"

if [ ! -f "$VOICE_DIR/$DEFAULT_VOICE.onnx" ]; then
    wget -q --show-progress -O "$VOICE_DIR/$DEFAULT_VOICE.onnx" "$VOICE_URL" || {
        echo "⚠️  Failed to download voice model. You can download it manually later."
    }
    wget -q --show-progress -O "$VOICE_DIR/$DEFAULT_VOICE.onnx.json" "$VOICE_JSON_URL" || true
    echo "✅ Voice model downloaded."
else
    echo "✅ Voice model already exists."
fi

# ─── Configuration ──────────────────────────────────────────────────

echo ""
if [ ! -f "$SCRIPT_DIR/config.yaml" ]; then
    echo "📝 Config file already in place at config.yaml"
    echo "   Edit it to set your API keys and Clawdbot gateway URL."
else
    echo "✅ Config file exists."
fi

# ─── Environment File ──────────────────────────────────────────────

if [ ! -f "$SCRIPT_DIR/.env" ]; then
    cat > "$SCRIPT_DIR/.env" << 'EOF'
# Clawlexa Environment Variables
# Fill in your API keys below

# Required: Picovoice access key (free at https://console.picovoice.ai/)
PORCUPINE_ACCESS_KEY=

# Required: OpenAI API key (for Whisper STT)
OPENAI_API_KEY=

# Required: Clawdbot Gateway token
CLAWDBOT_GATEWAY_TOKEN=

# Optional: Clawdbot Gateway URL (if not localhost)
# CLAWDBOT_GATEWAY_URL=http://your-server:3000
EOF
    echo "📝 Created .env file — fill in your API keys!"
else
    echo "✅ .env file exists."
fi

# ─── Systemd Service (Optional) ────────────────────────────────────

echo ""
read -p "🔧 Install systemd service for auto-start? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Update the service file with actual paths
    sed "s|/home/pi/Clawlexa|$SCRIPT_DIR|g" "$SCRIPT_DIR/systemd/clawlexa.service" | \
    sed "s|/home/pi/Clawlexa/venv/bin/python|$VENV_DIR/bin/python|g" | \
    sudo tee /etc/systemd/system/clawlexa.service > /dev/null

    sudo systemctl daemon-reload
    sudo systemctl enable clawlexa
    echo "✅ Systemd service installed. Start with: sudo systemctl start clawlexa"
fi

# ─── Done ───────────────────────────────────────────────────────────

echo ""
echo "🦞 Clawlexa setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and fill in your API keys"
echo "  2. Edit config.yaml to set your Clawdbot gateway URL"
echo "  3. Run: source venv/bin/activate && python src/main.py"
echo ""
echo "For full setup guide, see: docs/SETUP.md"
