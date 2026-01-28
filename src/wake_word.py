"""
Wake word detection using Porcupine (Picovoice).

Listens continuously for a wake word with minimal CPU usage.
Default keyword is "picovoice" (free, built-in). Custom keywords
require a .ppn file from Picovoice Console.
"""

import logging
import os
import struct
from typing import Optional

import pvporcupine

logger = logging.getLogger("clawlexa.wake_word")


class WakeWordDetector:
    """Porcupine-based wake word detector."""

    def __init__(self, config: dict) -> None:
        self.access_key: str = config.get("access_key", "") or os.getenv("PORCUPINE_ACCESS_KEY", "")
        self.keyword: str = config.get("keyword", "picovoice")
        self.sensitivity: float = config.get("sensitivity", 0.5)
        self._porcupine: Optional[pvporcupine.Porcupine] = None

    @property
    def frame_length(self) -> int:
        """Number of audio samples per frame required by Porcupine."""
        if self._porcupine is None:
            # Default frame length before initialization
            return 512
        return self._porcupine.frame_length

    @property
    def sample_rate(self) -> int:
        """Sample rate required by Porcupine."""
        if self._porcupine is None:
            return 16000
        return self._porcupine.sample_rate

    def initialize(self) -> None:
        """Initialize the Porcupine engine."""
        if not self.access_key:
            raise ValueError(
                "Porcupine access key is required. "
                "Set PORCUPINE_ACCESS_KEY env var or access_key in config.yaml. "
                "Get a free key at https://console.picovoice.ai/"
            )

        try:
            # Check if keyword is a file path (custom keyword) or built-in
            if os.path.isfile(self.keyword):
                logger.info(f"Using custom wake word: {self.keyword}")
                self._porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keyword_paths=[self.keyword],
                    sensitivities=[self.sensitivity],
                )
            else:
                logger.info(f"Using built-in wake word: '{self.keyword}'")
                self._porcupine = pvporcupine.create(
                    access_key=self.access_key,
                    keywords=[self.keyword],
                    sensitivities=[self.sensitivity],
                )

            logger.info(
                f"Porcupine initialized (frame_length={self.frame_length}, "
                f"sample_rate={self.sample_rate})"
            )

        except pvporcupine.PorcupineError as e:
            raise RuntimeError(f"Failed to initialize Porcupine: {e}") from e

    def process(self, audio_frame: bytes) -> bool:
        """
        Process a single audio frame and check for wake word.

        Args:
            audio_frame: Raw PCM audio bytes (16-bit signed, mono).
                         Must contain exactly `frame_length` samples.

        Returns:
            True if wake word was detected in this frame.
        """
        if self._porcupine is None:
            raise RuntimeError("WakeWordDetector not initialized. Call initialize() first.")

        # Convert bytes to list of int16 values
        num_samples = len(audio_frame) // 2
        pcm = struct.unpack_from(f"{num_samples}h", audio_frame)

        # Porcupine expects exactly frame_length samples
        if len(pcm) != self._porcupine.frame_length:
            logger.warning(
                f"Frame size mismatch: got {len(pcm)}, "
                f"expected {self._porcupine.frame_length}"
            )
            return False

        keyword_index = self._porcupine.process(pcm)
        return keyword_index >= 0

    def cleanup(self) -> None:
        """Release Porcupine resources."""
        if self._porcupine is not None:
            self._porcupine.delete()
            self._porcupine = None
            logger.info("Porcupine resources released.")
