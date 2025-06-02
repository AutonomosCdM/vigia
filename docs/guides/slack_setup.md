# Guía de Configuración de Slack para Vigía

## 📋 Requisitos Previos

1. Workspace de Slack con permisos de administrador
2. Python 3.8+ instalado
3. ngrok instalado (para desarrollo local)

## 🚀 Configuración Paso a Paso

### 1. Crear Slack App

1. Ve a [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click en "Create New App"
3. Selecciona "From scratch"
4. Nombre: "Vigía - Sistema LPP"
5. Selecciona tu workspace

### 2. Configurar Bot Token Scopes

En "OAuth & Permissions":

Agregar los siguientes **Bot Token Scopes**:
- `chat:write` - Enviar mensajes
- `chat:write.public` - Enviar mensajes a canales públicos
- `channels:read` - Leer información de canales
- `im:write` - Enviar mensajes directos
- `users:read` - Leer información de usuarios
- `files:write` - Subir archivos (imágenes de lesiones)

### 3. Instalar App en Workspace

1. En "OAuth & Permissions", click en "Install to Workspace"
2. Autoriza los permisos
3. Copia el **Bot User OAuth Token** (empieza con `xoxb-`)

### 4. Configurar Interactividad

En "Interactivity & Shortcuts":

1. Toggle "Interactivity" a **ON**
2. Request URL: 
   - Desarrollo: `https://[tu-ngrok-url].ngrok.io/slack/events`
   - Producción: `https://tu-dominio.com/slack/events`
3. Guardar cambios

### 5. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
# Copiar desde el ejemplo
cp config/.env.example .env
```

Edita `.env` y agrega:

```bash
SLACK_BOT_TOKEN=xoxb-tu-token-aqui
SLACK_SIGNING_SECRET=tu-signing-secret
SLACK_CHANNEL_LPP=ID-canal-lpp
SLACK_CHANNEL_VIGIA=ID-canal-vigia
```

### 6. Obtener IDs de Canales

En Slack:
1. Click derecho en el canal → "View channel details"
2. Scroll hasta el bottom
3. Copia el Channel ID

### 7. Iniciar Servidor de Desarrollo

```bash
# Dar permisos de ejecución
chmod +x scripts/start_slack_server.sh

# Iniciar servidor con ngrok
./scripts/start_slack_server.sh
```

El script:
- Iniciará el servidor Flask en puerto 5000
- Abrirá túnel ngrok automáticamente
- Mostrará la URL pública para configurar en Slack

### 8. Actualizar Request URL en Slack

1. Copia la URL de ngrok mostrada (ej: `https://abc123.ngrok.io`)
2. Ve a tu Slack App → "Interactivity & Shortcuts"
3. Actualiza Request URL: `https://abc123.ngrok.io/slack/events`
4. Verifica que muestre "Your URL works!" ✅

## 🧪 Probar la Integración

### Test 1: Enviar Mensaje de Prueba

```python
from vigia_detect.messaging.slack_notifier import SlackNotifier

notifier = SlackNotifier()
notifier.send_notification(
    severity=2,
    patient_id="TEST001",
    detection_details={
        "location": "Sacro",
        "confidence": 0.95
    }
)
```

### Test 2: Probar Botones

1. El mensaje aparecerá con 3 botones
2. Click en "Ver Historial Médico"
3. Debe abrir un modal con información del paciente

## 🐛 Troubleshooting

### "Token inválido"
- Verifica que el token empiece con `xoxb-`
- Reinstala la app en el workspace

### "Channel not found"
- Verifica los IDs de canal
- Asegúrate que el bot esté en el canal (`/invite @vigia`)

### Botones no responden
- Verifica que ngrok esté corriendo
- Confirma Request URL en Slack App
- Revisa logs del servidor

### Modal no abre
- Verifica `trigger_id` en los logs
- Confirma que tienes scope `views:open`

## 📱 Configuración de Producción

Para producción:

1. **SSL/HTTPS obligatorio**
```nginx
server {
    listen 443 ssl;
    server_name vigia.hospital.cl;
    
    location /slack/events {
        proxy_pass http://localhost:5000;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

2. **Variables de entorno seguras**
```bash
# Usar secrets manager
export SLACK_BOT_TOKEN=$(aws secretsmanager get-secret-value --secret-id vigia/slack/bot-token)
```

3. **Monitoreo**
```python
# Agregar health checks
@app.route('/health')
def health():
    return {"status": "ok", "timestamp": datetime.now()}
```

## 📚 Recursos Adicionales

- [Slack API Docs](https://api.slack.com/docs)
- [Block Kit Builder](https://app.slack.com/block-kit-builder)
- [Bolt Python Framework](https://slack.dev/bolt-python/)

## 🔐 Seguridad

⚠️ **IMPORTANTE**: 
- Nunca commits tokens en el código
- Usa variables de entorno siempre
- Regenera tokens si se exponen
- Valida firmas de Slack en producción