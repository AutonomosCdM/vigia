# LPP-Detect Messaging API Reference

Este documento detalla las interfaces de programación (API) de los componentes principales del módulo de messaging.

## TwilioClient

Clase principal para interactuar con la API de Twilio para enviar y recibir mensajes de WhatsApp.

**Ubicación:** `vigia_detect/messaging/twilio_client.py`

```python
class TwilioClient:
    def __init__(self):
        """
        Inicializa el cliente Twilio con credenciales de las variables de entorno.

        Requiere las variables de entorno `TWILIO_ACCOUNT_SID` y `TWILIO_AUTH_TOKEN`.
        Opcionalmente, `TWILIO_WHATSAPP_FROM` para especificar el número de origen (por defecto usa el sandbox de Twilio).

        Raises:
            ValueError: Si faltan las credenciales requeridas.
        """
        pass # Implementación detallada en el código fuente

    def send_whatsapp(self, to_number: str, message: str) -> str:
        """
        Envía un mensaje de texto de WhatsApp a un número específico.

        Args:
            to_number: Número de destino en formato E.164 (ej: +56912345678).
            message: Contenido del mensaje de texto a enviar.

        Returns:
            str: El SID (identificador único) del mensaje enviado por Twilio.

        Raises:
            Exception: Si ocurre un error durante el envío del mensaje a través de la API de Twilio.
        """
        pass # Implementación detallada en el código fuente

    def send_whatsapp_template(self, to_number: str, template_sid: str, params: Dict[str, Any]) -> str:
        """
        Envía un mensaje de WhatsApp basado en una plantilla pre-aprobada.

        Args:
            to_number: Número de destino en formato E.164.
            template_sid: El SID de la plantilla de mensaje aprobada en Twilio.
            params: Un diccionario con los parámetros necesarios para poblar la plantilla.

        Returns:
            str: El SID (identificador único) del mensaje de plantilla enviado por Twilio.

        Raises:
            Exception: Si ocurre un error durante el envío de la plantilla a través de la API de Twilio.
        """
        pass # Implementación detallada en el código fuente

    def handle_incoming_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa los datos de una solicitud webhook entrante de Twilio.

        Esta función parsea los datos crudos del webhook y extrae información clave
        como el remitente, el cuerpo del mensaje, y los detalles de los medios adjuntos.

        Args:
            data: Un diccionario que contiene los datos recibidos en la solicitud webhook de Twilio.

        Returns:
            Dict: Un diccionario con los datos del webhook procesados y estructurados.
                  Incluye 'sender', 'body', 'num_media', 'media_urls', y 'media_types'.
        """
        pass # Implementación detallada en el código fuente

    def validate_phone_number(self, number: str) -> bool:
        """
        Valida el formato básico de un número de teléfono.

        Realiza una validación simple para verificar si el número comienza con '+'
        seguido de dígitos. Para una validación más robusta, se recomienda usar
        la API Twilio Lookup.

        Args:
            number: El número de teléfono a validar.

        Returns:
            bool: True si el formato básico es válido, False en caso contrario.
        """
        pass # Implementación detallada en el código fuente

    # Método interno para formatear números de WhatsApp
    # def _format_whatsapp_number(self, number: str) -> str:
    #     """
    #     Asegura que el número tenga el formato correcto para WhatsApp (whatsapp:+E.164).
    #     """
    #     pass # Implementación detallada en el código fuente

```

## WhatsApp Processor

Funciones y/o clases encargadas de procesar los mensajes entrantes de WhatsApp, manejar la lógica de negocio, interactuar con otros módulos y coordinar las respuestas.

**Ubicación:** `vigia_detect/messaging/whatsapp/processor.py`

```python
# Ejemplo de función principal (la implementación exacta puede variar)
def process_whatsapp_message(webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Procesa un mensaje entrante de WhatsApp recibido a través del webhook de Twilio.

    Esta función maneja la lógica principal para mensajes entrantes:
    1. Extrae información relevante de los datos del webhook.
    2. Identifica si el mensaje contiene texto, media (imágenes), u otros tipos de contenido.
    3. Si hay imágenes, las descarga de forma segura.
    4. Interactúa con el pipeline de CV para analizar las imágenes.
    5. Utiliza agentes ADK para triage, interpretación de resultados y generación de respuestas.
    6. Almacena información relevante en la base de datos.
    7. Determina la respuesta adecuada para el usuario (texto, plantilla).
    8. Coordina el envío de la respuesta a través del TwilioClient.
    9. Notifica a Slack u otros sistemas internos si es necesario.

    Args:
        webhook_data: Diccionario con los datos procesados del webhook (salida de TwilioClient.handle_incoming_webhook).

    Returns:
        Optional[Dict[str, Any]]: Un diccionario con los detalles de la respuesta enviada al usuario,
                                   o None si no se envió una respuesta directa.
    """
    pass # Implementación detallada en el código fuente

# Otras funciones auxiliares pueden incluir:
# - download_media(url: str, content_type: str) -> str: Descarga un archivo multimedia.
# - analyze_image_with_cv(file_path: str) -> Dict[str, Any]: Envía imagen al pipeline de CV.
# - get_agent_response(analysis_results: Dict[str, Any]) -> Dict[str, Any]: Obtiene respuesta de agente ADK.
# - send_slack_notification(message: str): Envía notificación a Slack.
```

## WhatsApp Server

Módulo que implementa el servidor web para recibir las solicitudes de webhook de Twilio.

**Ubicación:** `vigia_detect/messaging/whatsapp/server.py`

