"""
Vigia Detect - Medical Detection System for Pressure Injuries (LPP)

This package provides:
- Computer vision detection for pressure injuries
- Medical protocol integration with Redis caching
- Messaging integrations (WhatsApp, Slack)
- Webhook system for external integrations
- Patient data management with Supabase

IMPORTANTE: Los módulos son independientes. Importe directamente lo que necesite:
  from vigia_detect.ai.medgemma_client import MedGemmaClient
  from vigia_detect.core.triage_engine import MedicalTriageEngine
"""

__version__ = "1.0.0"
__author__ = "Vigia Team"

# NO IMPORTAR TODO AUTOMÁTICAMENTE - Los módulos deben ser independientes
# Cada módulo debe importarse explícitamente cuando se necesite

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