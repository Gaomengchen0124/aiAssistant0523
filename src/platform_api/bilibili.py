"""
Bilibili API integration (placeholder).

Requires: Bilibili Open Platform developer account + app approval.
Docs: https://openhome.bilibili.com/
"""

from .base import PlatformAPIBase


class BilibiliAPI(PlatformAPIBase):
    """Bilibili Open Platform API integration."""

    BASE_URL = "https://openhome.bilibili.com"

    def send_private_message(self, recipient_id: str, message: str) -> dict:
        """Send a private message via Bilibili API."""
        # TODO: Implement Bilibili message API
        # Requires: appkey, appsecret, access_token
        raise NotImplementedError(
            "Bilibili API integration requires developer credentials. "
            "Apply at https://openhome.bilibili.com/"
        )

    def get_user_info(self, user_id: str) -> dict:
        """Get Bilibili user public info."""
        raise NotImplementedError("Bilibili API not yet implemented")
