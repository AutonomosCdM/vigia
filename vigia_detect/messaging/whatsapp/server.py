"""
Servidor de Webhook para integración con WhatsApp.

Este módulo implementa un servidor Flask para manejar webhooks de Twilio WhatsApp
y se integra con el pipeline de Vigía para procesar imágenes y responder.
"""

import os
import sys
from flask import Flask, request, jsonify, make_response
from twilio.twiml.messaging_response import MessagingResponse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('vigia-detect.whatsapp.server')

# Cargar variables de entorno
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv no instalado, continuando sin cargar .env")
except Exception as e:
    logger.warning(f"Error cargando .env: {e}")

# Agregar directorio raíz al path para importaciones
# IMPORTANTE: Insertamos al final para evitar conflictos con YOLOv5
vigia_root = str(Path(__file__).resolve().parent.parent.parent)
if vigia_root not in sys.path:
    sys.path.append(vigia_root)

# Importar rate limiter
try:
    from vigia_detect.utils.rate_limiter import rate_limit_flask
    rate_limiter_available = True
    logger.info("Rate limiter importado correctamente")
except Exception as e:
    logger.error(f"Error importando rate limiter: {e}")
    rate_limiter_available = False

# Importar el cliente de Twilio
try:
    from vigia_detect.messaging.twilio_client import TwilioClient
    twilio_client = TwilioClient()
    logger.info("Cliente Twilio importado correctamente")
except Exception as e:
    logger.error(f"Error importando cliente Twilio: {e}")
    twilio_client = None

# Importar procesador de imágenes
try:
    from vigia_detect.messaging.whatsapp.processor import process_whatsapp_image
    processor_available = True
    logger.info("Procesador WhatsApp importado correctamente")
except Exception as e:
    logger.error(f"Error importando procesador WhatsApp: {e}")
    processor_available = False

# Importar SlackNotifier
slack_notifier = None
try:
    # Intentar importar directamente las funciones de Slack
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    import os
    
    slack_token = os.getenv('SLACK_BOT_TOKEN')
    if slack_token:
        slack_client = WebClient(token=slack_token)
        slack_notifier = slack_client
        logger.info("Slack client configurado correctamente")
    else:
        logger.warning("SLACK_BOT_TOKEN no configurado")
except Exception as e:
    logger.error(f"Error configurando Slack client: {e}")
    slack_notifier = None

