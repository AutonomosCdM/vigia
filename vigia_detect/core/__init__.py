"""Core module for shared functionality."""

from .base_client import BaseClient
from .constants import *
from .unified_image_processor import UnifiedImageProcessor as ImageProcessor
from .slack_templates import (
    create_detection_notification_data,
    create_error_notification_data,
    create_patient_history_notification_data,
    MedicalNotificationTemplates,
    MedicalAlertTemplates,
)

__all__ = [
    "BaseClient",
    "ImageProcessor",
    "create_detection_notification_data",
    "create_error_notification_data", 
    "create_patient_history_notification_data",
    "MedicalNotificationTemplates",
    "MedicalAlertTemplates",
]