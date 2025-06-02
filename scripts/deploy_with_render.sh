#!/bin/bash

# Script para deployment completo usando Render CLI
# Autor: Vigia Team
# Descripción: Automatiza el proceso de deployment en Render

set -e  # Salir si hay errores

echo "🚀 Vigia - Deployment Automatizado con Render CLI"
echo "================================================="
echo ""

# Verificar que tenemos las herramientas necesarias
command -v render >/dev/null 2>&1 || { echo "❌ Error: Render CLI no está instalado. Instala con: brew install render"; exit 1; }
command -v git >/dev/null 2>&1 || { echo "❌ Error: Git no está instalado."; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "❌ Error: jq no está instalado. Instala con: brew install jq"; exit 1; }

# Verificar que estamos en el directorio correcto
if [ ! -f "render.yaml" ]; then
    echo "❌ Error: No se encontró render.yaml. Asegúrate de estar en el directorio raíz del proyecto."
    exit 1
fi

# Verificar autenticación con Render
echo "🔐 Verificando autenticación con Render..."
if ! render whoami --output json >/dev/null 2>&1; then
    echo "❌ No estás autenticado. Ejecutando render login..."
    render login
fi

# Obtener información del usuario
USER_INFO=$(render whoami --output json)
echo "✅ Autenticado como: $(echo $USER_INFO | jq -r '.Email')"
echo ""

# Verificar y commit cambios si hay
echo "📋 Verificando cambios pendientes..."
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Hay cambios sin commitear. ¿Deseas commitearlos? (s/n)"
    read -r response
    if [[ "$response" =~ ^[Ss]$ ]]; then
        git add .
        echo "Mensaje del commit:"
        read -r commit_message
        git commit -m "$commit_message"
        git push origin main
    fi
fi

# Obtener el último commit
LATEST_COMMIT=$(git rev-parse HEAD)
echo "📌 Último commit: $LATEST_COMMIT"
echo ""

# Función para obtener servicios
get_services() {
    curl -s -H "Authorization: Bearer ${RENDER_API_KEY}" \
         https://api.render.com/v1/services | \
    jq -r '.[] | select(.service.name | startswith("vigia-")) | .service | "\(.id)|\(.name)"'
}

# Verificar API Key
if [ -z "$RENDER_API_KEY" ]; then
    echo "⚠️  RENDER_API_KEY no está configurada."
    echo "   Ve a https://dashboard.render.com/u/settings#api-keys"
    echo "   y ejecuta: export RENDER_API_KEY='tu-api-key'"
    exit 1
fi

# Listar servicios
echo "🔍 Buscando servicios de Vigia..."
SERVICES=$(get_services)

if [ -z "$SERVICES" ]; then
    echo "❌ No se encontraron servicios de Vigia"
    echo "   Asegúrate de que los servicios estén creados en Render"
    exit 1
fi

echo "📋 Servicios encontrados:"
while IFS='|' read -r service_id service_name; do
    echo "   - $service_name ($service_id)"
done <<< "$SERVICES"
echo ""

# Opción de deployment
echo "🎯 ¿Qué deseas hacer?"
echo "   1) Deploy todos los servicios"
echo "   2) Deploy un servicio específico"
echo "   3) Ver logs de servicios"
echo "   4) Verificar estado de servicios"
echo "   5) Conectar Environment Groups"
echo ""
read -p "Selecciona una opción (1-5): " option

case $option in
    1)
        echo ""
        echo "🚀 Iniciando deployment de todos los servicios..."
        while IFS='|' read -r service_id service_name; do
            echo ""
            echo "📦 Desplegando $service_name..."
            # Usar API porque el CLI tiene limitaciones
            response=$(curl -s -X POST \
                -H "Authorization: Bearer ${RENDER_API_KEY}" \
                -H "Content-Type: application/json" \
                -d "{\"commitId\": \"$LATEST_COMMIT\"}" \
                "https://api.render.com/v1/services/$service_id/deploys")
            
            deploy_id=$(echo $response | jq -r '.id // empty')
            if [ -n "$deploy_id" ]; then
                echo "✅ Deploy iniciado: $deploy_id"
            else
                echo "❌ Error al iniciar deploy"
                echo $response | jq '.'
            fi
        done <<< "$SERVICES"
        ;;
    
    2)
        echo ""
        echo "Servicios disponibles:"
        i=1
        declare -a service_array
        while IFS='|' read -r service_id service_name; do
            echo "   $i) $service_name"
            service_array[$i]="$service_id|$service_name"
            ((i++))
        done <<< "$SERVICES"
        
        read -p "Selecciona el servicio (número): " service_num
        selected="${service_array[$service_num]}"
        
        if [ -n "$selected" ]; then
            IFS='|' read -r service_id service_name <<< "$selected"
            echo ""
            echo "📦 Desplegando $service_name..."
            response=$(curl -s -X POST \
                -H "Authorization: Bearer ${RENDER_API_KEY}" \
                -H "Content-Type: application/json" \
                -d "{\"commitId\": \"$LATEST_COMMIT\"}" \
                "https://api.render.com/v1/services/$service_id/deploys")
            
            deploy_id=$(echo $response | jq -r '.id // empty')
            if [ -n "$deploy_id" ]; then
                echo "✅ Deploy iniciado: $deploy_id"
            else
                echo "❌ Error al iniciar deploy"
                echo $response | jq '.'
            fi
        fi
        ;;
    
    3)
        echo ""
        echo "📋 Selecciona el servicio para ver logs:"
        i=1
        declare -a service_array
        while IFS='|' read -r service_id service_name; do
            echo "   $i) $service_name"
            service_array[$i]="$service_id|$service_name"
            ((i++))
        done <<< "$SERVICES"
        
        read -p "Selecciona el servicio (número): " service_num
        selected="${service_array[$service_num]}"
        
        if [ -n "$selected" ]; then
            IFS='|' read -r service_id service_name <<< "$selected"
            echo ""
            echo "📜 Logs de $service_name (Ctrl+C para salir):"
            render logs $service_id --tail
        fi
        ;;
    
    4)
        echo ""
        echo "📊 Estado de los servicios:"
        while IFS='|' read -r service_id service_name; do
            echo ""
            echo "🔍 $service_name:"
            status=$(curl -s -H "Authorization: Bearer ${RENDER_API_KEY}" \
                "https://api.render.com/v1/services/$service_id" | \
                jq -r '.suspended // "active"')
            
            last_deploy=$(curl -s -H "Authorization: Bearer ${RENDER_API_KEY}" \
                "https://api.render.com/v1/services/$service_id/deploys?limit=1" | \
                jq -r '.[0].deploy | "Estado: \(.status) - Commit: \(.commit.id[0:7]) - Fecha: \(.createdAt)"')
            
            echo "   Estado del servicio: $status"
            echo "   Último deploy: $last_deploy"
        done <<< "$SERVICES"
        ;;
    
    5)
        echo ""
        echo "🔗 Conectando Environment Groups..."
        python scripts/connect_env_groups.py
        ;;
    
    *)
        echo "❌ Opción no válida"
        exit 1
        ;;
esac

echo ""
echo "✅ ¡Operación completada!"