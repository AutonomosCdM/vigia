#!/usr/bin/env python3
"""
Servidor de WhatsApp simplificado para Render - Solo simulación
"""

import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import logging
import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('vigia-whatsapp-simple')

app = Flask(__name__)

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """Webhook principal de WhatsApp con solo simulación"""
    try:
        twiml_response = MessagingResponse()
        
        # Obtener datos del mensaje
        from_number = request.values.get('From', '').replace('whatsapp:', '')
        body = request.values.get('Body', '')
        num_media = int(request.values.get('NumMedia', 0))
        
        logger.info(f"Mensaje recibido de {from_number}: {body[:50]}...")
        logger.info(f"NumMedia: {num_media}")
        
        # Verificar si hay medios adjuntos
        if num_media > 0:
            media_url = request.values.get('MediaUrl0', '')
            media_type = request.values.get('MediaContentType0', '')
            
            logger.info(f"Media URL: {media_url}")
            logger.info(f"Media Type: {media_type}")
            
            if media_type and media_type.startswith('image/'):
                logger.info("Procesando imagen con simulación...")
                
                # Respuesta simulada siempre
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
                
                twiml_response.message(fake_message)
                logger.info("✅ Respuesta simulada enviada exitosamente")
                
                # Notificación a Slack simplificada
                try:
                    slack_token = os.getenv('SLACK_BOT_TOKEN')
                    if slack_token:
                        from slack_sdk import WebClient
                        slack_client = WebClient(token=slack_token)
                        
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
                        slack_client.chat_postMessage(
                            channel="C08TJHZFVD1",  # Canal #vigia
                            text=slack_message,
                            mrkdwn=True
                        )
                        logger.info("✅ Notificación enviada a Slack")
                    else:
                        logger.info("Slack token no configurado")
                except Exception as e:
                    logger.error(f"Error enviando a Slack: {e}")
                    
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
        
        return str(twiml_response)
        
    except Exception as e:
        logger.error(f"Error en webhook: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Siempre devolver respuesta válida a Twilio
        resp = MessagingResponse()
        resp.message("Error en el procesamiento. Por favor intenta de nuevo.")
        return str(resp)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return {
        "service": "whatsapp-webhook-simple",
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "version": "1.0.0"
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5005))
    print(f"Iniciando servidor webhook simplificado en puerto {port}...")
    print("Para salir, presiona CTRL+C")
    app.run(host='0.0.0.0', port=port, debug=True)