```python
# Ejemplo de estructura (usando Flask)
# from flask import Flask, request, Response
# from twilio.twiml.messaging_response import MessagingResponse
# from vigia_detect.messaging.twilio_client import TwilioClient
# from vigia_detect.messaging.whatsapp.processor import process_whatsapp_message
# from vigia_detect.messaging.utils.twilio_utils import validate_twilio_request

# app = Flask(__name__)
# twilio_client = TwilioClient()

# @app.route("/webhook", methods=['POST'])
# def twilio_webhook():
#     """
#     Endpoint para recibir webhooks de Twilio.
#
#     Valida la solicitud, procesa los datos entrantes y coordina la respuesta.
#     """
#     # 1. Validar la solicitud de Twilio
#     # if not validate_twilio_request(request.data, request.headers.get('X-Twilio-Signature', ''), os.getenv('TWILIO_AUTH_TOKEN')):
#     #     return Response("Invalid signature", status=400)
#
#     # 2. Procesar los datos del webhook
#     # webhook_data = twilio_client.handle_incoming_webhook(request.form)
#
#     # 3. Procesar el mensaje con la lógica de negocio
#     # response_details = process_whatsapp_message(webhook_data)
#
#     # 4. Generar respuesta TwiML (si es necesario, aunque a menudo se responde directamente con la API)
#     # resp = MessagingResponse()
#     # if response_details and response_details.get('reply_text'):
#     #     resp.message(response_details['reply_text'])
#
#     # return Response(str(resp), mimetype="application/xml")
#
# # Función para iniciar el servidor
# # def run_server(port=5005):
# #     """Inicia el servidor Flask."""
# #     app.run(port=port, debug=True)
```

**Endpoints:**

- `/webhook` (POST): Recibe las notificaciones de mensajes entrantes y eventos de Twilio.

## Templates

Módulo que contiene las definiciones y la lógica para usar plantillas de mensajes de WhatsApp pre-aprobadas por Twilio.

**Ubicación:** `vigia_detect/messaging/templates/whatsapp_templates.py`

```python
# Ejemplo de estructura
# class WhatsAppTemplates:
#     """Gestiona las plantillas de mensajes de WhatsApp."""
#
#     # Definición de plantillas (ejemplo)
#     WELCOME_MESSAGE = {
#         "sid": "YOUR_WELCOME_TEMPLATE_SID",
#         "params": ["patient_name"]
#     }
#     ANALYSIS_RESULT_LOW = {
#         "sid": "YOUR_LOW_RISK_TEMPLATE_SID",
#         "params": ["patient_name", "result_details"]
#     }
#     # ... otras plantillas por nivel de gravedad o propósito
#
#     @staticmethod
#     def get_template(template_name: str) -> Dict[str, Any]:
#         """
#         Obtiene los detalles de una plantilla por su nombre.
#
#         Args:
#             template_name: Nombre interno de la plantilla (ej: "WELCOME_MESSAGE").
#
#         Returns:
#             Dict[str, Any]: Diccionario con el 'sid' y 'params' de la plantilla.
#
#         Raises:
#             ValueError: Si el nombre de la plantilla no existe.
#         """
#         pass # Implementación detallada en el código fuente
#
#     @staticmethod
#     def format_template_params(template_name: str, **kwargs) -> Dict[str, str]:
#         """
#         Formatea los parámetros para una plantilla específica.
#
#         Verifica que todos los parámetros requeridos por la plantilla estén presentes
#         y los formatea adecuadamente para la API de Twilio.
#
#         Args:
#             template_name: Nombre interno de la plantilla.
#             **kwargs: Parámetros clave-valor para la plantilla.
#
#         Returns:
#             Dict[str, str]: Diccionario de parámetros formateados para Twilio.
#
#         Raises:
#             ValueError: Si faltan parámetros requeridos.
#         """
#         pass # Implementación detallada en el código fuente
```

## Utilities

Funciones auxiliares para tareas comunes relacionadas con la integración de Twilio y WhatsApp.

**Ubicación:** `vigia_detect/messaging/utils/twilio_utils.py`

```python
# Ejemplo de funciones
# def validate_twilio_request(request_body: bytes, twilio_signature: str, auth_token: str) -> bool:
#     """
#     Valida la firma de una solicitud webhook de Twilio.
#
#     Asegura que la solicitud proviene de Twilio y no ha sido alterada.
#
#     Args:
#         request_body: El cuerpo crudo de la solicitud HTTP (bytes).
#         twilio_signature: El valor del encabezado 'X-Twilio-Signature'.
#         auth_token: Tu token de autenticación de Twilio.
#
#     Returns:
#         bool: True si la firma es válida, False en caso contrario.
#     """
#     pass # Implementación detallada en el código fuente

# def format_e164(phone_number: str) -> str:
#     """
#     Formatea un número de teléfono al estándar E.164.
#
#     Puede requerir lógica más compleja o integración con Twilio Lookup
#     para manejar diversos formatos de entrada.
#
#     Args:
#         phone_number: El número de teléfono en cualquier formato.
#
#     Returns:
#         str: El número de teléfono en formato E.164.
#
#     Raises:
#         ValueError: Si el número no puede ser formateado.
#     """
#     pass # Implementación detallada en el código fuente

# def download_file(url: str, destination_path: str) -> str:
#     """
#     Descarga un archivo desde una URL a una ruta local.
#
#     Utilizado para descargar imágenes u otros medios enviados por los usuarios.
#
#     Args:
#         url: La URL del archivo a descargar.
#         destination_path: La ruta completa donde guardar el archivo.
#
#     Returns:
#         str: La ruta completa del archivo descargado.
#
#     Raises:
#         Exception: Si la descarga falla.
#     """
#     pass # Implementación detallada en el código fuente
