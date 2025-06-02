"""
Messaging module for LPP-Detect system.
Contains Slack integration and notification services.
"""

from .slack_notifier import SlackNotifier

__all__ = ['SlackNotifier']
