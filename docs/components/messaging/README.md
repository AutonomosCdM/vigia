# LPP-Detect Messaging Module Documentation

## Overview
Este módulo proporciona la integración de LPP-Detect con sistemas de mensajería, específicamente WhatsApp vía Twilio, para permitir a los usuarios enviar imágenes de lesiones por presión y recibir análisis automatizados. Su propósito principal es facilitar la comunicación bidireccional entre el sistema y los pacientes, así como integrar las notificaciones y resultados con plataformas internas como Slack. La arquitectura se basa en un cliente Twilio para la interacción con la API, un servidor de webhooks para recibir mensajes entrantes, procesadores dedicados para manejar el contenido (especialmente imágenes), y un sistema de plantillas para mensajes salientes.

## Key Features
- **Integración con WhatsApp**: Comunicación directa con usuarios a través de la plataforma WhatsApp.
- **Cliente Twilio**: Interfaz robusta para enviar mensajes de texto y plantillas.
- **Servidor de Webhooks**: Recepción y procesamiento en tiempo real de mensajes y media entrantes de Twilio.
- **Procesamiento de Media**: Manejo seguro y asíncrono de imágenes enviadas por los usuarios para su análisis.
- **Plantillas de Mensajes**: Uso de plantillas aprobadas para comunicaciones estructuradas y eficientes.
- **Manejo de Seguridad y Privacidad**: Consideraciones específicas para la protección de Información de Salud Protegida (PHI).
- **Integración con Slack**: Notificación de eventos y resultados a canales internos.

## Components
- **`twilio_client.py`**: Implementa la clase `TwilioClient` para interactuar con la API de Twilio, enviando mensajes de WhatsApp y manejando la estructura básica de los datos de webhook.
- **`whatsapp/server.py`**: Contiene la implementación del servidor HTTP (usando Flask) que escucha los webhooks entrantes de Twilio. Es responsable de recibir los datos, validarlos y pasarlos al procesador.
- **`whatsapp/processor.py`**: Encargado de procesar los mensajes entrantes, descargar y manejar la media adjunta (imágenes), interactuar con el pipeline de visión computacional y los agentes ADK, y coordinar las respuestas.
- **`templates/whatsapp_templates.py`**: Define y gestiona las plantillas de mensajes de WhatsApp aprobadas, incluyendo la estructura y los parámetros requeridos para cada una.
- **`utils/twilio_utils.py`**: Contiene funciones auxiliares para tareas como la validación de firmas de webhook, formato de números de teléfono, y otras utilidades relacionadas con la API de Twilio.

## Integration
El módulo de Messaging se integra con:
- **Pipeline de Visión Computacional (`cv_pipeline`)**: Envía imágenes recibidas de WhatsApp para su análisis y detección de LPP.
- **Agentes ADK**: Interactúa con agentes para tareas como el triage inicial, la generación de respuestas basadas en los resultados del CV, y la comunicación con Slack.
- **Módulo de Base de Datos (`db`)**: Almacena información relevante sobre las interacciones, usuarios y resultados del análisis.
- **Slack**: Envía notificaciones y resúmenes de casos para el equipo clínico.

El flujo típico de integración es:
WhatsApp (Usuario) → Twilio Webhook → `whatsapp/server.py` → `whatsapp/processor.py` → `cv_pipeline` / Agentes ADK / `db` / Slack → `whatsapp/processor.py` → `twilio_client.py` → WhatsApp (Usuario).

## Installation & Configuration
1. Clonar el repositorio LPP-Detect.
2. Instalar las dependencias de Python, incluyendo `flask`, `twilio`, `requests`, `python-dotenv`. Se recomienda usar un entorno virtual.
   ```bash
   pip install -r requirements.txt
   ```
3. Configurar las variables de entorno requeridas:
   - `TWILIO_ACCOUNT_SID`: SID de tu cuenta Twilio.
   - `TWILIO_AUTH_TOKEN`: Token de autenticación de tu cuenta Twilio.
   - `TWILIO_WHATSAPP_FROM`: Número de WhatsApp configurado en Twilio (ej: `+14155238886` para el sandbox).
   Se recomienda usar un archivo `.env` en la raíz del proyecto.
4. Configurar el webhook de Twilio para tu número de WhatsApp para apuntar a la URL pública de tu instancia del servidor de WhatsApp (`whatsapp/server.py`).

## Usage Examples
Para iniciar el servidor de WhatsApp:
```bash
# Desde el directorio raíz del proyecto
python lpp_detect/run_whatsapp.py
```
Esto iniciará el servidor Flask que escucha los webhooks de Twilio.

Para enviar un mensaje saliente (usando el cliente Twilio directamente):
```python
from lpp_detect.messaging import TwilioClient

client = TwilioClient()
to_number = "+56912345678" # Número del destinatario en formato E.164
message_body = "Hola, este es un mensaje de prueba."

try:
    message_sid = client.send_whatsapp(to_number, message_body)
    print(f"Mensaje enviado con SID: {message_sid}")
except Exception as e:
    print(f"Error al enviar mensaje: {e}")
```

## Security Considerations
- **Manejo de PHI**: Toda la información del paciente, especialmente las imágenes, debe tratarse como Información de Salud Protegida (PHI). Se deben implementar medidas estrictas para su almacenamiento, transmisión y procesamiento seguro, cumpliendo con las regulaciones de privacidad aplicables (ej: HIPAA si aplica).
- **Validación de Webhooks**: Es crucial validar la firma de las solicitudes de webhook entrantes de Twilio para asegurar que provienen de una fuente legítima y no han sido manipuladas. El módulo `utils/twilio_utils.py` debe incluir funciones para esta validación.
- **Almacenamiento Temporal**: Las imágenes y otros medios se almacenan temporalmente en el directorio `whatsapp/temp/`. Se deben implementar políticas de limpieza y seguridad para este directorio.
- **Credenciales**: Las credenciales de Twilio (`TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`) deben almacenarse de forma segura, preferiblemente usando variables de entorno y no hardcodeadas en el código.

## Development
Para el desarrollo y pruebas del módulo:
- Configurar las variables de entorno de Twilio.
- Utilizar el sandbox de Twilio para pruebas iniciales sin un número de WhatsApp aprobado.
- Implementar pruebas unitarias y de integración para el cliente Twilio, el procesador y el servidor.
- Considerar el uso de herramientas como `ngrok` para exponer el servidor local a internet y recibir webhooks de Twilio durante el desarrollo.
- Simular webhooks entrantes para probar el servidor y el procesador sin necesidad de enviar mensajes reales desde WhatsApp.
