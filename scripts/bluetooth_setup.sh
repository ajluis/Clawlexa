#!/usr/bin/env bash
#
# Bluetooth speaker setup helper for Raspberry Pi
#
set -euo pipefail

echo "📡 Bluetooth Speaker Setup"
echo "=========================="
echo ""

# Ensure Bluetooth service is running
echo "Starting Bluetooth service..."
sudo systemctl enable bluetooth
sudo systemctl start bluetooth

# Ensure PulseAudio Bluetooth module is loaded
echo "Loading PulseAudio Bluetooth module..."
pactl load-module module-bluetooth-discover 2>/dev/null || true
pactl load-module module-bluetooth-policy 2>/dev/null || true

echo ""
echo "🔍 Scanning for Bluetooth devices..."
echo "   Put your speaker in pairing mode now!"
echo "   (Press Ctrl+C when you see your device)"
echo ""

# Start scanning
bluetoothctl scan on &
SCAN_PID=$!
sleep 10
kill $SCAN_PID 2>/dev/null || true

echo ""
echo "📋 Found devices. To pair your speaker:"
echo ""
echo "  1. Find your device MAC address above (XX:XX:XX:XX:XX:XX)"
echo "  2. Run these commands:"
echo ""
echo "     bluetoothctl"
echo "     > trust XX:XX:XX:XX:XX:XX"
echo "     > pair XX:XX:XX:XX:XX:XX"
echo "     > connect XX:XX:XX:XX:XX:XX"
echo "     > exit"
echo ""
echo "  3. Set as default audio output:"
echo "     pactl set-default-sink bluez_sink.XX_XX_XX_XX_XX_XX.a2dp_sink"
echo ""
echo "  4. Test audio:"
echo "     speaker-test -t wav -c 2"
echo ""
echo "💡 To auto-connect on boot, the 'trust' command above handles it."
echo "   PulseAudio will automatically switch to Bluetooth when available."
