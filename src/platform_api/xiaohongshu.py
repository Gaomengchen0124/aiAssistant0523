"""
Xiaohongshu (Little Red Book) API integration (placeholder).

Requires: XHS Open Platform developer account + app approval.
Docs: https://open.xiaohongshu.com/
"""

from .base import PlatformAPIBase


class XiaohongshuAPI(PlatformAPIBase):
    """Xiaohongshu Open Platform API integration."""

    BASE_URL = "https://open.xiaohongshu.com"

    def send_private_message(self, recipient_id: str, message: str) -> dict:
        """Send a private message via XHS API."""
        # TODO: Implement XHS message API
        # Requires: app_key, app_secret, user_access_token
        raise NotImplementedError(
            "Xiaohongshu API integration requires developer credentials. "
            "Apply at https://open.xiaohongshu.com/"
        )

    def get_user_info(self, user_id: str) -> dict:
        """Get XHS user public info."""
        raise NotImplementedError("Xiaohongshu API not yet implemented")
