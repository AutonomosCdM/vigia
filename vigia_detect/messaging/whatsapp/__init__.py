"""
LPP-Detect WhatsApp Integration Package

Este subpaquete contiene los componentes específicos para la
integración con WhatsApp vía Twilio.

Componentes principales:
- Processor: Procesa imágenes recibidas de WhatsApp
- Server: Servidor HTTP para manejar webhooks de WhatsApp
"""

from vigia_detect.messaging.whatsapp.processor import (
    process_whatsapp_image,
    download_image,
    format_detection_results
)
from vigia_detect.messaging.whatsapp.server import (
    start_server,
    app,
    whatsapp_webhook
)

__all__ = [
    'process_whatsapp_image',
    'download_image',
    'format_detection_results',
    'start_server',
    'app',
    'whatsapp_webhook'
]
