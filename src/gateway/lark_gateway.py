"""Lark (Feishu) WebSocket gateway.

Handles WebSocket connection to Lark for event subscription,
message receiving, and card pushing.
"""

import asyncio
import hashlib
import json
import logging
import time
from collections.abc import Callable

import aiohttp
import requests

from src.config import Config
from src.gateway.card_templates import (
    task_error_card,
    task_progress_card,
    task_result_card,
    task_start_card,
)

logger = logging.getLogger(__name__)


class LarkGateway:
    """Lark WebSocket gateway for event subscription and message handling."""

    # Lark API endpoints
    EVENT_URL = "https://open.feishu.cn/open-apis/event/v2/"
    TENANT_ACCESS_TOKEN_URL = (
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    )
    SEND_MSG_URL = "https://open.feishu.cn/open-apis/im/v1/messages"

    def __init__(self, config: Config):
        self.config = config.lark
        self.app_id = config.lark.app_id
        self.app_secret = config.lark.app_secret
        self._tenant_token: str | None = None
        self._token_expires: float = 0
        self._message_callback: Callable | None = None
        self._running = False
        self._ws_session: aiohttp.ClientSession | None = None

    def on_message(self, callback: Callable):
        """Register a callback for incoming messages.

        Args:
            callback: Function(user_id, message_text) -> None
        """
        self._message_callback = callback
        logger.info("Message callback registered")

    async def start(self):
        """Start the WebSocket connection to Lark."""
        if not self.app_id or not self.app_secret:
            logger.warning("Lark credentials not configured, gateway disabled")
            return

        logger.info("Starting Lark gateway...")
        self._running = True

        # Get tenant access token
        await self._refresh_token()

        # Start WebSocket connection
        await self._connect_websocket()

    async def _refresh_token(self):
        """Refresh tenant access token."""
        try:
            response = requests.post(
                self.TENANT_ACCESS_TOKEN_URL,
                json={
                    "app_id": self.app_id,
                    "app_secret": self.app_secret,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            self._tenant_token = data["tenant_access_token"]
            self._token_expires = time.time() + data.get("expire", 7200)
            logger.info("Lark tenant token refreshed")

        except Exception as e:
            logger.error(f"Failed to refresh Lark token: {e}")

    async def _connect_websocket(self):
        """Establish WebSocket connection to Lark event subscription."""
        url = f"{self.EVENT_URL}sub?app_id={self.app_id}"

        # Calculate WebSocket signature
        timestamp = str(int(time.time()))
        sign_str = f"{timestamp}\n{self.app_secret}"
        sign = hashlib.sha256(sign_str.encode()).hexdigest()

        ws_url = f"{url}&timestamp={timestamp}&sign={sign}"

        try:
            async with aiohttp.ClientSession() as session:
                self._ws_session = session
                async with session.ws_connect(ws_url) as ws:
                    logger.info("Lark WebSocket connected")

                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            await self._handle_ws_message(msg.data)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            logger.error("Lark WebSocket error")
                            break

        except Exception as e:
            logger.error(f"Lark WebSocket connection failed: {e}")

            if self._running:
                logger.info("Reconnecting in 5s...")
                await asyncio.sleep(5)
                await self._connect_websocket()

    async def _handle_ws_message(self, data: str):
        """Handle incoming WebSocket message."""
        try:
            event = json.loads(data)

            # Handle challenge (connection verification)
            if event.get("challenge"):
                logger.info("Lark challenge received, responding")
                return

            # Handle token refresh
            if event.get("subscribe_to_resource") == "v1.im.message.receive":
                logger.info("Event subscription confirmed")
                return

            # Handle message events
            header = event.get("header", {})
            event_type = header.get("event_type", "")

            if event_type == "message.receive_v1":
                await self._handle_message_event(event)

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from Lark: {data[:100]}")
        except Exception as e:
            logger.error(f"Error handling Lark message: {e}")

    async def _handle_message_event(self, event: dict):
        """Process incoming message event."""
        try:
            event_data = event.get("event", {})
            message = event_data.get("message", {})
            sender = event_data.get("sender", {})

            message_type = message.get("message_type", "")
            if message_type != "text":
                logger.debug(f"Non-text message type: {message_type}")
                return

            content = json.loads(message.get("content", "{}"))
            text = content.get("text", "")

            sender_id = sender.get("sender_id", {}).get("open_id", "")
            message.get("chat_id", "")

            logger.info(f"Message from {sender_id}: {text[:100]}")

            # Send to callback
            if self._message_callback:
                # Run callback in executor to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None,
                    self._message_callback,
                    sender_id,
                    text,
                )

        except Exception as e:
            logger.error(f"Error processing message event: {e}")

    async def send_card(self, user_id: str, card: dict):
        """Send a message card to a user."""
        if not self._tenant_token:
            logger.warning("No tenant token, cannot send card")
            return

        # Create a single chat with the user and send card
        card_json = json.dumps({"card": card})

        url = f"{self.SEND_MSG_URL}?receive_id_type=open_id"
        headers = {
            "Authorization": f"Bearer {self._tenant_token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        payload = {
            "receive_id": user_id,
            "msg_type": "interactive",
            "content": card_json,
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info(f"Card sent to {user_id}")
        except Exception as e:
            logger.error(f"Failed to send card: {e}")

    async def send_task_start(self, user_id: str, goal: str, plan: str = ""):
        """Send task start card."""
        card = task_start_card(goal, plan)
        await self.send_card(user_id, card)

    async def send_task_progress(
        self, user_id: str, step: int, total: int, detail: str
    ):
        """Send task progress card."""
        card = task_progress_card(step, total, detail)
        await self.send_card(user_id, card)

    async def send_task_result(
        self,
        user_id: str,
        summary: str,
        details: str = "",
        mode: str = "react",
        iterations: int = 0,
        elapsed: float = 0,
    ):
        """Send task result card."""
        card = task_result_card(summary, details, mode, iterations, elapsed)
        await self.send_card(user_id, card)

    async def send_task_error(self, user_id: str, error: str, partial_result: str = ""):
        """Send task error card."""
        card = task_error_card(error, partial_result)
        await self.send_card(user_id, card)

    def stop(self):
        """Stop the gateway."""
        self._running = False
        logger.info("Lark gateway stopping")
