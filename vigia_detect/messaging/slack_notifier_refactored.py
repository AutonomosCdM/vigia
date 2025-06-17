"""
Compatibility module for slack_notifier_refactored imports.
This module provides backward compatibility during refactoring.
"""

# Import the new consolidated slack notifier
from .slack_notifier import SlackNotifierRefactored
# Create aliases for different import patterns
SlackNotifier = SlackNotifierRefactored

# Ensure backward compatibility
__all__ = ['SlackNotifierRefactored', 'SlackNotifier']