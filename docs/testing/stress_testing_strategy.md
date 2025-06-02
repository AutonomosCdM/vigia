# Estrategia de Stress Testing - Vigia Detection System

## Resumen Ejecutivo

Con 124 tests pasando exitosamente, tenemos una base sólida para implementar una estrategia de stress testing que valide la robustez del sistema Vigia bajo cargas intensivas y condiciones extremas.

## Análisis de Tests Existentes

### Tests que Pasan (124)
- **CLI Module**: 5 tests - Procesamiento de imágenes, argumentos
- **CV Pipeline**: 8 tests - Detección, preprocesamiento  
- **Database**: 7 tests - Supabase client, CRUD operations
- **Messaging**: 27 tests - WhatsApp/Twilio integration, templates
- **Utils**: 1 test - Utilidades de imagen
- **Webhook System**: 76 tests - Cliente, servidor, handlers, integración

## Estrategia de Stress Testing

### 1. Test de Carga Gradual (Load Testing)
```bash
# Ejecutar tests en paralelo con pytest-xdist
pip install pytest-xdist pytest-benchmark

# Stress test básico - 10 procesos paralelos
pytest vigia_detect/ --ignore=vigia_detect/redis_layer/tests/test_cache_service.py \
       --ignore=vigia_detect/redis_layer/tests/test_vector_service.py \
       --ignore=vigia_detect/redis_layer/tests/test_medical_cache.py \
       -n 10 --maxfail=5

# Stress test intensivo - 20 procesos paralelos  
pytest vigia_detect/ --ignore=vigia_detect/redis_layer/tests/test_cache_service.py \
       --ignore=vigia_detect/redis_layer/tests/test_vector_service.py \
       --ignore=vigia_detect/redis_layer/tests/test_medical_cache.py \
       -n 20 --maxfail=10
```

### 2. Test de Repetición Masiva (Endurance Testing)
```bash
# Ejecutar cada test 100 veces para detectar race conditions
pytest vigia_detect/messaging/tests/ --count=100

# Test de memoria - ejecutar en loop para detectar memory leaks
for i in {1..50}; do
    echo "Iteration $i"
    pytest vigia_detect/cv_pipeline/tests/ -v
    sleep 1
done
```

### 3. Test de Concurrencia (Concurrency Testing)

#### 3.1 Webhook Stress Testing
```python
# Script: scripts/webhook_stress_test.py
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor

async def webhook_stress_test():
    """Test concurrencia de webhooks"""
    concurrent_requests = 50
    total_requests = 1000
    
    async with aiohttp.ClientSession() as session:
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def send_webhook_event(event_id):
            async with semaphore:
                webhook_data = {
                    "event_type": "DETECTION_COMPLETED",
                    "payload": {
                        "patient_code": f"TEST-{event_id}",
                        "detections": [{"confidence": 0.85, "stage": 2}]
                    }
                }
                
                try:
                    async with session.post(
                        "http://localhost:8000/webhook",
                        json=webhook_data,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        return response.status == 200
                except Exception as e:
                    return False
        
        # Ejecutar requests concurrentes
        tasks = [send_webhook_event(i) for i in range(total_requests)]
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        success_rate = sum(1 for r in results if r is True) / len(results)
        rps = total_requests / (end_time - start_time)
        
        print(f"Success Rate: {success_rate:.2%}")
        print(f"Requests/Second: {rps:.2f}")
        print(f"Total Time: {end_time - start_time:.2f}s")

if __name__ == "__main__":
    asyncio.run(webhook_stress_test())
```

