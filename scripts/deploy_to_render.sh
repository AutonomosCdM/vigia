#!/bin/bash
# Script para desplegar Vigia en Render

echo "🚀 Desplegando Vigia en Render..."
echo ""
echo "Este script te guiará a través del proceso de despliegue."
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Pasos para desplegar:${NC}"
echo ""
echo "1. Abre tu navegador en: https://dashboard.render.com/blueprints"
echo ""
echo "2. Click en 'New Blueprint Instance'"
echo ""
echo "3. Conecta tu repositorio:"
echo "   - URL: https://github.com/AutonomosCdM/vigia"
echo "   - Branch: main"
echo ""
echo "4. Render detectará automáticamente el archivo render.yaml"
echo ""
echo "5. Configura las siguientes variables de entorno:"
echo ""
echo -e "${GREEN}Variables requeridas:${NC}"
echo "TWILIO_ACCOUNT_SID = [Tu Account SID de Twilio]"
echo "TWILIO_AUTH_TOKEN = [Tu Auth Token de Twilio]"
echo "TWILIO_WHATSAPP_FROM = [Tu número de WhatsApp Twilio]"
echo "ANTHROPIC_API_KEY = [Tu API Key de Anthropic]"
echo "SUPABASE_URL = [Tu URL de Supabase]"
echo "SUPABASE_KEY = [Tu Key de Supabase]"
echo ""
echo "6. Click en 'Apply'"
echo ""
echo -e "${YELLOW}Después del despliegue:${NC}"
echo ""
echo "📱 Configura el webhook en Twilio:"
echo "   https://vigia-whatsapp.onrender.com/webhook/whatsapp"
echo ""
echo "🔍 Monitorea los logs en:"
echo "   https://dashboard.render.com/services"
echo ""
echo "📊 URLs de los servicios:"
echo "   - WhatsApp: https://vigia-whatsapp.onrender.com"
echo "   - Webhook: https://vigia-webhook.onrender.com"
echo ""

# Abrir el navegador automáticamente
read -p "¿Quieres abrir Render Dashboard ahora? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    echo "Abriendo Render Dashboard..."
    open "https://dashboard.render.com/blueprints/new?repo=https://github.com/AutonomosCdM/vigia"
fi

echo ""
echo "✅ Script completado. ¡Sigue los pasos en el navegador!"