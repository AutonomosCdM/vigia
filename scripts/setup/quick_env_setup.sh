#!/bin/bash
# Script rápido para cargar las credenciales en el entorno actual

echo "🔐 Cargando credenciales de Vigia..."

# Cargar desde .env.local si existe
if [ -f .env.local ]; then
    export $(cat .env.local | grep -v '^#' | xargs)
    echo "✅ Credenciales cargadas desde .env.local"
else
    echo "❌ No se encontró .env.local"
    echo "   Ejecuta primero: python scripts/setup_credentials.py"
    exit 1
fi

# Verificar que las credenciales principales estén configuradas
required_vars=(
    "ANTHROPIC_API_KEY"
    "SUPABASE_URL"
    "SUPABASE_KEY"
)

missing=0
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Falta: $var"
        missing=1
    else
        echo "✅ $var configurada"
    fi
done

if [ $missing -eq 1 ]; then
    echo ""
    echo "⚠️  Algunas credenciales faltan. Ejecuta:"
    echo "   python scripts/setup_credentials.py"
else
    echo ""
    echo "✅ Todas las credenciales están configuradas"
    echo ""
    echo "📋 Para usar en otros scripts:"
    echo "   source scripts/quick_env_setup.sh"
fi