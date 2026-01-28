#!/usr/bin/env python3
"""
Clawlexa — Personal voice assistant powered by Clawdbot.

Main orchestrator loop:
  Wake Word → STT → Brain → TTS → Speaker
"""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

from audio import AudioManager
from brain import ClawdbotBrain
from stt import WhisperSTT
from tts import PiperTTS
from vad import VoiceActivityDetector
from wake_word import WakeWordDetector

load_dotenv()

logger = logging.getLogger("clawlexa")


def load_config(path: str = "config.yaml") -> dict:
    """Load configuration from YAML file with env var overrides."""
    config_path = Path(path)
    if not config_path.exists():
        logger.error(f"Config file not found: {path}")
        logger.info("Copy config.yaml.example to config.yaml and configure it.")
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Environment variable overrides
    if key := os.getenv("PORCUPINE_ACCESS_KEY"):
        config.setdefault("wake_word", {})["access_key"] = key
    if key := os.getenv("OPENAI_API_KEY"):
        config.setdefault("stt", {})["api_key"] = key
    if token := os.getenv("CLAWDBOT_GATEWAY_TOKEN"):
        config.setdefault("brain", {})["gateway_token"] = token
    if url := os.getenv("CLAWDBOT_GATEWAY_URL"):
        config.setdefault("brain", {})["gateway_url"] = url

    return config


def setup_logging(config: dict) -> None:
    """Configure logging based on config."""
    log_config = config.get("logging", {})
    level = getattr(logging, log_config.get("level", "INFO").upper(), logging.INFO)
    log_file = log_config.get("file")

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


class Clawlexa:
    """Main voice assistant orchestrator."""

    def __init__(self, config: dict) -> None:
        self.config = config
        self._running = False
        self._current_task: Optional[asyncio.Task] = None

        # Initialize components
        self.audio = AudioManager(config.get("audio", {}))
        self.wake_word = WakeWordDetector(config.get("wake_word", {}))
        self.vad = VoiceActivityDetector(config.get("audio", {}))
        self.stt = WhisperSTT(config.get("stt", {}))
        self.brain = ClawdbotBrain(config.get("brain", {}))
        self.tts = PiperTTS(config.get("tts", {}))

        self._chime_on_wake = config.get("feedback", {}).get("chime_on_wake", True)

    async def start(self) -> None:
        """Initialize all components and start the main loop."""
        logger.info("🦞 Starting Clawlexa...")

        try:
            self.audio.initialize()
            self.wake_word.initialize()
            self.vad.initialize()
            await self.brain.connect()
            self.tts.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            await self.shutdown()
            raise

        self._running = True
        logger.info("✅ All components initialized. Listening for wake word...")

        await self._main_loop()

    async def _main_loop(self) -> None:
        """Main assistant loop: wake → listen → think → speak → repeat."""
        while self._running:
            try:
                # Step 1: Listen for wake word (blocking, runs in thread)
                detected = await asyncio.get_event_loop().run_in_executor(
                    None, self._wait_for_wake_word
                )
                if not detected or not self._running:
                    continue

                logger.info("🎤 Wake word detected!")

                # Step 2: Play acknowledgment chime
                if self._chime_on_wake:
                    self.audio.play_chime()

                # Step 3: Record speech until silence (VAD)
                logger.info("👂 Listening...")
                audio_data = await asyncio.get_event_loop().run_in_executor(
                    None, self._record_speech
                )

                if audio_data is None or len(audio_data) == 0:
                    logger.info("No speech detected, returning to wake word listening.")
                    continue

                # Step 4: Speech-to-text
                logger.info("🔤 Transcribing...")
                transcript = await self.stt.transcribe(audio_data)

                if not transcript or not transcript.strip():
                    logger.info("Empty transcript, ignoring.")
                    continue

                logger.info(f"📝 Heard: {transcript}")

                # Step 5: Send to Clawdbot brain
                logger.info("🧠 Thinking...")
                response = await self.brain.think(transcript)

                if not response:
                    logger.warning("No response from brain.")
                    response = "Sorry, I didn't get a response. Try again."

                logger.info(f"💬 Response: {response[:100]}...")

                # Step 6: Text-to-speech
                logger.info("🔊 Speaking...")
                audio_file = await asyncio.get_event_loop().run_in_executor(
                    None, self.tts.synthesize, response
                )

                # Step 7: Play response
                if audio_file:
                    await asyncio.get_event_loop().run_in_executor(
                        None, self.audio.play_file, audio_file
                    )

                logger.info("✅ Done. Listening for wake word...")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(1)  # Brief pause before retrying

    def _wait_for_wake_word(self) -> bool:
        """Block until wake word is detected. Returns False if shutting down."""
        while self._running:
            try:
                audio_frame = self.audio.read_frame(
                    self.wake_word.frame_length
                )
                if audio_frame is not None and self.wake_word.process(audio_frame):
                    return True
            except Exception as e:
                logger.error(f"Wake word error: {e}")
                return False
        return False

    def _record_speech(self) -> Optional[bytes]:
        """Record audio until VAD detects silence. Returns raw PCM bytes."""
        frames: list[bytes] = []
        silence_threshold = self.config.get("audio", {}).get("silence_threshold", 2.0)
        sample_rate = self.config.get("audio", {}).get("sample_rate", 16000)
        chunk_size = self.config.get("audio", {}).get("chunk_size", 512)

        self.vad.reset()
        silence_duration = 0.0
        has_speech = False
        max_duration = 30.0  # Maximum recording duration (seconds)
        total_duration = 0.0
        chunk_duration = chunk_size / sample_rate

        while self._running and total_duration < max_duration:
            frame = self.audio.read_frame(chunk_size)
            if frame is None:
                break

            frames.append(frame)
            total_duration += chunk_duration

            is_speech = self.vad.is_speech(frame, sample_rate)

            if is_speech:
                has_speech = True
                silence_duration = 0.0
            else:
                silence_duration += chunk_duration

            # Stop if we had speech and then enough silence
            if has_speech and silence_duration >= silence_threshold:
                logger.debug(f"Silence detected after {total_duration:.1f}s of recording")
                break

        if not has_speech:
            return None

        return b"".join(frames)

    async def shutdown(self) -> None:
        """Gracefully shut down all components."""
        logger.info("🛑 Shutting down Clawlexa...")
        self._running = False

        if self._current_task and not self._current_task.done():
            self._current_task.cancel()

        try:
            self.wake_word.cleanup()
        except Exception as e:
            logger.debug(f"Wake word cleanup: {e}")

        try:
            self.audio.cleanup()
        except Exception as e:
            logger.debug(f"Audio cleanup: {e}")

        try:
            await self.brain.disconnect()
        except Exception as e:
            logger.debug(f"Brain cleanup: {e}")

        try:
            self.tts.cleanup()
        except Exception as e:
            logger.debug(f"TTS cleanup: {e}")

        logger.info("👋 Clawlexa stopped.")


async def main() -> None:
    """Entry point."""
    # Change to project root directory
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)

    config = load_config()
    setup_logging(config)

    assistant = Clawlexa(config)

    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()

    def signal_handler(sig: int) -> None:
        logger.info(f"Received signal {sig}, shutting down...")
        asyncio.ensure_future(assistant.shutdown())

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler, sig)

    try:
        await assistant.start()
    except KeyboardInterrupt:
        pass
    finally:
        await assistant.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
