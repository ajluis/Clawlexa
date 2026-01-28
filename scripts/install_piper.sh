#!/usr/bin/env bash
#
# Install Piper TTS for Raspberry Pi (aarch64)
#
set -euo pipefail

echo "🔊 Installing Piper TTS..."

# Method 1: pip install (preferred)
if command -v pip &> /dev/null; then
    echo "Installing via pip..."
    pip install piper-tts
    echo "✅ Piper installed via pip."
    exit 0
fi

# Method 2: Download pre-built binary
ARCH=$(uname -m)
case "$ARCH" in
    aarch64) PIPER_ARCH="aarch64" ;;
    x86_64)  PIPER_ARCH="amd64" ;;
    armv7l)  PIPER_ARCH="armv7l" ;;
    *)
        echo "❌ Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

PIPER_VERSION="2023.11.14-2"
PIPER_URL="https://github.com/rhasspy/piper/releases/download/${PIPER_VERSION}/piper_linux_${PIPER_ARCH}.tar.gz"
INSTALL_DIR="$HOME/.local/bin"

echo "Downloading Piper for ${PIPER_ARCH}..."
mkdir -p "$INSTALL_DIR"
wget -q --show-progress -O /tmp/piper.tar.gz "$PIPER_URL"
tar -xzf /tmp/piper.tar.gz -C /tmp/
cp /tmp/piper/piper "$INSTALL_DIR/"
cp -r /tmp/piper/lib/ "$INSTALL_DIR/piper_lib/" 2>/dev/null || true
rm -rf /tmp/piper /tmp/piper.tar.gz

# Ensure it's in PATH
if ! echo "$PATH" | grep -q "$INSTALL_DIR"; then
    echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> "$HOME/.bashrc"
    echo "Added $INSTALL_DIR to PATH (restart your shell or source ~/.bashrc)"
fi

echo "✅ Piper installed to $INSTALL_DIR/piper"
echo "Test with: echo 'Hello world' | $INSTALL_DIR/piper --model en_US-lessac-medium --output_file test.wav"
