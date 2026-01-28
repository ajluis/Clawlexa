"""
Speech-to-Text using OpenAI Whisper API.

Sends recorded audio to the Whisper API and returns the transcript.
"""

import io
import logging
import os
import wave
from typing import Optional

from openai import AsyncOpenAI

logger = logging.getLogger("clawlexa.stt")


class WhisperSTT:
    """OpenAI Whisper API speech-to-text engine."""

    def __init__(self, config: dict) -> None:
        self.model: str = config.get("model", "whisper-1")
        self.language: Optional[str] = config.get("language", "en")
        api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OpenAI API key is required for Whisper STT. "
                "Set OPENAI_API_KEY env var or stt.api_key in config.yaml."
            )

        self._client = AsyncOpenAI(api_key=api_key)

    async def transcribe(
        self,
        audio_data: bytes,
        sample_rate: int = 16000,
        channels: int = 1,
    ) -> Optional[str]:
        """
        Transcribe raw PCM audio data to text.

        Args:
            audio_data: Raw 16-bit PCM audio bytes.
            sample_rate: Sample rate of the audio (default: 16000).
            channels: Number of audio channels (default: 1).

        Returns:
            Transcribed text, or None on error.
        """
        if not audio_data:
            return None

        try:
            # Convert PCM to WAV in memory (Whisper API expects a file)
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data)

            wav_buffer.seek(0)
            wav_buffer.name = "audio.wav"  # OpenAI client needs a filename

            # Call Whisper API
            kwargs: dict = {"model": self.model, "file": wav_buffer}
            if self.language:
                kwargs["language"] = self.language

            transcript = await self._client.audio.transcriptions.create(**kwargs)

            text = transcript.text.strip()
            logger.info(f"Transcribed ({len(audio_data)} bytes audio): '{text}'")
            return text

        except Exception as e:
            logger.error(f"Whisper API error: {e}", exc_info=True)
            return None
