#!/bin/bash

# Script para iniciar el servidor Slack con ngrok para desarrollo local

echo "🚀 Iniciando Servidor Slack de Vigía..."

# Verificar que las variables de entorno estén configuradas
if [ ! -f .env ]; then
    echo "❌ Error: No se encontró archivo .env"
    echo "Por favor, copia config/.env.example a .env y configura las variables"
    exit 1
fi

# Cargar variables de entorno
export $(cat .env | grep -v '^#' | xargs)

# Verificar que tengamos el token de Slack
if [ -z "$SLACK_BOT_TOKEN" ]; then
    echo "❌ Error: SLACK_BOT_TOKEN no está configurado en .env"
    exit 1
fi

# Iniciar el servidor en background
echo "📡 Iniciando servidor Flask..."
cd apps && python slack_server.py &
SERVER_PID=$!

# Esperar a que el servidor inicie
sleep 3

# Verificar si el servidor está corriendo
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "❌ Error: El servidor no pudo iniciar"
    exit 1
fi

echo "✅ Servidor Flask iniciado (PID: $SERVER_PID)"

# Si estamos en desarrollo, iniciar ngrok
if [ "$ENVIRONMENT" = "development" ]; then
    echo "🌐 Iniciando ngrok para desarrollo local..."
    
    # Verificar si ngrok está instalado
    if ! command -v ngrok &> /dev/null; then
        echo "❌ Error: ngrok no está instalado"
        echo "Instálalo con: brew install ngrok (macOS) o descárgalo de https://ngrok.com"
        exit 1
    fi
    
    # Iniciar ngrok
    ngrok http 5000 &
    NGROK_PID=$!
    
    # Esperar a que ngrok inicie
    sleep 3
    
    # Obtener la URL de ngrok
    NGROK_URL=$(curl -s localhost:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null)
    
    if [ -z "$NGROK_URL" ]; then
        echo "❌ Error: No se pudo obtener la URL de ngrok"
        kill $SERVER_PID
        exit 1
    fi
    
    echo "✅ ngrok iniciado (PID: $NGROK_PID)"
    echo ""
    echo "🔗 URL pública de ngrok: $NGROK_URL"
    echo ""
    echo "📋 Configuración en Slack App:"
    echo "1. Ve a https://api.slack.com/apps"
    echo "2. Selecciona tu app"
    echo "3. En 'Interactivity & Shortcuts':"
    echo "   - Enable Interactivity: ON"
    echo "   - Request URL: $NGROK_URL/slack/events"
    echo "4. En 'Event Subscriptions' (si usas eventos):"
    echo "   - Enable Events: ON"
    echo "   - Request URL: $NGROK_URL/slack/events"
    echo "5. Guarda los cambios"
    echo ""
    echo "🛑 Para detener el servidor: Ctrl+C"
    
    # Mantener el script corriendo
    trap "echo ''; echo '🛑 Deteniendo servicios...'; kill $SERVER_PID $NGROK_PID 2>/dev/null; exit" INT TERM
    wait
else
    echo "✅ Servidor iniciado en modo $ENVIRONMENT"
    echo "URL: http://$SERVER_HOST:$SERVER_PORT"
    echo ""
    echo "🛑 Para detener el servidor: Ctrl+C"
    
    # Mantener el script corriendo
    trap "echo ''; echo '🛑 Deteniendo servidor...'; kill $SERVER_PID 2>/dev/null; exit" INT TERM
    wait $SERVER_PID
fi