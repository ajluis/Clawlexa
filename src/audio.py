"""
Audio I/O manager for microphone capture and speaker output.

Handles PyAudio streams, Bluetooth/USB device selection,
and PulseAudio/PipeWire integration.
"""

import io
import logging
import math
import struct
import wave
from pathlib import Path
from typing import Optional

import numpy as np
import pyaudio
import soundfile as sf

logger = logging.getLogger("clawlexa.audio")

# Chime: short 440Hz beep generated in-memory
_CHIME_FREQ = 880
_CHIME_DURATION = 0.15  # seconds
_CHIME_SAMPLE_RATE = 16000


def _generate_chime() -> bytes:
    """Generate a short beep as raw PCM bytes."""
    n_samples = int(_CHIME_SAMPLE_RATE * _CHIME_DURATION)
    samples = []
    for i in range(n_samples):
        t = i / _CHIME_SAMPLE_RATE
        # Sine wave with fade-in/fade-out envelope
        envelope = min(1.0, i / 200) * min(1.0, (n_samples - i) / 200)
        value = int(16000 * envelope * math.sin(2 * math.pi * _CHIME_FREQ * t))
        samples.append(max(-32768, min(32767, value)))
    return struct.pack(f"{len(samples)}h", *samples)


class AudioManager:
    """Manages audio input (microphone) and output (speaker)."""

    def __init__(self, config: dict) -> None:
        self.sample_rate: int = config.get("sample_rate", 16000)
        self.channels: int = config.get("channels", 1)
        self.chunk_size: int = config.get("chunk_size", 512)
        self.input_device: Optional[int] = config.get("input_device")
        self.output_device: Optional[int] = config.get("output_device")

        self._pa: Optional[pyaudio.PyAudio] = None
        self._input_stream: Optional[pyaudio.Stream] = None
        self._chime_data: bytes = _generate_chime()

    def initialize(self) -> None:
        """Initialize PyAudio and open the input stream."""
        self._pa = pyaudio.PyAudio()

        # Log available devices
        self._log_devices()

        # Open input stream (microphone)
        try:
            stream_kwargs: dict = {
                "format": pyaudio.paInt16,
                "channels": self.channels,
                "rate": self.sample_rate,
                "input": True,
                "frames_per_buffer": self.chunk_size,
            }
            if self.input_device is not None:
                stream_kwargs["input_device_index"] = self.input_device

            self._input_stream = self._pa.open(**stream_kwargs)
            logger.info(
                f"Audio input opened: {self.sample_rate}Hz, "
                f"{self.channels}ch, chunk={self.chunk_size}"
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to open audio input: {e}. "
                f"Run 'python -c \"import pyaudio; p = pyaudio.PyAudio(); "
                f"[print(p.get_device_info_by_index(i)) for i in range(p.get_device_count())]\"' "
                f"to list available devices."
            ) from e

    def _log_devices(self) -> None:
        """Log available audio devices."""
        if self._pa is None:
            return
        info = self._pa.get_host_api_info_by_index(0)
        num_devices = info.get("deviceCount", 0)

        logger.info("Available audio devices:")
        for i in range(num_devices):
            dev = self._pa.get_device_info_by_index(i)
            direction = []
            if dev.get("maxInputChannels", 0) > 0:
                direction.append("IN")
            if dev.get("maxOutputChannels", 0) > 0:
                direction.append("OUT")
            logger.info(
                f"  [{i}] {dev['name']} ({'/'.join(direction)}) "
                f"@ {int(dev['defaultSampleRate'])}Hz"
            )

    def read_frame(self, num_frames: Optional[int] = None) -> Optional[bytes]:
        """
        Read a single frame of audio from the microphone.

        Args:
            num_frames: Number of frames to read. Defaults to chunk_size.

        Returns:
            Raw PCM audio bytes, or None on error.
        """
        if self._input_stream is None:
            return None

        frames = num_frames or self.chunk_size

        try:
            data = self._input_stream.read(frames, exception_on_overflow=False)
            return data
        except IOError as e:
            logger.warning(f"Audio read error: {e}")
            return None

    def play_chime(self) -> None:
        """Play a short acknowledgment beep through the speaker."""
        if self._pa is None:
            return

        try:
            stream_kwargs: dict = {
                "format": pyaudio.paInt16,
                "channels": 1,
                "rate": _CHIME_SAMPLE_RATE,
                "output": True,
            }
            if self.output_device is not None:
                stream_kwargs["output_device_index"] = self.output_device

            stream = self._pa.open(**stream_kwargs)
            stream.write(self._chime_data)
            stream.stop_stream()
            stream.close()
        except Exception as e:
            logger.warning(f"Failed to play chime: {e}")

    def play_file(self, file_path: str) -> None:
        """
        Play a WAV audio file through the speaker.

        Args:
            file_path: Path to a WAV file.
        """
        if self._pa is None:
            logger.error("AudioManager not initialized.")
            return

        path = Path(file_path)
        if not path.exists():
            logger.error(f"Audio file not found: {file_path}")
            return

        try:
            wf = wave.open(str(path), "rb")

            stream_kwargs: dict = {
                "format": self._pa.get_format_from_width(wf.getsampwidth()),
                "channels": wf.getnchannels(),
                "rate": wf.getframerate(),
                "output": True,
            }
            if self.output_device is not None:
                stream_kwargs["output_device_index"] = self.output_device

            stream = self._pa.open(**stream_kwargs)

            chunk = 1024
            data = wf.readframes(chunk)
            while data:
                stream.write(data)
                data = wf.readframes(chunk)

            stream.stop_stream()
            stream.close()
            wf.close()

        except Exception as e:
            logger.error(f"Failed to play audio file {file_path}: {e}")

    def play_bytes(self, audio_data: bytes, sample_rate: int = 16000) -> None:
        """
        Play raw PCM audio bytes through the speaker.

        Args:
            audio_data: Raw 16-bit PCM audio bytes.
            sample_rate: Sample rate of the audio data.
        """
        if self._pa is None:
            return

        try:
            stream_kwargs: dict = {
                "format": pyaudio.paInt16,
                "channels": 1,
                "rate": sample_rate,
                "output": True,
            }
            if self.output_device is not None:
                stream_kwargs["output_device_index"] = self.output_device

            stream = self._pa.open(**stream_kwargs)
            stream.write(audio_data)
            stream.stop_stream()
            stream.close()

        except Exception as e:
            logger.error(f"Failed to play audio bytes: {e}")

    def pcm_to_wav_bytes(self, pcm_data: bytes) -> bytes:
        """
        Convert raw PCM data to WAV format in memory.

        Args:
            pcm_data: Raw 16-bit PCM audio bytes.

        Returns:
            WAV file content as bytes.
        """
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self.sample_rate)
            wf.writeframes(pcm_data)
        return buf.getvalue()

    def cleanup(self) -> None:
        """Close streams and terminate PyAudio."""
        if self._input_stream is not None:
            try:
                self._input_stream.stop_stream()
                self._input_stream.close()
            except Exception:
                pass
            self._input_stream = None

        if self._pa is not None:
            self._pa.terminate()
            self._pa = None
            logger.info("Audio resources released.")
