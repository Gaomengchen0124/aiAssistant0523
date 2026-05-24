"""
Weibo API integration (placeholder).

Requires: Weibo Open Platform developer account + app approval.
Docs: https://open.weibo.com/wiki/API
"""

from .base import PlatformAPIBase


class WeiboAPI(PlatformAPIBase):
    """Weibo Open Platform API integration."""

    BASE_URL = "https://api.weibo.com/2"

    def send_private_message(self, recipient_id: str, message: str) -> dict:
        """Send a private message via Weibo API."""
        # TODO: Implement OAuth2 flow and /messages/send API
        # Requires: access_token, uid
        raise NotImplementedError(
            "Weibo API integration requires developer credentials. "
            "Apply at https://open.weibo.com/"
        )

    def get_user_info(self, user_id: str) -> dict:
        """Get Weibo user public info."""
        raise NotImplementedError("Weibo API not yet implemented")
