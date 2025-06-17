"""Core module for shared functionality."""

from .base_client import BaseClient
from .constants import *
from .unified_image_processor import UnifiedImageProcessor as ImageProcessor
from .slack_templates import (
    create_detection_blocks,
    create_error_blocks,
    create_patient_history_blocks,
)

__all__ = [
    "BaseClient",
    "ImageProcessor",
    "create_detection_blocks",
    "create_error_blocks",
    "create_patient_history_blocks",
]