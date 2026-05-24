"""
Platform API integration package for KOL Matcher.

This package provides abstract base classes and concrete implementations
for integrating with social media platforms (Weibo, Xiaohongshu, Douyin, Bilibili).

Currently placeholders — real API integrations require developer credentials
from each platform's open platform.
"""

from .base import PlatformAPIBase

__all__ = ["PlatformAPIBase"]
