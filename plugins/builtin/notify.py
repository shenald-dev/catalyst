"""Notify Plugin: Sending notifications via webhooks and email.

Supports:
  - Webhooks (Slack, Discord, generic)
  - Email via SMTP
Configuration:
  - webhook_url: Slack/Discord webhook URL (optional)
  - smtp_host, smtp_port, smtp_user, smtp_password: for email
  - from_addr: sender email
"""
import asyncio
from typing import Dict, Any
from core.plugin import Plugin

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    import aiosmtplib
    HAS_SMTP = True
except ImportError:
    HAS_SMTP = False


class NotifyPlugin(Plugin):
    name = "notify"
    version = "0.2.0"
    description = "Notification dispatcher (webhooks, email)"

    def __init__(self, webhook_url: str = "", smtp_host: str = "", smtp_port: int = 587,
                 smtp_user: str = "", smtp_password: str = "", from_addr: str = "",
                 **kwargs):
        """
        Args:
            webhook_url: Webhook endpoint (Slack/Discord)
            smtp_*: SMTP configuration
            from_addr: Default sender email
        """
        self.webhook_url = webhook_url
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_addr = from_addr
        self._session = None
        self._stats = {"sent": 0, "errors": 0}

    def on_load(self) -> None:
        pass

    async def on_unload(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    def health_check(self) -> bool:
        # If any transport is configured, check dependency
        if self.webhook_url and not HAS_AIOHTTP:
            return False
        if self.smtp_host and not HAS_SMTP:
            return False
        return True

    async def execute(self, message: str, title: str = "", recipient: str = "",
                      method: str = "webhook") -> bool:
        """
        Send a notification.

        Args:
            message: Notification body
            title: Subject/title
            recipient: Email address (for email) or unused for webhook
            method: "webhook" or "email"

        Returns:
            True if sent successfully, False otherwise.
        """
        if method == "webhook":
            return await self._send_webhook(message, title)
        elif method == "email":
            return await self._send_email(message, title, recipient)
        else:
            raise ValueError(f"Unknown notify method: {method}")

    async def _send_webhook(self, message: str, title: str = "") -> bool:
        if not self.webhook_url:
            raise ValueError("No webhook_url configured")
        if not HAS_AIOHTTP:
            raise RuntimeError("aiohttp is not installed")

        if self._session is None:
            self._session = aiohttp.ClientSession()

        # Assume Slack/Discord format: payload with blocks or text
        payload = {
            "text": f"{title}\n{message}" if title else message
        }
        try:
            async with self._session.post(self.webhook_url, json=payload) as resp:
                if resp.status == 200:
                    self._stats["sent"] += 1
                    return True
                else:
                    self._stats["errors"] += 1
                    return False
        except Exception as e:
            self._stats["errors"] += 1
            raise

    async def _send_email(self, message: str, title: str, to_addr: str) -> bool:
        if not self.smtp_host:
            raise ValueError("No SMTP configured")
        if not HAS_SMTP:
            raise RuntimeError("aiosmtplib is not installed")
        if not self.from_addr:
            raise ValueError("from_addr not set")

        import email.message
        msg = email.message.EmailMessage()
        msg["From"] = self.from_addr
        msg["To"] = to_addr
        msg["Subject"] = title or "Notification"
        msg.set_content(message)

        try:
            async with aiosmtplib.SMTP(hostname=self.smtp_host, port=self.smtp_port) as server:
                await server.starttls()
                if self.smtp_user:
                    await server.login(self.smtp_user, self.smtp_password)
                await server.send_message(msg)
            self._stats["sent"] += 1
            return True
        except Exception as e:
            self._stats["errors"] += 1
            raise

    def metrics(self) -> Dict[str, int]:
        return self._stats.copy()