#### 3.2 Database Stress Testing
```python
# Script: scripts/db_stress_test.py
import threading
import time
from vigia_detect.db.supabase_client import SupabaseClient

def db_stress_worker(worker_id, iterations=100):
    """Worker para stress testing de base de datos"""
    client = SupabaseClient()
    success_count = 0
    
    for i in range(iterations):
        try:
            # Test CRUD operations
            patient_code = f"STRESS-{worker_id}-{i}"
            
            # Create patient
            patient = client.get_or_create_patient(patient_code)
            
            # Save detection
            detection_data = {
                "patient_id": patient["id"],
                "detections": [{"confidence": 0.8, "stage": 1}],
                "image_path": f"/test/stress_{worker_id}_{i}.jpg"
            }
            client.save_detection(detection_data)
            
            # Query detections
            client.get_patient_detections(patient_code)
            
            success_count += 1
            
        except Exception as e:
            print(f"Worker {worker_id}, iteration {i} failed: {e}")
    
    print(f"Worker {worker_id}: {success_count}/{iterations} successful operations")

def run_db_stress_test():
    """Ejecutar stress test de base de datos"""
    num_workers = 20
    iterations_per_worker = 50
    
    threads = []
    start_time = time.time()
    
    for i in range(num_workers):
        thread = threading.Thread(
            target=db_stress_worker, 
            args=(i, iterations_per_worker)
        )
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    total_operations = num_workers * iterations_per_worker * 3  # 3 ops per iteration
    
    print(f"\nDB Stress Test Complete:")
    print(f"Total Operations: {total_operations}")
    print(f"Total Time: {end_time - start_time:.2f}s")
    print(f"Operations/Second: {total_operations / (end_time - start_time):.2f}")

if __name__ == "__main__":
    run_db_stress_test()
```

### 4. Test de Recursos (Resource Testing)

#### 4.1 Memory Stress Test
```bash
# Script: scripts/memory_stress_test.sh
#!/bin/bash

echo "Starting Memory Stress Test"
echo "Monitoring memory usage during test execution..."

# Monitor memory usage
(
    while true; do
        echo "$(date): $(ps aux | grep pytest | grep -v grep | awk '{sum+=$6} END {print "Memory: " sum/1024 " MB"}')"
        sleep 5
    done
) &
MONITOR_PID=$!

# Run memory-intensive tests repeatedly
for i in {1..20}; do
    echo "Memory Test Iteration $i"
    pytest vigia_detect/cv_pipeline/tests/ \
           vigia_detect/messaging/tests/ \
           vigia_detect/webhook/tests/test_models.py \
           vigia_detect/webhook/tests/test_client.py \
           --tb=no -q
done

# Stop monitoring
kill $MONITOR_PID
echo "Memory Stress Test Complete"
```

#### 4.2 I/O Stress Test  
```python
# Script: scripts/io_stress_test.py
import concurrent.futures
import tempfile
import os
from pathlib import Path
from vigia_detect.utils.image_utils import load_image, save_image
from vigia_detect.cv_pipeline.preprocessor import ImagePreprocessor

def io_stress_worker(worker_id, iterations=50):
    """Worker para stress testing de I/O"""
    preprocessor = ImagePreprocessor()
    success_count = 0
    
    with tempfile.TemporaryDirectory() as temp_dir:
        for i in range(iterations):
            try:
                # Create test image
                test_image_path = Path(temp_dir) / f"test_{worker_id}_{i}.jpg"
                
                # Simulate image processing I/O
                # This would normally load a real image
                # For stress testing, we'll use a dummy operation
                
                # Simulate preprocessing
                result = preprocessor.preprocess(str(test_image_path), enhance_contrast=True)
                
                success_count += 1
                
            except Exception as e:
                print(f"I/O Worker {worker_id}, iteration {i} failed: {e}")
    
    print(f"I/O Worker {worker_id}: {success_count}/{iterations} successful operations")

def run_io_stress_test():
    """Ejecutar stress test de I/O"""
    num_workers = 10
    iterations_per_worker = 100
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [
            executor.submit(io_stress_worker, i, iterations_per_worker)
            for i in range(num_workers)
        ]
        
        concurrent.futures.wait(futures)
    
    print("I/O Stress Test Complete")

if __name__ == "__main__":
    run_io_stress_test()
```

### 5. Test de Integración Extrema

