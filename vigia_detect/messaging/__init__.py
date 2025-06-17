"""
Messaging module for LPP-Detect system.
Contains Slack integration and notification services.

IMPORTANTE: Los módulos son independientes y se importan solo cuando se necesitan.
"""

# Importaciones opcionales para evitar dependencias circulares
try:
    from .slack_notifier import SlackNotifierRefactored as SlackNotifier
except ImportError:
    SlackNotifier = None

try:
    from .twilio_client import TwilioClientRefactored as TwilioClient
except ImportError:
    TwilioClient = None

try:
    from .whatsapp.processor import WhatsAppProcessor
except ImportError:
    WhatsAppProcessor = None

# Solo exportar lo que se pudo importar
__all__ = []
if SlackNotifier: __all__.append('SlackNotifier')
if TwilioClient: __all__.append('TwilioClient')
if WhatsAppProcessor: __all__.append('WhatsAppProcessor')
