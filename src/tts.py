"""
Text-to-Speech using Piper TTS (local, offline).

Piper is a fast, lightweight TTS engine that runs entirely on-device.
No internet connection required after voice model download.

Voice models: https://github.com/rhasspy/piper/blob/master/VOICES.md
"""

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger("clawlexa.tts")


class PiperTTS:
    """Piper TTS engine for local text-to-speech synthesis."""

    def __init__(self, config: dict) -> None:
        self.voice: str = config.get("voice", "en_US-lessac-medium")
        self.voice_dir: Path = Path(config.get("voice_dir", "./voices"))
        self.speed: float = config.get("speed", 1.0)
        self.speaker_id: Optional[int] = config.get("speaker_id")

        self._piper_bin: Optional[str] = None
        self._model_path: Optional[Path] = None
        self._temp_dir = tempfile.mkdtemp(prefix="clawlexa_tts_")

    def initialize(self) -> None:
        """Verify Piper is installed and voice model is available."""
        # Find piper binary
        self._piper_bin = self._find_piper()
        if not self._piper_bin:
            raise RuntimeError(
                "Piper TTS not found. Install it with: ./scripts/install_piper.sh\n"
                "Or: pip install piper-tts"
            )

        # Check for voice model
        self._model_path = self._find_voice_model()
        if self._model_path:
            logger.info(f"Piper TTS initialized with voice: {self.voice}")
            logger.info(f"Model: {self._model_path}")
        else:
            logger.warning(
                f"Voice model '{self.voice}' not found in {self.voice_dir}. "
                f"Run: piper --download-dir {self.voice_dir} --model {self.voice} "
                f"--update-voices"
            )

    def _find_piper(self) -> Optional[str]:
        """Find the piper binary or Python module."""
        # Check if piper is in PATH
        try:
            result = subprocess.run(
                ["which", "piper"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

        # Check if piper-tts Python package is available
        try:
            import piper  # noqa: F401
            return "piper"  # Use as Python module
        except ImportError:
            pass

        # Check common install locations
        common_paths = [
            Path.home() / ".local" / "bin" / "piper",
            Path("/usr/local/bin/piper"),
            Path("/usr/bin/piper"),
        ]
        for p in common_paths:
            if p.exists():
                return str(p)

        return None

    def _find_voice_model(self) -> Optional[Path]:
        """Find the voice model file in the voices directory."""
        self.voice_dir.mkdir(parents=True, exist_ok=True)

        # Look for .onnx model file
        patterns = [
            f"{self.voice}.onnx",
            f"{self.voice}/*.onnx",
        ]

        for pattern in patterns:
            matches = list(self.voice_dir.glob(pattern))
            if matches:
                return matches[0]

        # Also check in subdirectories
        for onnx_file in self.voice_dir.rglob("*.onnx"):
            if self.voice in onnx_file.stem or self.voice in str(onnx_file.parent):
                return onnx_file

        return None

    def synthesize(self, text: str) -> Optional[str]:
        """
        Convert text to speech and save as a WAV file.

        Args:
            text: Text to synthesize.

        Returns:
            Path to the generated WAV file, or None on error.
        """
        if not text or not text.strip():
            return None

        output_path = Path(self._temp_dir) / "response.wav"

        try:
            # Try Python piper-tts module first
            if self._try_piper_python(text, str(output_path)):
                return str(output_path)

            # Fall back to CLI
            if self._try_piper_cli(text, str(output_path)):
                return str(output_path)

            logger.error("All TTS methods failed")
            return None

        except Exception as e:
            logger.error(f"TTS synthesis error: {e}", exc_info=True)
            return None

    def _try_piper_python(self, text: str, output_path: str) -> bool:
        """Try synthesizing with the piper-tts Python package."""
        try:
            from piper import PiperVoice
            import wave

            model_path = self._model_path
            if model_path is None:
                # Let piper download the model
                model_path = self.voice

            voice = PiperVoice.load(str(model_path))

            with wave.open(output_path, "wb") as wav_file:
                voice.synthesize(text, wav_file, speaker_id=self.speaker_id)

            logger.debug(f"Synthesized {len(text)} chars via piper-tts Python")
            return True

        except ImportError:
            return False
        except Exception as e:
            logger.debug(f"piper-tts Python failed: {e}")
            return False

    def _try_piper_cli(self, text: str, output_path: str) -> bool:
        """Try synthesizing with the piper CLI binary."""
        if not self._piper_bin or self._piper_bin == "piper":
            return False

        try:
            cmd = [self._piper_bin, "--output_file", output_path]

            if self._model_path:
                cmd.extend(["--model", str(self._model_path)])
            else:
                cmd.extend(["--model", self.voice])
                cmd.extend(["--download-dir", str(self.voice_dir)])

            if self.speaker_id is not None:
                cmd.extend(["--speaker", str(self.speaker_id)])

            if self.speed != 1.0:
                cmd.extend(["--length-scale", str(1.0 / self.speed)])

            result = subprocess.run(
                cmd,
                input=text,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0 and Path(output_path).exists():
                logger.debug(f"Synthesized {len(text)} chars via piper CLI")
                return True

            logger.debug(f"Piper CLI error: {result.stderr}")
            return False

        except Exception as e:
            logger.debug(f"Piper CLI failed: {e}")
            return False

    def cleanup(self) -> None:
        """Clean up temporary files."""
        import shutil

        try:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        except Exception:
            pass
        logger.info("TTS resources released.")
