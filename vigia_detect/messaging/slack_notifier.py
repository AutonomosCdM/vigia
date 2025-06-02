"""
Slack Notifier for LPP-Detect Medical Alert System
Handles automated notifications to medical team via Slack based on LPP severity detection.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


class SlackNotifier:
    """
    Slack notification service for LPP medical alerts.
    Integrates with Google ADK agents to send severity-based notifications.
    """
    
    def __init__(self, bot_token: Optional[str] = None):
        """
        Initialize Slack client with bot token.
        
        Args:
            bot_token: Slack bot token. If None, reads from environment.
        """
        # Import settings from centralized config
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from config.settings import settings
        
        self.bot_token = bot_token or settings.slack_bot_token
        if not self.bot_token:
            raise ValueError("SLACK_BOT_TOKEN not configured. Please set it in .env file")
        
        self.client = WebClient(token=self.bot_token)
        
        # LPP severity mapping for medical alerts
        self.severity_alerts = {
            0: {
                'emoji': '✅',
                'level': 'INFO', 
                'message': 'Sin LPP detectada',
                'urgency': 'low'
            },
            1: {
                'emoji': '⚠️',
                'level': 'ATENCIÓN',
                'message': 'LPP Grado 1 - Eritema no blanqueable',
                'urgency': 'medium'
            },
            2: {
                'emoji': '🔶',
                'level': 'IMPORTANTE',
                'message': 'LPP Grado 2 - Úlcera superficial',
                'urgency': 'high'
            },
            3: {
                'emoji': '🚨',
                'level': 'CRÍTICO',
                'message': 'LPP Grado 3 - Úlcera profunda',
                'urgency': 'critical'
            },
            4: {
                'emoji': '🆘',
                'level': 'EMERGENCIA',
                'message': 'LPP Grado 4 - Úlcera hasta hueso/músculo',
                'urgency': 'emergency'
            }
        }
    
    def notificar_deteccion_lpp(self, canal: str, severidad: int, 
                               paciente_id: str, detalles: Dict) -> Dict:
        """
        Envía notificación de detección LPP al equipo médico.
        
        Args:
            canal: ID del canal Slack (#lpp-alerts o similar)
            severidad: Grado LPP (0-4) según clasificación EPUAP/NPIAP
            paciente_id: Identificador anonimizado del paciente
            detalles: Dict con confidence, timestamp, imagen_path, etc.
        
        Returns:
            Dict: {'status': 'success'|'error', 'response': response|error}
        """
        try:
            alert_info = self.severity_alerts.get(severidad, {
                'emoji': '❓',
                'level': 'DESCONOCIDO',
                'message': 'Clasificación pendiente',
                'urgency': 'unknown'
            })
            
            # Construir mensaje médico estructurado
            mensaje = self._construir_mensaje_medico(
                alert_info, paciente_id, severidad, detalles
            )
            
            # Enviar con priorización por urgencia
            response = self._enviar_mensaje_priorizado(
                canal, mensaje, alert_info['urgency']
            )
            
            logger.info(f"Notificación LPP enviada - Paciente: {paciente_id}, Severidad: {severidad}")
            return {'status': 'success', 'response': response}
            
        except SlackApiError as e:
            logger.error(f"Error Slack API: {e}")
            return {'status': 'error', 'error': str(e)}
        except Exception as e:
            logger.error(f"Error notificación LPP: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _construir_mensaje_medico(self, alert_info: Dict, paciente_id: str, 
                                 severidad: int, detalles: Dict) -> str:
        """Construye mensaje médico formateado según protocolos."""
        
        timestamp = detalles.get('timestamp', datetime.now().isoformat())
        confidence = detalles.get('confidence', 'N/A')
        ubicacion = detalles.get('ubicacion', 'No especificada')
        
        mensaje = f"{alert_info['emoji']} **{alert_info['level']}** - {alert_info['message']}\n\n"
        mensaje += f"**Paciente:** {paciente_id}\n"
        mensaje += f"**Severidad:** Grado {severidad}\n"
        mensaje += f"**Confianza:** {confidence}%\n"
        mensaje += f"**Ubicación anatómica:** {ubicacion}\n"
        mensaje += f"**Timestamp:** {timestamp}\n"
        
        # Agregar recomendaciones según severidad
        if severidad >= 3:
            mensaje += f"\n🏥 **ACCIÓN REQUERIDA:** Evaluación médica inmediata"
        elif severidad >= 1:
            mensaje += f"\n👩‍⚕️ **SEGUIMIENTO:** Revisar en próxima ronda"
        
        return mensaje
    
    def _enviar_mensaje_priorizado(self, canal: str, mensaje: str, urgencia: str) -> Dict:
        """Envía mensaje con priorización según urgencia médica."""
        
        # Configurar notificaciones según urgencia
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": mensaje
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ Atendido"
                        },
                        "style": "primary",
                        "action_id": "lpp_atendido"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "📋 Ver Detalles"
                        },
                        "action_id": "lpp_detalles"
                    }
                ]
            }
        ]
        
        return self.client.chat_postMessage(
            channel=canal,
            text=mensaje,
            blocks=blocks,
            unfurl_links=False,
            unfurl_media=False
        )
    
    def enviar_mensaje_test(self, canal: str) -> Dict:
        """
        Envía mensaje de prueba para verificar conectividad.
        
        Args:
            canal: Canal de Slack para testing
            
        Returns:
            Dict: Status de la operación
        """
        try:
            mensaje = "🔧 **Test LPP-Detect System**\nSistema de notificaciones operativo\nTimestamp: " + datetime.now().isoformat()
            
            response = self.client.chat_postMessage(
                channel=canal,
                text=mensaje
            )
            
            return {'status': 'success', 'response': response}
            
        except SlackApiError as e:
            return {'status': 'error', 'error': str(e)}
    
    def obtener_canales(self) -> Dict:
        """
        Obtiene lista de canales disponibles para configuración.
        
        Returns:
            Dict: Lista de canales o error
        """
        try:
            response = self.client.conversations_list(
                types="public_channel,private_channel"
            )
            
            canales = []
            for channel in response['channels']:
                canales.append({
                    'id': channel['id'],
                    'name': channel['name'],
                    'is_private': channel['is_private']
                })
            
            return {'status': 'success', 'canales': canales}
            
        except SlackApiError as e:
            return {'status': 'error', 'error': str(e)}


# ADK Tool Integration Functions
def enviar_notificacion_lpp_adk(canal: str, severidad: int, paciente_id: str, 
                               detalles: Dict) -> Dict:
    """
    ADK Tool function for sending LPP notifications.
    Designed to be registered as custom tool in Google ADK agents.
    
    Args:
        canal: Slack channel ID for medical alerts
        severidad: LPP severity grade (0-4)
        paciente_id: Anonymized patient identifier  
        detalles: Detection details dict with confidence, timestamp, etc.
    
    Returns:
        Dict: Operation status for ADK agent processing
    """
    notifier = SlackNotifier()
    return notifier.notificar_deteccion_lpp(canal, severidad, paciente_id, detalles)


def test_slack_connection(canal: str) -> Dict:
    """
    ADK Tool function for testing Slack connectivity.
    
    Args:
        canal: Slack channel for testing
        
    Returns:
        Dict: Connection test results
    """
    notifier = SlackNotifier()
    return notifier.enviar_mensaje_test(canal)
