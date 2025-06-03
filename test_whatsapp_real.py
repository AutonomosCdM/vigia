#!/usr/bin/env python3
"""
Script para probar el sistema con WhatsApp real
"""
import os
import sys
import time
from datetime import datetime

# Cargar credenciales
from dotenv import load_dotenv
load_dotenv('.env.local')

print("🚀 Prueba del Sistema Vigia con WhatsApp Real\n")

print("📋 Configuración:")
print(f"- Número WhatsApp: {os.getenv('TWILIO_WHATSAPP_FROM', 'NO CONFIGURADO')}")
print(f"- Webhook URL: {os.getenv('WEBHOOK_URL', 'http://localhost:8000')}")
print(f"- Anthropic API: {'✅ Configurado' if os.getenv('ANTHROPIC_API_KEY') else '❌ NO CONFIGURADO'}")
print(f"- Supabase: {'✅ Configurado' if os.getenv('SUPABASE_URL') else '❌ NO CONFIGURADO'}")

print("\n📱 Instrucciones para la prueba:")
print("1. Asegúrate de que el servidor WhatsApp esté corriendo:")
print("   ./start_whatsapp_server.sh")
print("")
print("2. En tu WhatsApp, envía un mensaje al número:")
print(f"   {os.getenv('TWILIO_WHATSAPP_FROM', 'whatsapp:+13343104976')}")
print("")
print("3. Si es la primera vez, debes enviar el código de activación:")
print("   'join <código-sandbox>'")
print("")
print("4. Luego envía una imagen de prueba con el mensaje:")
print("   'Paciente CD-2025-001'")
print("")
print("5. El sistema debería:")
print("   - Confirmar recepción de la imagen")
print("   - Procesar y detectar lesiones")
print("   - Enviar resultados por WhatsApp")
print("   - Guardar en base de datos")
print("   - Notificar por Slack (si está configurado)")

print("\n⏰ Logs en tiempo real:")
print("Revisa whatsapp_server.log para ver el procesamiento")
print("")

# Verificar credenciales críticas
critical_missing = []
if not os.getenv('TWILIO_ACCOUNT_SID'):
    critical_missing.append('TWILIO_ACCOUNT_SID')
if not os.getenv('TWILIO_AUTH_TOKEN'):
    critical_missing.append('TWILIO_AUTH_TOKEN')
if not os.getenv('ANTHROPIC_API_KEY'):
    critical_missing.append('ANTHROPIC_API_KEY')

if critical_missing:
    print(f"\n⚠️  ADVERTENCIA: Faltan credenciales críticas: {', '.join(critical_missing)}")
    print("   Ejecuta: source scripts/quick_env_setup.sh")
else:
    print("\n✅ Todas las credenciales críticas están configuradas")

print("\n📊 Monitoreo:")
print("tail -f whatsapp_server.log  # Ver logs en tiempo real")
print("")

# Crear comando de prueba con curl
test_webhook = f"""
# Prueba manual del webhook (opcional):
curl -X POST http://localhost:8000/webhook \\
  -H "Content-Type: application/json" \\
  -d '{{
    "event": "test.manual",
    "timestamp": "{datetime.now().isoformat()}",
    "patient_code": "TEST-2025-001",
    "detection": {{
      "lesion_detected": true,
      "confidence": 0.95,
      "grade": 2
    }}
  }}'
"""

print(f"\n🔧 Comando de prueba webhook:\n{test_webhook}")

# URLs importantes cuando esté en Render
print("\n🌐 URLs de Render (cuando esté desplegado):")
print("- WhatsApp: https://vigia-whatsapp.onrender.com")
print("- Webhook: https://vigia-webhook.onrender.com") 
print("- Configurar en Twilio: https://console.twilio.com/console/sms/whatsapp/sandbox")
print("  Webhook URL: https://vigia-whatsapp.onrender.com/webhook")