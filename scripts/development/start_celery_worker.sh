#!/bin/bash

# Start Celery Worker for Vigia Medical Pipeline
# =============================================
# Script para iniciar worker de Celery con configuración específica médica

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🏥 Iniciando Celery Worker para Pipeline Médico Vigía${NC}"

# Verificar que estamos en el directorio correcto
if [ ! -f "vigia_detect/core/celery_config.py" ]; then
    echo -e "${RED}❌ Error: No se encuentra celery_config.py. Ejecutar desde directorio raíz del proyecto.${NC}"
    exit 1
fi

# Verificar Redis
echo -e "${YELLOW}🔍 Verificando conexión Redis...${NC}"
if ! redis-cli ping >/dev/null 2>&1; then
    echo -e "${RED}❌ Error: Redis no está ejecutándose. Iniciar Redis primero:${NC}"
    echo "   brew services start redis"
    echo "   # O en Linux: sudo systemctl start redis"
    exit 1
fi

echo -e "${GREEN}✅ Redis conectado correctamente${NC}"

# Configurar variables de entorno
export PYTHONPATH="$(pwd):$PYTHONPATH"
export CELERY_APP="vigia_detect.core.celery_config:celery_app"

# Configuración del worker médico
WORKER_NAME="${1:-vigia_medical_worker}"
LOGLEVEL="${2:-info}"
CONCURRENCY="${3:-4}"
QUEUES="${4:-medical_priority,image_processing,notifications,audit_logging,default}"

echo -e "${BLUE}📋 Configuración del Worker:${NC}"
echo "   Worker Name: $WORKER_NAME"
echo "   Log Level: $LOGLEVEL"
echo "   Concurrency: $CONCURRENCY"
echo "   Queues: $QUEUES"

# Crear directorio de logs si no existe
mkdir -p logs/celery

# Iniciar worker con configuración médica específica
echo -e "${GREEN}🚀 Iniciando Celery Worker...${NC}"

celery -A vigia_detect.core.celery_config worker \
    --hostname="$WORKER_NAME@%h" \
    --loglevel="$LOGLEVEL" \
    --concurrency="$CONCURRENCY" \
    --queues="$QUEUES" \
    --logfile="logs/celery/worker_${WORKER_NAME}.log" \
    --pidfile="logs/celery/worker_${WORKER_NAME}.pid" \
    --time-limit=300 \
    --soft-time-limit=240 \
    --max-tasks-per-child=100 \
    --prefetch-multiplier=1 \
    --without-gossip \
    --without-mingle \
    --without-heartbeat

# Nota: Las opciones específicas médicas:
# --time-limit=300: 5 minutos máximo por tarea
# --soft-time-limit=240: 4 minutos warning
# --max-tasks-per-child=100: Reciclar worker cada 100 tareas
# --prefetch-multiplier=1: Una tarea por vez para procesos críticos
# --without-gossip/mingle/heartbeat: Reducir overhead de red

echo -e "${GREEN}✅ Celery Worker iniciado correctamente${NC}"