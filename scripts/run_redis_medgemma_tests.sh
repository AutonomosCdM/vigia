#!/bin/bash
"""
Script para ejecutar pruebas completas del módulo Redis + MedGemma
Incluye diferentes categorías de pruebas y reportes de cobertura.
"""

set -e  # Exit on error

echo "🧪 Ejecutando Suite de Pruebas Redis + MedGemma"
echo "==============================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Función para ejecutar tests con manejo de errores
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    log_info "Ejecutando: $test_name"
    if eval "$test_command"; then
        log_success "$test_name completado"
        return 0
    else
        log_error "$test_name falló"
        return 1
    fi
}

# Cambiar al directorio del proyecto
cd "$(dirname "$0")/.."

log_info "Directorio de trabajo: $(pwd)"

# Verificar que pytest está disponible
if ! command -v python -m pytest &> /dev/null; then
    log_error "pytest no está disponible. Instalar con: pip install pytest"
    exit 1
fi

# 1. Pruebas básicas
echo ""
log_info "=== PRUEBAS BÁSICAS ==="
run_test "Pruebas de inicialización" \
    "python -m pytest tests/test_redis_medgemma_final.py::TestRedisGemmaIntegration::test_initialization -v"

run_test "Pruebas de cache" \
    "python -m pytest tests/test_redis_medgemma_final.py::TestRedisGemmaIntegration::test_cache_miss_and_hit -v"

run_test "Pruebas de protocolos" \
    "python -m pytest tests/test_redis_medgemma_final.py::TestRedisGemmaIntegration::test_protocol_retrieval -v"

# 2. Pruebas de integración
echo ""
log_info "=== PRUEBAS DE INTEGRACIÓN ==="
run_test "Flujo completo de consulta médica" \
    "python -m pytest tests/test_redis_medgemma_final.py::TestRedisGemmaIntegration::test_complete_workflow -v"

run_test "Comportamiento de cache repetido" \
    "python -m pytest tests/test_redis_medgemma_final.py::TestRedisGemmaIntegration::test_repeated_query_cache_behavior -v"

run_test "Operaciones Redis" \
    "python -m pytest tests/test_redis_medgemma_final.py::TestRedisGemmaIntegration::test_redis_operations -v"

# 3. Pruebas médicas específicas
echo ""
log_info "=== ESCENARIOS MÉDICOS ==="
run_test "Escenario de prevención" \
    "python -m pytest tests/test_redis_medgemma_final.py::TestMedicalScenarios::test_prevention_scenario -v"

run_test "Escenario de tratamiento" \
    "python -m pytest tests/test_redis_medgemma_final.py::TestMedicalScenarios::test_treatment_scenario -v"

run_test "Escenario de emergencia" \
    "python -m pytest tests/test_redis_medgemma_final.py::TestMedicalScenarios::test_emergency_scenario -v"

# 4. Pruebas de manejo de errores
echo ""
log_info "=== MANEJO DE ERRORES ==="
run_test "Manejo de errores" \
    "python -m pytest tests/test_redis_medgemma_final.py::TestRedisGemmaIntegration::test_error_handling -v"

# 5. Suite completa
echo ""
log_info "=== SUITE COMPLETA ==="
run_test "Todas las pruebas" \
    "python -m pytest tests/test_redis_medgemma_final.py -v --tb=short"

# 6. Pruebas con estadísticas
echo ""
log_info "=== ESTADÍSTICAS DE RENDIMIENTO ==="
run_test "Análisis de duración" \
    "python -m pytest tests/test_redis_medgemma_final.py --durations=10"

# 7. Verificación de cobertura (si está disponible)
echo ""
log_info "=== COBERTURA DE CÓDIGO ==="
if command -v python -m pytest --cov &> /dev/null; then
    run_test "Reporte de cobertura" \
        "python -m pytest tests/test_redis_medgemma_final.py --cov=tests --cov-report=term-missing"
else
    log_warning "pytest-cov no disponible. Instalar con: pip install pytest-cov"
fi

# 8. Resumen final
echo ""
echo "=========================================="
log_success "🎉 Suite de pruebas completada"
echo "=========================================="

# Estadísticas finales
total_tests=$(python -m pytest tests/test_redis_medgemma_final.py --collect-only -q | grep -c "test")
log_info "Total de pruebas ejecutadas: $total_tests"

# Verificar archivos de prueba generados
if [ -f ".coverage" ]; then
    log_info "Archivo de cobertura generado: .coverage"
fi

if [ -d "htmlcov" ]; then
    log_info "Reporte HTML de cobertura: htmlcov/index.html"
fi

echo ""
log_info "💡 Para ejecutar pruebas específicas:"
echo "   python -m pytest tests/test_redis_medgemma_final.py::TestClass::test_method -v"

log_info "💡 Para ejecutar con cobertura detallada:"
echo "   python -m pytest tests/test_redis_medgemma_final.py --cov --cov-report=html"

log_info "💡 Para ejecutar en modo silencioso:"
echo "   python -m pytest tests/test_redis_medgemma_final.py -q"

echo ""
log_success "Script completado exitosamente! ✅"