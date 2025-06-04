"""
Messaging module for LPP-Detect system.
Contains Slack integration and notification services.
"""

from .slack_notifier_refactored import SlackNotifierRefactored as SlackNotifier

__all__ = ['SlackNotifier']
