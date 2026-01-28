#!/usr/bin/env bash
#
# Install Porcupine wake word engine dependencies
#
set -euo pipefail

echo "🎤 Installing Porcupine wake word engine..."

# Install the Python package
pip install pvporcupine

echo ""
echo "✅ Porcupine installed."
echo ""
echo "You need a free access key from Picovoice:"
echo "  1. Go to https://console.picovoice.ai/"
echo "  2. Sign up (free tier available)"
echo "  3. Copy your Access Key"
echo "  4. Set it in .env: PORCUPINE_ACCESS_KEY=your-key-here"
echo ""
echo "Built-in wake words (free):"
echo "  alexa, americano, blueberry, bumblebee, computer,"
echo "  grapefruit, grasshopper, hey barista, hey google,"
echo "  hey siri, jarvis, ok google, pico clock, picovoice,"
echo "  porcupine, smart mirror, terminator, view glass"
echo ""
echo "Default wake word: 'picovoice'"
echo "Change in config.yaml under wake_word.keyword"
