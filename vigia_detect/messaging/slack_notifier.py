"""
Cliente Slack refactorizado usando BaseClient y templates centralizados.
"""
from typing import Dict, Any, Optional, List
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Importar módulos centralizados
from ..core.base_client import BaseClient
from ..core.slack_templates import SlackMessageTemplates
from ..core.constants import SlackChannels, LPP_SEVERITY_ALERTS


class SlackNotifierRefactored(BaseClient):
    """
    Servicio de notificaciones Slack mejorado.
    Usa BaseClient para configuración y templates centralizados para mensajes.
    """
    
    def __init__(self, channel: Optional[str] = None):
        """
        Inicializa el notificador de Slack.
        
        Args:
            channel: Canal por defecto (opcional, usa config si no se especifica)
        """
        # Variables requeridas para Slack
        required_vars = {
            'bot_token': 'SLACK_BOT_TOKEN',
            'signing_secret': 'SLACK_SIGNING_SECRET'
        }
        
        # Variables opcionales
        optional_vars = {
            'default_channel': 'SLACK_CHANNEL_LPP',
            'vigia_channel': 'SLACK_CHANNEL_VIGIA'
        }
        
        super().__init__(
            service_name="Slack",
            required_env_vars=required_vars,
            optional_env_vars=optional_vars
        )
        
        # Canal por defecto
        self.channel = channel or self.default_channel or SlackChannels.PROJECT_LPP
    
    def _initialize_client(self):
        """Inicializa el cliente Slack"""
        try:
            self.client = WebClient(token=self.bot_token)
            # Verificar autenticación
            auth_response = self.client.auth_test()
            self.bot_user_id = auth_response['user_id']
            self.log_info(f"Slack client authenticated as {auth_response['user']}")
        except SlackApiError as e:
            self.log_error("Failed to initialize Slack client", e)
            raise
    
    def health_check(self) -> bool:
        """Verifica que el cliente Slack esté funcionando"""
        try:
            response = self.client.auth_test()
            return response['ok']
        except Exception as e:
            self.log_error("Slack health check failed", e)
            return False
    
    def send_lpp_alert(self,
                      severity: int,
                      patient_id: str,
                      detection_details: Dict[str, Any],
                      channel: Optional[str] = None,
                      image_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Envía alerta de detección de LPP.
        
        Args:
            severity: Grado de severidad (0-4)
            patient_id: ID del paciente
            detection_details: Detalles de la detección
            channel: Canal específico (opcional)
            image_url: URL de imagen (opcional)
            
        Returns:
            Dict con resultado del envío
        """
        try:
            # Usar canal especificado o default
            target_channel = channel or self.channel
            
            # Generar ID de caso único
            from datetime import datetime
            case_id = f"LPP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # Extraer detalles
            location = detection_details.get('location', 'No especificada')
            confidence = detection_details.get('confidence', 0.0)
            patient_name = detection_details.get('patient_name', f'Paciente {patient_id}')
            service = detection_details.get('service', 'No especificado')
            bed = detection_details.get('bed', 'No especificada')
            emotional_analysis = detection_details.get('emotional_analysis')
            
            # Crear mensaje usando template centralizado
            message_data = SlackMessageTemplates.alerta_lpp(
                grado=severity,
                paciente=patient_name,
                id_caso=case_id,
                ubicacion=location,
                confianza=confidence,
                servicio=service,
                cama=bed,
                imagen_url=image_url,
                analisis_emocional=emotional_analysis
            )
            
            # Enviar mensaje
            response = self.client.chat_postMessage(
                channel=target_channel,
                text=f"🚨 Nueva detección LPP Grado {severity} - {patient_name}",
                **message_data
            )
            
            self.log_info(f"LPP alert sent to {target_channel}. Case ID: {case_id}")
            
            return {
                'success': True,
                'case_id': case_id,
                'channel': target_channel,
                'timestamp': response['ts'],
                'message_data': message_data
            }
            
        except SlackApiError as e:
            self.log_error(f"Slack API error sending alert", e)
            return {
                'success': False,
                'error': str(e),
                'error_code': e.response.get('error')
            }
        except Exception as e:
            self.log_error(f"Unexpected error sending alert", e)
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_simple_message(self,
                           text: str,
                           channel: Optional[str] = None,
                           blocks: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Envía un mensaje simple a Slack.
        
        Args:
            text: Texto del mensaje
            channel: Canal destino
            blocks: Bloques de Slack (opcional)
            
        Returns:
            Dict con resultado
        """
        try:
            target_channel = channel or self.channel
            
            params = {
                'channel': target_channel,
                'text': text
            }
            
            if blocks:
                params['blocks'] = blocks
            
            response = self.client.chat_postMessage(**params)
            
            return {
                'success': True,
                'timestamp': response['ts'],
                'channel': target_channel
            }
            
        except Exception as e:
            self.log_error("Error sending simple message", e)
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_message(self,
                      channel: str,
                      timestamp: str,
                      text: Optional[str] = None,
                      blocks: Optional[List[Dict]] = None) -> bool:
        """
        Actualiza un mensaje existente.
        
        Args:
            channel: Canal del mensaje
            timestamp: Timestamp del mensaje original
            text: Nuevo texto
            blocks: Nuevos bloques
            
        Returns:
            True si se actualizó correctamente
        """
        try:
            params = {
                'channel': channel,
                'ts': timestamp
            }
            
            if text:
                params['text'] = text
            if blocks:
                params['blocks'] = blocks
            
            self.client.chat_update(**params)
            self.log_info(f"Message updated in {channel}")
            return True
            
        except Exception as e:
            self.log_error("Error updating message", e)
            return False
    
    def add_reaction(self,
                    channel: str,
                    timestamp: str,
                    reaction: str) -> bool:
        """
        Agrega una reacción a un mensaje.
        
        Args:
            channel: Canal del mensaje
            timestamp: Timestamp del mensaje
            reaction: Emoji de reacción (sin :)
            
        Returns:
            True si se agregó correctamente
        """
        try:
            self.client.reactions_add(
                channel=channel,
                timestamp=timestamp,
                name=reaction
            )
            return True
        except Exception as e:
            self.log_error(f"Error adding reaction {reaction}", e)
            return False
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información de un usuario.
        
        Args:
            user_id: ID del usuario de Slack
            
        Returns:
            Dict con información del usuario o None
        """
        try:
            response = self.client.users_info(user=user_id)
            if response['ok']:
                return response['user']
            return None
        except Exception as e:
            self.log_error(f"Error getting user info for {user_id}", e)
            return None
    
    def send_ephemeral(self,
                      channel: str,
                      user: str,
                      text: str,
                      blocks: Optional[List[Dict]] = None) -> bool:
        """
        Envía un mensaje efímero (solo visible para un usuario).
        
        Args:
            channel: Canal
            user: ID del usuario
            text: Texto del mensaje
            blocks: Bloques opcionales
            
        Returns:
            True si se envió correctamente
        """
        try:
            params = {
                'channel': channel,
                'user': user,
                'text': text
            }
            
            if blocks:
                params['blocks'] = blocks
            
            self.client.chat_postEphemeral(**params)
            return True
            
        except Exception as e:
            self.log_error("Error sending ephemeral message", e)
            return False


# Función helper para migración
def migrate_from_old_notifier():
    """
    Ejemplo de cómo migrar del notificador antiguo.
    """
    # Antiguo
    # from vigia_detect.messaging.slack_notifier import SlackNotifier
    # notifier = SlackNotifier()
    
    # Nuevo
    notifier = SlackNotifierRefactored()
    
    # La API es similar pero mejorada
    # Ahora usa templates centralizados y mejor manejo de errores
    return notifier


if __name__ == "__main__":
    # Ejemplo de uso
    try:
        notifier = SlackNotifierRefactored()
        
        # Health check
        if notifier.health_check():
            print("✅ Conexión con Slack establecida")
            
            # Enviar alerta de prueba
            result = notifier.send_lpp_alert(
                severity=2,
                patient_id="TEST-001",
                detection_details={
                    'location': 'Sacro',
                    'confidence': 0.92,
                    'patient_name': 'Paciente de Prueba',
                    'service': 'UCI',
                    'bed': '101-A'
                }
            )
            
            if result['success']:
                print(f"✅ Alerta enviada. Case ID: {result['case_id']}")
            else:
                print(f"❌ Error: {result['error']}")
                
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        print("Por favor, configura SLACK_BOT_TOKEN en tu archivo .env")


# Legacy alias for backward compatibility
SlackNotifier = SlackNotifierRefactored