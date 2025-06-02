# LPP-Detect Messaging Module

Este módulo proporciona la integración de LPP-Detect con sistemas de mensajería, 
específicamente WhatsApp vía Twilio, para permitir a los usuarios enviar imágenes
de lesiones por presión y recibir análisis automatizados.

## Estructura

```
messaging/
├── __init__.py             # Exporta componentes principales
├── twilio_client.py        # Cliente Twilio para enviar/recibir mensajes
├── templates/              # Plantillas de mensajes
│   ├── __init__.py
│   └── whatsapp_templates.py
├── utils/                  # Utilidades para Twilio y WhatsApp
│   ├── __init__.py
│   └── twilio_utils.py
└── whatsapp/               # Integración específica con WhatsApp
    ├── __init__.py
    ├── processor.py        # Procesamiento de imágenes de WhatsApp
    ├── server.py           # Servidor de webhooks para WhatsApp
    └── temp/               # Directorio para archivos temporales
```

## Funcionalidades

- **Cliente Twilio**: Interfaz para enviar mensajes vía WhatsApp
- **Procesador de imágenes**: Recibe y analiza imágenes de WhatsApp
- **Servidor de webhooks**: Maneja interacciones en tiempo real
- **Plantillas**: Mensajes estructurados para comunicación con usuarios
- **Utilidades**: Funciones auxiliares para validación y seguridad

## Uso básico

Para iniciar el servidor de WhatsApp:

```bash
# Desde el directorio raíz del proyecto
python lpp_detect/run_whatsapp.py
```

Esto iniciará un servidor en el puerto 5005 (configurable) que manejará
webhooks de Twilio para WhatsApp.

## Configuración

Requiere las siguientes variables de entorno:

- `TWILIO_ACCOUNT_SID`: SID de la cuenta Twilio
- `TWILIO_AUTH_TOKEN`: Token de autenticación de Twilio
- `TWILIO_WHATSAPP_FROM`: Número de WhatsApp configurado en Twilio

Se recomienda usar un archivo `.env` para configurar estas variables.

## Dependencias

- Flask: Para el servidor de webhooks
- Twilio: SDK oficial para interactuar con API de Twilio
- Requests: Para descargar imágenes de WhatsApp
- python-dotenv: (Opcional) Para cargar variables de entorno desde .env

## Integración con LPP-Detect

Este módulo se integra con el pipeline de visión computacional de LPP-Detect
para procesar las imágenes recibidas y detectar lesiones por presión.
