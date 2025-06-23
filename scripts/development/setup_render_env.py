#!/usr/bin/env python3
"""
Script para configurar variables de entorno en Render manualmente.
Carga las credenciales desde .env.local de forma segura.
"""

import os
from dotenv import load_dotenv

# Cargar variables desde .env.local
load_dotenv('.env.local')

# Variables de entorno necesarias
env_vars = {
    "TWILIO_ACCOUNT_SID": os.getenv("TWILIO_ACCOUNT_SID", ""),
    "TWILIO_AUTH_TOKEN": os.getenv("TWILIO_AUTH_TOKEN", ""),
    "TWILIO_WHATSAPP_FROM": os.getenv("TWILIO_WHATSAPP_FROM", ""),
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
    "SUPABASE_URL": os.getenv("SUPABASE_URL", ""),
    "SUPABASE_KEY": os.getenv("SUPABASE_KEY", ""),
    "SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN", ""),
    "SLACK_CHANNEL_ID": "C08TJHZFVD1",  # Canal #vigia
    "PYTHON_VERSION": "3.11.0",
    "RATE_LIMIT_ENABLED": "true", 
    "RATE_LIMIT_PER_MINUTE": "30",
    "VIGIA_USE_MOCK_YOLO": "true"
}

print("🔧 Configuración de Variables de Entorno para Render")
print("=" * 60)
print()

# Verificar variables críticas
missing_vars = []
for key, value in env_vars.items():
    if not value and key not in ["SLACK_BOT_TOKEN", "PYTHON_VERSION", "RATE_LIMIT_ENABLED", "RATE_LIMIT_PER_MINUTE", "SLACK_CHANNEL_ID"]:
        missing_vars.append(key)

if missing_vars:
    print("⚠️  FALTAN VARIABLES CRÍTICAS:")
    for var in missing_vars:
        print(f"   - {var}")
    print("\n   Ejecuta: source scripts/quick_env_setup.sh")
    sys.exit(1)

print("📋 VARIABLES PARA RENDER:")
print()
print("1. Ve a: https://dashboard.render.com")
print("2. Haz clic en el servicio 'vigia-whatsapp'")
print("3. Ve a 'Environment' → 'Environment Variables'")
print("4. Haz clic en 'Add Environment Variable' o 'Bulk add'")
print("5. Copia y pega estas variables:")
print()
print("-" * 60)

# Crear archivo para copiar/pegar
with open("render_env_complete.txt", "w") as f:
    for key, value in env_vars.items():
        if value:
            f.write(f"{key}={value}\n")
            # Mostrar con máscara para seguridad
            if "TOKEN" in key or "KEY" in key:
                masked = value[:6] + "..." + value[-4:] if len(value) > 10 else "****"
                print(f"{key}={masked}")
            else:
                print(f"{key}={value}")

print("-" * 60)
print()
print("✅ Archivo 'render_env_complete.txt' creado con todas las variables")
print()
print("⚠️  NOTA SOBRE SLACK:")
if not env_vars.get("SLACK_BOT_TOKEN"):
    print("   - SLACK_BOT_TOKEN no está configurado")
    print("   - Las notificaciones a Slack NO funcionarán")
    print("   - Pero el procesamiento de WhatsApp SÍ funcionará")
    print("   - Para obtener el token: https://api.slack.com/apps")
else:
    print("   - SLACK_BOT_TOKEN configurado")
    print("   - Las notificaciones se enviarán al canal #vigia")

print("\n🚀 Una vez configuradas las variables:")
print("   1. El servicio se reiniciará automáticamente")
print("   2. Habilita el procesamiento real en el código")
print("   3. Prueba enviando una imagen por WhatsApp")