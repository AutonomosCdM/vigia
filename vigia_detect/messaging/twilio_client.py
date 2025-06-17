"""
Cliente Twilio refactorizado usando BaseClient
Este es un ejemplo de cómo debería verse el cliente usando la clase base
"""
import os
from typing import Dict, Optional, Union
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Importar la clase base
from ..core.base_client import BaseClient


class TwilioClientRefactored(BaseClient):
    """
    Cliente Twilio mejorado que extiende BaseClient.
    Elimina duplicación de código de inicialización y logging.
    """
    
    def __init__(self):
        """Inicializa el cliente Twilio con las credenciales necesarias"""
        # Definir variables requeridas y opcionales
        required_vars = {
            'account_sid': 'TWILIO_ACCOUNT_SID',
            'auth_token': 'TWILIO_AUTH_TOKEN',
            'whatsapp_from': 'TWILIO_WHATSAPP_FROM'
        }
        
        optional_vars = {
            'phone_from': 'TWILIO_PHONE_FROM',
            'status_callback': 'TWILIO_STATUS_CALLBACK_URL'
        }
        
        # Inicializar usando la clase base
        super().__init__(
            service_name="Twilio",
            required_env_vars=required_vars,
            optional_env_vars=optional_vars
        )
    
    def _initialize_client(self):
        """Inicializa el cliente Twilio específico"""
        try:
            self.client = Client(self.account_sid, self.auth_token)
            self.log_info("Twilio client initialized successfully")
        except Exception as e:
            self.log_error("Failed to initialize Twilio client", e)
            raise
    
    def health_check(self) -> bool:
        """Verifica que el cliente Twilio esté funcionando"""
        try:
            # Intentar obtener información de la cuenta
            account = self.client.api.accounts(self.account_sid).fetch()
            self.log_info(f"Twilio health check passed. Account status: {account.status}")
            return account.status == 'active'
        except Exception as e:
            self.log_error("Twilio health check failed", e)
            return False
    
    def send_whatsapp(self, 
                     to_number: str, 
                     message: str,
                     media_url: Optional[str] = None) -> Dict[str, Union[str, bool]]:
        """
        Envía mensaje de WhatsApp.
        
        Args:
            to_number: Número destino (con código de país)
            message: Texto del mensaje
            media_url: URL de media adjunta (opcional)
            
        Returns:
            Dict con resultado del envío
        """
        try:
            # Validar y formatear número
            formatted_to = self._format_whatsapp_number(to_number)
            
            # Preparar parámetros del mensaje
            msg_params = {
                'from_': self.whatsapp_from,
                'to': formatted_to,
                'body': message
            }
            
            # Agregar media si existe
            if media_url:
                msg_params['media_url'] = [media_url]
            
            # Agregar callback si está configurado
            if self.status_callback:
                msg_params['status_callback'] = self.status_callback
            
            # Enviar mensaje
            message_instance = self.client.messages.create(**msg_params)
            
            self.log_info(f"WhatsApp sent successfully. SID: {message_instance.sid}")
            
            return {
                'success': True,
                'sid': message_instance.sid,
                'status': message_instance.status,
                'to': formatted_to
            }
            
        except TwilioRestException as e:
            self.log_error(f"Twilio error sending WhatsApp to {to_number}", e)
            return {
                'success': False,
                'error': str(e),
                'error_code': e.code
            }
        except Exception as e:
            self.log_error(f"Unexpected error sending WhatsApp", e)
            return {
                'success': False,
                'error': str(e)
            }
    
    def send_sms(self, 
                to_number: str, 
                message: str) -> Dict[str, Union[str, bool]]:
        """
        Envía SMS regular.
        
        Args:
            to_number: Número destino
            message: Texto del mensaje
            
        Returns:
            Dict con resultado del envío
        """
        if not self.phone_from:
            return {
                'success': False,
                'error': 'SMS phone number not configured'
            }
        
        try:
            message_instance = self.client.messages.create(
                from_=self.phone_from,
                to=to_number,
                body=message
            )
            
            self.log_info(f"SMS sent successfully. SID: {message_instance.sid}")
            
            return {
                'success': True,
                'sid': message_instance.sid,
                'status': message_instance.status
            }
            
        except TwilioRestException as e:
            self.log_error(f"Error sending SMS to {to_number}", e)
            return {
                'success': False,
                'error': str(e),
                'error_code': e.code
            }
    
    def get_message_status(self, message_sid: str) -> Optional[str]:
        """Obtiene el estado de un mensaje enviado"""
        try:
            message = self.client.messages(message_sid).fetch()
            return message.status
        except Exception as e:
            self.log_error(f"Error fetching message status for {message_sid}", e)
            return None
    
    @staticmethod
    def _format_whatsapp_number(number: str) -> str:
        """Formatea número para WhatsApp"""
        if not number.startswith('whatsapp:'):
            number = f'whatsapp:{number}'
        return number
    
    @staticmethod
    def validate_phone_number(number: str) -> bool:
        """Valida formato de número telefónico"""
        # Remover el prefijo whatsapp: si existe
        clean_number = number.replace('whatsapp:', '')
        
        # Verificar que tenga formato internacional
        return (clean_number.startswith('+') and 
                clean_number[1:].replace(' ', '').isdigit() and
                len(clean_number) >= 10)


# Ejemplo de uso
if __name__ == "__main__":
    # El cliente ahora maneja automáticamente:
    # 1. Carga de variables de entorno
    # 2. Validación de credenciales
    # 3. Logging estandarizado
    # 4. Manejo de errores consistente
    
    try:
        client = TwilioClientRefactored()
        
        # Health check
        if client.health_check():
            print("✅ Cliente Twilio funcionando correctamente")
            
            # Ejemplo de envío
            result = client.send_whatsapp(
                to_number="+56912345678",
                message="Test desde cliente refactorizado"
            )
            
            if result['success']:
                print(f"✅ Mensaje enviado: {result['sid']}")
            else:
                print(f"❌ Error: {result['error']}")
                
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        print("Por favor, configura las variables de entorno necesarias en .env")

# Backward compatibility alias
TwilioClient = TwilioClientRefactored