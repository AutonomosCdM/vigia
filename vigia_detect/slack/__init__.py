"""
Slack integration module for Vigía medical system
Provides Block Kit medical components and MCP integration
"""

from .block_kit_medical import BlockKitMedical, BlockKitInteractions

__all__ = [
    'BlockKitMedical',
    'BlockKitInteractions'
]