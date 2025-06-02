#!/bin/bash
# Redis setup script using Redis CLI
# This script creates indexes and loads initial data using Redis CLI commands

echo "🚀 Redis Setup for Vigia Medical System"
echo "======================================"

# Load environment variables
if [ -f "vigia_detect/.env" ]; then
    export $(cat vigia_detect/.env | grep -v '^#' | xargs)
else
    echo "❌ Error: vigia_detect/.env file not found"
    echo "Please create it from .env.example"
    exit 1
fi

# Set Redis CLI connection parameters
REDIS_CLI_ARGS=""
if [ ! -z "$REDIS_HOST" ]; then
    REDIS_CLI_ARGS="$REDIS_CLI_ARGS -h $REDIS_HOST"
fi
if [ ! -z "$REDIS_PORT" ]; then
    REDIS_CLI_ARGS="$REDIS_CLI_ARGS -p $REDIS_PORT"
fi
if [ ! -z "$REDIS_PASSWORD" ]; then
    REDIS_CLI_ARGS="$REDIS_CLI_ARGS -a $REDIS_PASSWORD"
fi
if [ "$REDIS_SSL" = "true" ]; then
    REDIS_CLI_ARGS="$REDIS_CLI_ARGS --tls"
fi

echo "Testing Redis connection..."
redis-cli $REDIS_CLI_ARGS ping > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Failed to connect to Redis"
    echo "Connection parameters:"
    echo "  Host: ${REDIS_HOST:-localhost}"
    echo "  Port: ${REDIS_PORT:-6379}"
    echo "  SSL: ${REDIS_SSL:-false}"
    exit 1
fi
echo "✅ Redis connection successful"

# Function to execute Redis command
redis_exec() {
    redis-cli $REDIS_CLI_ARGS "$@"
}

# Check if RediSearch module is loaded
echo -e "\nChecking RediSearch module..."
MODULE_CHECK=$(redis_exec MODULE LIST | grep -i search)
if [ -z "$MODULE_CHECK" ]; then
    echo "❌ RediSearch module not found"
    echo "Please install Redis Stack or load RediSearch module"
    exit 1
fi
echo "✅ RediSearch module found"

# Create medical cache index
echo -e "\nCreating medical cache index..."
redis_exec FT.CREATE idx:medical_cache ON HASH PREFIX 1 "cache:medical:" \
    SCHEMA \
    query TEXT NOSTEM \
    response TEXT \
    medical_context TEXT NOSTEM \
    timestamp NUMERIC \
    ttl NUMERIC \
    hit_count NUMERIC \
    embedding VECTOR FLAT 6 TYPE FLOAT32 DIM 384 DISTANCE_METRIC COSINE

if [ $? -eq 0 ]; then
    echo "✅ Medical cache index created"
else
    echo "⚠️  Medical cache index might already exist (this is OK)"
fi

# Create protocol index
echo -e "\nCreating medical protocols index..."
redis_exec FT.CREATE idx:medical_protocols ON HASH PREFIX 1 "protocol:" \
    SCHEMA \
    title TEXT NOSTEM WEIGHT 2.0 \
    content TEXT WEIGHT 1.0 \
    source TEXT NOSTEM \
    tags TAG \
    lpp_grades TAG \
    page_number NUMERIC \
    embedding VECTOR HNSW 8 TYPE FLOAT32 DIM 384 DISTANCE_METRIC COSINE M 16 EF_CONSTRUCTION 200

if [ $? -eq 0 ]; then
    echo "✅ Medical protocols index created"
else
    echo "⚠️  Medical protocols index might already exist (this is OK)"
fi

# Load sample protocols
echo -e "\nLoading sample medical protocols..."

# Prevention protocol
redis_exec HSET protocol:prevention_001 \
    title "Protocolo de Prevención de LPP - MINSAL" \
    content "Las lesiones por presión (LPP) son áreas de daño localizado en la piel y tejidos subyacentes. Prevención: 1) Cambios posturales cada 2 horas 2) Superficies especiales 3) Evaluación con escala de Braden 4) Piel limpia y seca 5) Nutrición adecuada" \
    source "MINSAL Chile 2019" \
    tags "prevention,care,assessment" \
    lpp_grades "grade_0,grade_1" \
    page_number 15 \
    embedding ""

# Treatment Grade 2 protocol
redis_exec HSET protocol:treatment_grade2_001 \
    title "Tratamiento LPP Grado 2" \
    content "Tratamiento de LPP grado 2 (pérdida parcial del espesor): 1) Limpieza con suero fisiológico 2) Apósito hidrocoloide o espuma 3) Protección de zona 4) Cambios según fabricante 5) Monitoreo de infección 6) Medidas preventivas continuas" \
    source "Protocolo EPUAP/NPUAP" \
    tags "treatment,care" \
    lpp_grades "grade_2" \
    page_number 45 \
    embedding ""

# Treatment Grade 3 protocol
redis_exec HSET protocol:treatment_grade3_001 \
    title "Tratamiento LPP Grado 3" \
    content "Tratamiento LPP grado 3 (pérdida total del espesor): 1) Evaluación multidisciplinaria 2) Desbridamiento si necesario 3) Control bacteriano 4) Apósitos avanzados 5) Considerar presión negativa 6) Optimización nutricional con proteínas" \
    source "Guía Clínica MINSAL" \
    tags "treatment,care" \
    lpp_grades "grade_3" \
    page_number 67 \
    embedding ""

echo "✅ Sample protocols loaded"

# Show index info
echo -e "\n📊 Index Statistics:"
echo "Medical Cache Index:"
redis_exec FT.INFO idx:medical_cache | grep -E "num_docs|num_terms"

echo -e "\nMedical Protocols Index:"
redis_exec FT.INFO idx:medical_protocols | grep -E "num_docs|num_terms"

echo -e "\n✨ Redis setup completed successfully!"
echo "You can now run: python examples/redis_phase2_demo.py"