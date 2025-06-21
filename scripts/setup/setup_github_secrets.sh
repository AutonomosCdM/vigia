#!/bin/bash
# Script para configurar GitHub Secrets para Vigia

echo "==================================="
echo "Configuración de GitHub Secrets"
echo "==================================="

# Verificar que gh CLI esté instalado
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) no está instalado."
    echo "Por favor instala gh: https://cli.github.com/"
    exit 1
fi

# Verificar autenticación
if ! gh auth status &> /dev/null; then
    echo "❌ No estás autenticado en GitHub CLI."
    echo "Ejecuta: gh auth login"
    exit 1
fi

echo "✅ GitHub CLI detectado y autenticado"
echo ""

# Función para establecer un secret
set_secret() {
    local secret_name=$1
    local secret_value=$2
    
    if [ -z "$secret_value" ]; then
        echo "⚠️  Saltando $secret_name (valor vacío)"
        return
    fi
    
    echo "Configurando $secret_name..."
    echo "$secret_value" | gh secret set "$secret_name" --repo AutonomosCdM/vigia
    
    if [ $? -eq 0 ]; then
        echo "✅ $secret_name configurado exitosamente"
    else
        echo "❌ Error configurando $secret_name"
    fi
}

# Leer credenciales de .env si existe
if [ -f .env ]; then
    echo "📄 Leyendo credenciales de .env..."
    export $(cat .env | grep -v '^#' | xargs)
fi

echo ""
echo "Configurando secrets de Twilio..."
set_secret "TWILIO_ACCOUNT_SID" "$TWILIO_ACCOUNT_SID"
set_secret "TWILIO_AUTH_TOKEN" "$TWILIO_AUTH_TOKEN"
set_secret "TWILIO_WHATSAPP_FROM" "$TWILIO_WHATSAPP_FROM"

echo ""
echo "Configurando API keys..."
set_secret "ANTHROPIC_API_KEY" "$ANTHROPIC_API_KEY"

echo ""
echo "Configurando Slack (si está disponible)..."
set_secret "SLACK_BOT_TOKEN" "$SLACK_BOT_TOKEN"
set_secret "SLACK_APP_TOKEN" "$SLACK_APP_TOKEN"
set_secret "SLACK_SIGNING_SECRET" "$SLACK_SIGNING_SECRET"

echo ""
echo "Configurando Supabase..."
set_secret "SUPABASE_URL" "$SUPABASE_URL"
set_secret "SUPABASE_KEY" "$SUPABASE_KEY"

echo ""
echo "==================================="
echo "✅ Configuración completada"
echo "==================================="
echo ""
echo "Puedes verificar los secrets en:"
echo "https://github.com/AutonomosCdM/vigia/settings/secrets/actions"
echo ""
echo "Para agregar manualmente:"
echo "gh secret set NOMBRE_SECRET --repo AutonomosCdM/vigia"