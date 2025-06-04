"""
User interfaces for Vigia medical detection system.
Includes Slack bot, web UI, and other interactive interfaces.
"""

from .slack_interface import SlackInterface
from .web_interface import WebInterface

__all__ = [
    "SlackInterface",
    "WebInterface",
]