# Inicializar Flask
app = Flask(__name__)

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """
    Endpoint para recibir mensajes de WhatsApp vía Twilio
    
    Returns:
        str: Respuesta TwiML para Twilio
    """
    try:
        # Inicializar respuesta TwiML
        twiml_response = MessagingResponse()
        
        # Obtener datos del mensaje
        from_number = request.values.get('From', '').replace('whatsapp:', '')
        body = request.values.get('Body', '')
        num_media = int(request.values.get('NumMedia', 0))
        
        logger.info(f"Mensaje recibido de {from_number}: {body[:50]}...")
        
        # Log completo de la solicitud para debugging
        logger.info(f"=== WEBHOOK REQUEST ===")
        logger.info(f"Form data: {dict(request.values)}")
        logger.info(f"From: {from_number}")
        logger.info(f"Body: {body}")
        logger.info(f"NumMedia: {num_media}")
        
        # Verificar si hay medios adjuntos
        if num_media > 0:
            logger.info(f"Medios detectados: {num_media}")
            
            # Fase piloto: Solo procesar la primera imagen
            media_url = request.values.get('MediaUrl0', '')
            media_type = request.values.get('MediaContentType0', '')
            
            logger.info(f"Media URL: {media_url}")
            logger.info(f"Media Type: {media_type}")
            
            if media_type and media_type.startswith('image/'):
                logger.info("Procesando imagen...")
                
                # En lugar de procesar sincrónicamente, vamos directo a la simulación
                # para evitar timeouts de Twilio
                if processor_available:  # Procesamiento habilitado
                    # Autenticar con Twilio para acceder al media_url
                    auth = (os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
                    
                    # Procesar imagen
                    result = process_whatsapp_image(media_url, auth)
                    
                    # Enviar respuesta
                    if result.get('success'):
                        if twilio_client:
                            twilio_client.send_whatsapp(from_number, result.get('message', ''))
                    else:
                        if twilio_client:
                            error_msg = "Error procesando la imagen. Por favor, intente nuevamente."
                            twilio_client.send_whatsapp(from_number, error_msg)
                else:
                    # Respuesta inmediata con análisis simulado
                    fake_message = """🔍 *Análisis de Vigia - Detección LPP*

📸 Imagen recibida y procesada

*Resultados preliminares (SIMULADO):*
• ✅ Lesión por Presión detectada
• 📊 Clasificación: Grado 2
• 📍 Región afectada: Sacro
• ⚡ Confianza: 85%

*Recomendación:* 
Consultar personal médico para evaluación inmediata.

_⚠️ Este es un sistema en fase piloto, la evaluación final siempre debe ser realizada por profesionales de salud._"""
                    
                    # Primero enviar respuesta a WhatsApp
                    twiml_response.message(fake_message)
                    
                    # Luego enviar notificación a Slack
                    if slack_notifier:
                        try:
                            # Crear mensaje para Slack
                            slack_message = f"""🚨 *Alerta de Detección LPP* 🚨
                            
*Fuente:* WhatsApp
*Teléfono:* {from_number}
*Hora:* {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

*Análisis (SIMULADO):*
• Lesión por Presión detectada
• Clasificación: Grado 2
• Región afectada: Sacro
• Confianza: 85%

*Recomendación:* Consultar personal médico para evaluación

*Imagen recibida:* {media_url}

_Este es un sistema en fase piloto, la evaluación final siempre debe ser realizada por profesionales de salud._
"""
                            # Enviar al canal vigia
                            response = slack_notifier.chat_postMessage(
                                channel="C08TJHZFVD1",  # ID del canal vigia
                                text=slack_message,
                                mrkdwn=True
                            )
                            logger.info("Notificación enviada a Slack exitosamente")
                        except SlackApiError as e:
                            logger.error(f"Error de Slack API: {e.response['error']}")
                        except Exception as e:
                            logger.error(f"Error enviando notificación a Slack: {e}")
            else:
                twiml_response.message("Solo se aceptan imágenes por el momento.")
        else:
            # Procesar comandos de texto
            if body.lower() == 'hola':
                twiml_response.message("¡Hola! Envía una imagen de lesión por presión para analizarla.")
            elif body.lower() == 'ayuda':
                twiml_response.message("LPP-Detect: Envía una imagen de la lesión por presión para recibir análisis. Escribe 'info' para más información.")
            elif body.lower() == 'info':
                twiml_response.message("LPP-Detect es un sistema para detección temprana de lesiones por presión. Envía una imagen clara de la lesión para recibir un análisis preliminar.")
            else:
                twiml_response.message("Comando no reconocido. Envía 'ayuda' para ver las opciones disponibles.")
        
        # Devolver respuesta TwiML
        return str(twiml_response)
        
    except Exception as e:
        logger.error(f"Error en webhook: {str(e)}")
        # Siempre devolver respuesta válida a Twilio
        resp = MessagingResponse()
        resp.message("Error en el procesamiento. Por favor intenta de nuevo.")
        return str(resp)

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    
    Returns:
        JSON response with server status
    """
    return jsonify({
        "status": "healthy",
        "service": "whatsapp-webhook",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

@app.route('/', methods=['GET'])
def index():
    """
    Página principal para verificar que el servidor está en ejecución
    
    Returns:
        str: Página HTML con información del estado del servidor
    """
    return """
    <html>
    <head>
        <title>LPP-Detect WhatsApp Server</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            h1 { color: #333; }
            .container { max-width: 800px; margin: 0 auto; }
            .status { padding: 15px; background-color: #d4edda; border-radius: 4px; color: #155724; }
            code { background-color: #f8f9fa; padding: 2px 4px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>LPP-Detect WhatsApp Server</h1>
            <div class="status">
                <strong>Estado:</strong> El servidor está en funcionamiento y listo para recibir webhooks.
            </div>
            <p>
                Configure el webhook de Twilio para apuntar a:
                <code>[su-dominio]/webhook/whatsapp</code>
            </p>
            <p>
                Para probar el servidor, envíe un mensaje WhatsApp al número configurado en Twilio.
            </p>
        </div>
    </body>
    </html>
    """

def start_server(port=5005):
    """
    Inicia el servidor Flask en el puerto especificado
    
    Args:
        port: Puerto en el que escuchará el servidor
    """
    print(f"Iniciando servidor webhook en puerto {port}...")
    print("Para salir, presiona CTRL+C")
    app.run(host='0.0.0.0', port=port, debug=True)
    logger.info(f"Servidor iniciado en puerto {port}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5005))
    start_server(port)