#### 5.1 Full System Stress Test
```bash
# Script: scripts/full_system_stress.sh
#!/bin/bash

echo "=== VIGIA FULL SYSTEM STRESS TEST ==="
echo "Starting comprehensive stress testing..."

# 1. Basic test validation
echo "Phase 1: Baseline validation"
pytest vigia_detect/ --ignore=vigia_detect/redis_layer/tests/test_cache_service.py \
       --ignore=vigia_detect/redis_layer/tests/test_vector_service.py \
       --ignore=vigia_detect/redis_layer/tests/test_medical_cache.py \
       -q --tb=no

if [ $? -ne 0 ]; then
    echo "❌ Baseline tests failed. Aborting stress test."
    exit 1
fi

# 2. Parallel execution stress
echo "Phase 2: Parallel execution stress"
pytest vigia_detect/ --ignore=vigia_detect/redis_layer/tests/test_cache_service.py \
       --ignore=vigia_detect/redis_layer/tests/test_vector_service.py \
       --ignore=vigia_detect/redis_layer/tests/test_medical_cache.py \
       -n 15 --maxfail=20 -q

# 3. Repetition stress  
echo "Phase 3: Repetition stress"
pytest vigia_detect/messaging/tests/ --count=50 -q --tb=no

# 4. Resource monitoring during tests
echo "Phase 4: Resource-monitored execution"
python scripts/memory_stress_test.py &
MEMORY_PID=$!

python scripts/io_stress_test.py &
IO_PID=$!

# Wait for completion
wait $MEMORY_PID
wait $IO_PID

# 5. Webhook system stress (if server is running)
echo "Phase 5: Webhook stress testing"
if curl -s http://localhost:8000/health > /dev/null; then
    python scripts/webhook_stress_test.py
else
    echo "⚠️  Webhook server not running, skipping webhook stress test"
fi

echo "=== STRESS TEST COMPLETE ==="
```

## Métricas y Monitoreo

### 1. Métricas Clave
- **Success Rate**: % de tests que pasan bajo carga
- **Response Time**: Tiempo promedio de ejecución de tests
- **Throughput**: Tests por segundo
- **Error Rate**: % de fallos bajo estrés
- **Resource Usage**: CPU, memoria, I/O durante tests

### 2. Thresholds de Aceptación
```yaml
acceptable_thresholds:
  success_rate: "> 95%"
  max_response_time: "< 30s per test"
  min_throughput: "> 2 tests/second" 
  max_memory_usage: "< 2GB"
  max_error_rate: "< 5%"
```

### 3. Alertas y Reportes
```python
# Script: scripts/stress_test_report.py
def generate_stress_report(results):
    """Generar reporte de stress testing"""
    report = f"""
    VIGIA STRESS TEST REPORT
    ========================
    
    Test Execution Summary:
    - Total Tests Run: {results['total_tests']}
    - Success Rate: {results['success_rate']:.2%}
    - Average Response Time: {results['avg_response_time']:.2f}s
    - Peak Memory Usage: {results['peak_memory']:.2f}MB
    - Total Duration: {results['total_duration']:.2f}s
    
    Performance Metrics:
    - Tests/Second: {results['throughput']:.2f}
    - Error Rate: {results['error_rate']:.2%}
    - CPU Usage: {results['cpu_usage']:.1f}%
    
    Status: {'✅ PASS' if results['success_rate'] > 0.95 else '❌ FAIL'}
    """
    
    return report
```

## Opinión y Recomendaciones

### ✅ Fortalezas del Sistema Actual
1. **Cobertura sólida**: 124 tests cubren componentes críticos
2. **Modularidad**: Tests bien organizados por módulos
3. **Integración robusta**: Webhook system bien testado
4. **Mocking efectivo**: Dependencias externas bien aisladas

### ⚠️ Áreas de Mejora Identificadas
1. **Redis**: Tests fallan por dependencias, necesita refactoring
2. **Webhook concurrency**: Algunos tests fallan con puertos ocupados
3. **Resource cleanup**: Sesiones aiohttp no se cierran correctamente
4. **Error handling**: Mejorar manejo de errores en tests de integración

### 🎯 Estrategia Recomendada

**Fase 1: Implementación Inmediata (1-2 días)**
```bash
# Ejecutar stress test básico
./scripts/full_system_stress.sh
```

**Fase 2: Optimización (3-5 días)**
- Arreglar tests de Redis
- Mejorar cleanup de recursos en webhook tests
- Implementar benchmarking automático

**Fase 3: Monitoreo Continuo (ongoing)**
- Integrar stress tests en CI/CD
- Alertas automáticas por degradación de performance
- Dashboard de métricas de testing

### 💡 Valor del Stress Testing

Con 124 tests pasando, el stress testing nos permitirá:

1. **Validar robustez** bajo cargas reales de producción
2. **Detectar race conditions** en componentes concurrentes  
3. **Identificar memory leaks** en procesamiento de imágenes
4. **Optimizar performance** del sistema webhook
5. **Asegurar estabilidad** antes de deploy a producción

La base actual es sólida y está lista para stress testing intensivo.