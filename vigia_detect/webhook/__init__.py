"""
Webhook system for Vigia medical detection notifications.

This module provides a flexible webhook infrastructure to send detection results
to any external system without dependencies on specific frameworks.
"""

from .client import WebhookClient
from .server import WebhookServer
from .models import (
    WebhookEvent, 
    WebhookResponse,
    EventType,
    Severity,
    Detection,
    DetectionPayload,
    PatientInfo
)
from .handlers import WebhookHandlers as WebhookHandler, create_default_handlers

__all__ = [
    # Client
    'WebhookClient',
    
    # Server
    'WebhookServer',
    
    # Models
    'WebhookEvent',
    'WebhookResponse',
    'EventType',
    'Severity',
    'Detection',
    'DetectionPayload',
    'PatientInfo',
    
    # Handlers
    'WebhookHandlers',
    'create_default_handlers'
]