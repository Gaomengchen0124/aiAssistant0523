"""
Douyin API integration (placeholder).

Requires: Douyin Open Platform developer account + app approval.
Docs: https://developer.open-douyin.com/
"""

from .base import PlatformAPIBase


class DouyinAPI(PlatformAPIBase):
    """Douyin Open Platform API integration."""

    BASE_URL = "https://open.douyin.com"

    def send_private_message(self, recipient_id: str, message: str) -> dict:
        """Send a private message via Douyin API."""
        # TODO: Implement Douyin message API
        # Requires: client_key, client_secret, access_token
        raise NotImplementedError(
            "Douyin API integration requires developer credentials. "
            "Apply at https://developer.open-douyin.com/"
        )

    def get_user_info(self, user_id: str) -> dict:
        """Get Douyin user public info."""
        raise NotImplementedError("Douyin API not yet implemented")
