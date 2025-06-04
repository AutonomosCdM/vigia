"""
Vigia Detect - Medical Detection System for Pressure Injuries (LPP)

This package provides:
- Computer vision detection for pressure injuries
- Medical protocol integration with Redis caching
- Messaging integrations (WhatsApp, Slack)
- Webhook system for external integrations
- Patient data management with Supabase
"""

__version__ = "1.0.0"
__author__ = "Vigia Team"

# Core components
from .core import (
    constants,
    image_processor,
    slack_templates,
    BaseClient,
)

# Database
from .db import SupabaseClient

# Messaging
from .messaging import (
    SlackNotifier,
    TwilioClient,
    WhatsAppProcessor,
)

# Computer Vision
from .cv_pipeline import (
    Detector,
    Preprocessor,
    YOLOLoader,
)

# Redis Layer
from .redis_layer import (
    create_redis_client,
    RedisClient,
    CacheService,
    VectorService,
)

# Webhook System
from .webhook import (
    WebhookClient,
    WebhookServer,
    WebhookEvent,
    WebhookHandler,
)

# CLI Tools
from .cli import process_images

# Agents
from .agents import LPPMedicalAgent

# Interfaces
from .interfaces import (
    SlackInterface,
    WebInterface,
)

__all__ = [
    # Version info
    "__version__",
    "__author__",
    
    # Core
    "constants",
    "image_processor", 
    "slack_templates",
    "BaseClient",
    
    # Database
    "SupabaseClient",
    
    # Messaging
    "SlackNotifier",
    "TwilioClient", 
    "WhatsAppProcessor",
    
    # CV Pipeline
    "Detector",
    "Preprocessor",
    "YOLOLoader",
    
    # Redis
    "create_redis_client",
    "RedisClient",
    "CacheService", 
    "VectorService",
    
    # Webhook
    "WebhookClient",
    "WebhookServer",
    "WebhookEvent",
    "WebhookHandler",
    
    # CLI
    "process_images",
    
    # Agents
    "LPPMedicalAgent",
    
    # Interfaces
    "SlackInterface",
    "WebInterface",
]