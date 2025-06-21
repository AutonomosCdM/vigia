# Módulo WhatsApp Aislado - Arquitectura y Funcionamiento

## Principio Fundamental: Zero Medical Knowledge

El módulo WhatsApp está completamente aislado del conocimiento médico siguiendo los principios de la arquitectura de 3 capas de Vigia. **NO procesa imágenes**, solo las **recibe y empaqueta** para enviarlas al "cerebro" del sistema.

## Cómo funciona el módulo WhatsApp aislado

### 1. **Recepción (isolated_bot.py)**
- Recibe webhook de Twilio con mensaje/imagen de WhatsApp
- **NO analiza** el contenido médico
- **NO interpreta** las imágenes
- Solo valida:
  - Formato técnico (JPG, PNG, MP4)
  - Tamaño máximo (10MB)
  - Estructura del webhook

### 2. **Empaquetado (input_packager.py)**
El bot crea un paquete estandarizado con:
```python
{
    'session_id': 'VIGIA_SESSION_20250106_103045_abc123',
    'timestamp': '2025-01-06T10:30:45Z',
    'input_type': 'image',  # o 'text', 'video', 'mixed'
    'raw_content': {
        'text': 'Mensaje del usuario',
        'media_url': 'https://twilio.com/image.jpg',  # URL de la imagen
        'media_type': 'image/jpeg',
        'from_number': '+56912345678',
        'to_number': '+56987654321'
    },
    'metadata': {
        'source': 'whatsapp',
        'format': 'image/jpeg',
        'size': 1048576,
        'checksum': 'sha256hash...',
        'has_media': true,
        'has_text': true
    },
    'audit_trail': {
        'received_at': '2025-01-06T10:30:45Z',
        'source_id': 'hash_anonimizado_del_numero',
        'processing_id': 'uuid-único'
    }
}
```

### 3. **Envío al Cerebro (input_queue.py)**
- El paquete se **encripta** con Fernet
- Se coloca en una cola Redis temporal
- Tiene timeout de 15 minutos
- Espera a que el "cerebro" (medical_dispatcher) lo procese

### 4. **Aislamiento Total**
El módulo WhatsApp:
- ❌ **NO descarga** la imagen
- ❌ **NO la procesa** con visión computacional
- ❌ **NO extrae** características médicas
- ❌ **NO toma** decisiones clínicas
- ✅ **Solo pasa la URL** de la imagen al siguiente nivel

### 5. **El Cerebro Procesa**
Es el **medical_dispatcher** y los sistemas especializados quienes:
- Descargan la imagen desde la URL
- Ejecutan el modelo YOLO para detectar LPP
- Analizan con MedGemma
- Toman decisiones médicas

## Analogía: El Recepcionista del Hospital

Este módulo funciona como un **recepcionista** en un hospital:
- Recibe al paciente con sus documentos
- Verifica que los papeles estén en orden (formato correcto)
- Les da un número de atención (session_id)
- Los envía a la sala de espera (input_queue)
- **NO examina** al paciente ni hace diagnósticos

## Garantías de Seguridad

Esta arquitectura garantiza que si el módulo WhatsApp es comprometido, **no puede acceder a información médica** porque literalmente no tiene esa capacidad. No tiene:
- Acceso a bases de datos médicas
- Capacidad de interpretar imágenes
- Conocimiento de protocolos médicos
- Acceso a historiales de pacientes

## Flujo de Datos

```
WhatsApp Usuario → Twilio Webhook → isolated_bot.py
                                           ↓
                                    Valida formato
                                           ↓
                                    input_packager.py
                                           ↓
                                    Crea paquete estandarizado
                                           ↓
                                    input_queue.py
                                           ↓
                                    Encripta y almacena
                                           ↓
                                    medical_dispatcher.py (Capa 2)
                                           ↓
                                    Procesamiento médico real
```

## Archivos del Módulo

- `isolated_bot.py`: Bot principal con zero conocimiento médico
- `processor.py`: Procesador de mensajes (coordina con otras capas)
- `server.py`: Servidor FastAPI para recibir webhooks
- `tests/`: Tests unitarios del módulo

## Configuración Requerida

Variables de entorno necesarias:
- `TWILIO_ACCOUNT_SID`: ID de cuenta Twilio
- `TWILIO_AUTH_TOKEN`: Token de autenticación
- `WHATSAPP_FROM_NUMBER`: Número de WhatsApp Business
- `REDIS_URL`: URL de Redis para la cola temporal

## Uso

```bash
# Iniciar el servidor WhatsApp
./start_whatsapp_server.sh

# El servidor escucha webhooks en:
# POST /webhook/whatsapp
```

## Principios de Diseño

1. **Separación de Responsabilidades**: Este módulo SOLO maneja entrada/salida
2. **Sin Estado**: No mantiene información entre mensajes
3. **Sin Decisiones**: No toma ninguna decisión médica
4. **Trazabilidad**: Todo se audita sin exponer PII
5. **Temporal**: Los datos se eliminan automáticamente después de 15 minutos