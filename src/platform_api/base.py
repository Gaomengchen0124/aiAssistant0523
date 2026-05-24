"""
Abstract base class for platform API integrations.

Subclasses should implement send_private_message() for each platform.
"""

from abc import ABC, abstractmethod


class PlatformAPIBase(ABC):
    """Base class for social media platform API integrations."""

    def __init__(self, app_key: str, app_secret: str, access_token: str = ""):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = access_token

    @abstractmethod
    def send_private_message(self, recipient_id: str, message: str) -> dict:
        """
        Send a private/direct message to a user on the platform.

        Args:
            recipient_id: Platform-specific user ID or username
            message: Message content

        Returns:
            dict with keys: success (bool), message_id (str|None), error (str|None)
        """
        pass

    @abstractmethod
    def get_user_info(self, user_id: str) -> dict:
        """Get public info for a user."""
        pass

    def is_authenticated(self) -> bool:
        """Check if valid credentials are available."""
        return bool(self.app_key and self.app_secret and self.access_token)
