"""
Voice Activity Detection using Silero VAD.

Detects when the user starts and stops speaking, so we know
when to stop recording after the wake word trigger.
"""

import logging
import struct
from typing import Optional

import numpy as np
import torch

logger = logging.getLogger("clawlexa.vad")


class VoiceActivityDetector:
    """Silero VAD-based voice activity detector."""

    def __init__(self, config: dict) -> None:
        self.sample_rate: int = config.get("sample_rate", 16000)
        self._model: Optional[torch.jit.ScriptModule] = None
        self._threshold: float = 0.5

    def initialize(self) -> None:
        """Load the Silero VAD model."""
        try:
            model, utils = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                trust_repo=True,
            )
            self._model = model
            logger.info("Silero VAD model loaded")
        except Exception as e:
            logger.warning(
                f"Failed to load Silero VAD: {e}. "
                f"Falling back to energy-based VAD."
            )
            self._model = None

    def reset(self) -> None:
        """Reset the VAD state for a new utterance."""
        if self._model is not None:
            self._model.reset_states()

    def is_speech(self, audio_frame: bytes, sample_rate: int = 16000) -> bool:
        """
        Check if an audio frame contains speech.

        Args:
            audio_frame: Raw 16-bit PCM audio bytes.
            sample_rate: Sample rate of the audio.

        Returns:
            True if speech is detected in the frame.
        """
        if self._model is not None:
            return self._silero_detect(audio_frame, sample_rate)
        else:
            return self._energy_detect(audio_frame)

    def _silero_detect(self, audio_frame: bytes, sample_rate: int) -> bool:
        """Detect speech using Silero VAD model."""
        try:
            # Convert bytes to float32 tensor
            num_samples = len(audio_frame) // 2
            pcm = struct.unpack_from(f"{num_samples}h", audio_frame)
            audio_float = np.array(pcm, dtype=np.float32) / 32768.0
            tensor = torch.from_numpy(audio_float)

            # Silero VAD expects specific chunk sizes: 256, 512, or 768 for 16kHz
            # Pad or trim to 512 if needed
            target_size = 512
            if len(tensor) < target_size:
                tensor = torch.nn.functional.pad(tensor, (0, target_size - len(tensor)))
            elif len(tensor) > target_size:
                tensor = tensor[:target_size]

            # Run VAD
            confidence = self._model(tensor, sample_rate).item()
            return confidence > self._threshold

        except Exception as e:
            logger.debug(f"Silero VAD error: {e}")
            return self._energy_detect(audio_frame)

    @staticmethod
    def _energy_detect(audio_frame: bytes, threshold: float = 500.0) -> bool:
        """
        Simple energy-based voice activity detection (fallback).

        Args:
            audio_frame: Raw 16-bit PCM audio bytes.
            threshold: RMS energy threshold for speech detection.

        Returns:
            True if the audio energy exceeds the threshold.
        """
        num_samples = len(audio_frame) // 2
        if num_samples == 0:
            return False

        pcm = struct.unpack_from(f"{num_samples}h", audio_frame)
        rms = np.sqrt(np.mean(np.array(pcm, dtype=np.float64) ** 2))
        return rms > threshold
