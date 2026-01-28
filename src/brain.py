"""
Clawdbot Gateway brain — sends user speech to Clawdbot and gets responses.

Communicates with the Clawdbot Gateway API via HTTP to process
user requests through Claude.
"""

import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger("clawlexa.brain")


class ClawdbotBrain:
    """Communicates with Clawdbot Gateway for AI-powered responses."""

    def __init__(self, config: dict) -> None:
        self.gateway_url: str = (
            config.get("gateway_url")
            or os.getenv("CLAWDBOT_GATEWAY_URL", "http://localhost:3000")
        ).rstrip("/")
        self.gateway_token: str = (
            config.get("gateway_token")
            or os.getenv("CLAWDBOT_GATEWAY_TOKEN", "")
        )
        self.session: str = config.get("session", "clawlexa")
        self.timeout: float = config.get("timeout", 30)

        self._client: Optional[httpx.AsyncClient] = None

        if not self.gateway_token:
            raise ValueError(
                "Clawdbot Gateway token is required. "
                "Set CLAWDBOT_GATEWAY_TOKEN env var or brain.gateway_token in config.yaml."
            )

    async def connect(self) -> None:
        """Initialize the HTTP client."""
        self._client = httpx.AsyncClient(
            base_url=self.gateway_url,
            timeout=httpx.Timeout(self.timeout, connect=10.0),
            headers={
                "Authorization": f"Bearer {self.gateway_token}",
                "Content-Type": "application/json",
            },
        )
        logger.info(f"Brain connected to Clawdbot Gateway at {self.gateway_url}")

    async def think(self, user_message: str) -> Optional[str]:
        """
        Send a message to Clawdbot and get a response.

        Args:
            user_message: The user's transcribed speech.

        Returns:
            Clawdbot's text response, or None on error.
        """
        if self._client is None:
            raise RuntimeError("Brain not connected. Call connect() first.")

        try:
            payload = {
                "message": user_message,
                "session": self.session,
            }

            logger.debug(f"Sending to brain: {user_message}")

            response = await self._client.post("/api/message", json=payload)
            response.raise_for_status()

            data = response.json()

            # Extract the response text from Clawdbot's reply
            # The exact format depends on the Gateway API version
            reply = (
                data.get("reply")
                or data.get("response")
                or data.get("message")
                or data.get("text")
            )

            if reply:
                # Clean up for speech — strip markdown, code blocks, etc.
                reply = self._clean_for_speech(reply)
                logger.debug(f"Brain response: {reply[:200]}")
                return reply

            logger.warning(f"Unexpected response format: {data}")
            return None

        except httpx.TimeoutException:
            logger.error("Brain request timed out")
            return None
        except httpx.HTTPStatusError as e:
            logger.error(f"Brain HTTP error {e.response.status_code}: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Brain error: {e}", exc_info=True)
            return None

    @staticmethod
    def _clean_for_speech(text: str) -> str:
        """
        Clean text for natural speech output.

        Removes markdown formatting, code blocks, and other
        elements that don't make sense when spoken.
        """
        import re

        # Remove code blocks
        text = re.sub(r"```[\s\S]*?```", "I have some code for that. ", text)
        text = re.sub(r"`([^`]+)`", r"\1", text)

        # Remove markdown headers
        text = re.sub(r"#{1,6}\s+", "", text)

        # Remove markdown bold/italic
        text = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", text)
        text = re.sub(r"_{1,3}([^_]+)_{1,3}", r"\1", text)

        # Remove markdown links, keep text
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        # Remove bullet points
        text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)

        # Remove numbered lists markers
        text = re.sub(r"^\s*\d+\.\s+", "", text, flags=re.MULTILINE)

        # Collapse multiple newlines
        text = re.sub(r"\n{2,}", ". ", text)
        text = re.sub(r"\n", " ", text)

        # Collapse multiple spaces
        text = re.sub(r"\s{2,}", " ", text)

        return text.strip()

    async def disconnect(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("Brain disconnected.")
