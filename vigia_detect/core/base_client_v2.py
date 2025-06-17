"""
Temporary compatibility module for base_client_v2 imports.
This module provides the old import path for backward compatibility during refactoring.
"""

# Import the new consolidated class and provide it under the old name
from .base_client import BaseClient as BaseClientV2

# Ensure backward compatibility
__all__ = ['BaseClientV2']