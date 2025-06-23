# MedGemma Local Setup Guide

Guía completa para configurar y usar MedGemma localmente en el sistema Vigia.

## 📋 Tabla de Contenidos

1. [Ventajas de MedGemma Local](#ventajas)
2. [Requisitos del Sistema](#requisitos)
3. [Instalación](#instalación)
4. [Configuración](#configuración)
5. [Uso](#uso)
6. [Troubleshooting](#troubleshooting)

## 🎯 Ventajas de MedGemma Local vs API

### ✅ **MedGemma Local (Recomendado)**
- 🔒 **Privacidad total**: Datos médicos nunca salen del servidor
- 💰 **Sin costos**: No hay cargos por consulta
- ⚡ **Latencia predecible**: Sin dependencia de internet
- 🎛️ **Control total**: Parámetros personalizables
- 🔐 **Compliance**: Cumple HIPAA out-of-the-box
- 📊 **Escalabilidad**: Performance constante

### ❌ **API Externa (Problemático)**
- 🌐 Requiere internet estable
- 💸 Costo por uso
- 🔑 Gestión de API keys
- 🚨 Datos enviados a Google
- ⏱️ Latencia variable
- 📈 Escalabilidad limitada por cuotas

## 💻 Requisitos del Sistema

### Mínimos
- **RAM**: 16GB+ (recomendado 32GB)
- **GPU**: 8GB VRAM (modelo 4B) o 32GB VRAM (modelo 27B)
- **Almacenamiento**: 20GB libres para modelo + cache
- **Python**: 3.8+

### Recomendados
- **GPU**: NVIDIA RTX 3080/4080 o superior
- **CUDA**: 11.8+ o 12.0+
- **RAM**: 32GB+
- **SSD**: Para mejor performance de carga

### Verificar Requisitos
```bash
python scripts/setup_medgemma_local.py --check-only
```

## 🚀 Instalación

### 1. Instalar Dependencias

```bash
# Instalar dependencias básicas
python scripts/setup_medgemma_local.py --install-deps

# O manualmente:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install transformers>=4.50.0 accelerate bitsandbytes sentencepiece
```

### 2. Verificar Instalación

```bash
python scripts/setup_medgemma_local.py --list
```

### 3. Descargar Modelo

```bash
# Modelo 4B (recomendado para la mayoría)
python scripts/setup_medgemma_local.py --model 4b --download

# Modelo 27B (para servidores potentes)
python scripts/setup_medgemma_local.py --model 27b --download
```

### 4. Probar Instalación

```bash
python scripts/setup_medgemma_local.py --model 4b --test
```

## ⚙️ Configuración

### Selección de Modelo

| Modelo | Parámetros | Memoria GPU | Tipo | Uso Recomendado |
|--------|------------|-------------|------|-----------------|
| `4b-it` | 4B | ~8GB | Multimodal | **Recomendado** - Texto e imágenes |
| `4b-pt` | 4B | ~8GB | Multimodal | Fine-tuning personalizado |
| `27b-text` | 27B | ~32GB | Solo texto | Servidores de alta gama |

### Configuración por Hardware

```python
# GPU potente (RTX 4080+)
config = MedGemmaConfig(
    model_name=MedGemmaModel.MEDGEMMA_4B_IT,
    device="cuda",
    quantization=False,  # Sin quantización
    torch_dtype="bfloat16"
)

# GPU estándar (RTX 3080)
config = MedGemmaConfig(
    model_name=MedGemmaModel.MEDGEMMA_4B_IT,
    device="cuda",
    quantization=True,  # Con quantización
    torch_dtype="bfloat16"
)

# CPU (desarrollo/testing)
config = MedGemmaConfig(
    model_name=MedGemmaModel.MEDGEMMA_4B_IT,
    device="cpu",
    quantization=False,
    torch_dtype="float32"
)
```

## 🔧 Uso

### 1. Uso Básico

```python
import asyncio
from vigia_detect.ai.medgemma_local_client import (
    MedGemmaLocalClient, MedGemmaConfig, MedGemmaModel,
    MedGemmaRequest, InferenceMode
)

async def basic_usage():
    # Configurar cliente
    config = MedGemmaConfig(
        model_name=MedGemmaModel.MEDGEMMA_4B_IT,
        device="auto"
    )
    
    client = MedGemmaLocalClient(config)
    await client.initialize()
    
    # Crear consulta
    request = MedGemmaRequest(
        text_prompt="¿Cuáles son los signos de una LPP grado 2?",
        inference_mode=InferenceMode.TEXT_ONLY,
        max_tokens=200
    )
    
    # Generar respuesta
    response = await client.generate_medical_response(request)
    
    if response.success:
        print(f"Respuesta: {response.generated_text}")
        print(f"Confianza: {response.confidence_score}")
    
    await client.cleanup()

# Ejecutar
asyncio.run(basic_usage())
```

### 2. Con Contexto Médico

```python
from vigia_detect.ai.medgemma_local_client import MedicalContext

# Crear contexto del paciente
context = MedicalContext(
    patient_age=75,
    patient_gender="femenino",
    medical_history="Diabetes tipo 2, hipertensión",
    current_medications=["Metformina", "Enalapril"],
    symptoms="Eritema en región sacra",
    urgency_level="urgent"
)

request = MedGemmaRequest(
    text_prompt="Evalúa esta posible lesión por presión",
    medical_context=context,
    inference_mode=InferenceMode.TEXT_ONLY
)
```

### 3. Análisis Multimodal (con imagen)

```python
request = MedGemmaRequest(
    text_prompt="Analiza esta imagen médica y describe los hallazgos",
    image_path="/path/to/medical_image.jpg",
    inference_mode=InferenceMode.IMAGE_TEXT,
    max_tokens=300
)
```

### 4. Demo Completo

```bash
python examples/medgemma_local_demo.py
```

## 📊 Monitoreo y Estadísticas

```python
# Obtener estadísticas
stats = await client.get_stats()
print(f"Consultas procesadas: {stats['requests_processed']}")
print(f"Tiempo promedio: {stats['average_processing_time']:.2f}s")
print(f"Cache hit rate: {stats['cache_hit_rate']:.2%}")
print(f"Memoria GPU: {stats['memory_usage']['cuda_allocated']:.1f}GB")
```

## 🛠️ Troubleshooting

### Error: "CUDA out of memory"

```bash
# Solución 1: Usar quantización
config.quantization = True

# Solución 2: Reducir max_tokens
request.max_tokens = 100

# Solución 3: Limpiar cache
torch.cuda.empty_cache()
```

### Error: "Model not found"

```bash
# Re-descargar modelo
python scripts/setup_medgemma_local.py --model 4b --download

# Verificar ubicación
ls ~/.cache/huggingface/transformers/
```

### Error: "Transformers version"

```bash
# Actualizar transformers
pip install transformers>=4.50.0 --upgrade
```

### Performance Lenta

```bash
# Verificar device
print(f"Device: {client.device}")

# Usar GPU si disponible
config.device = "cuda"

# Habilitar quantización
config.quantization = True
```

### Problemas de Memoria

```bash
# Monitorear memoria
nvidia-smi

# Limpiar cache entre consultas
await client.cleanup()
```

## 🔧 Configuración Avanzada

### Variables de Entorno

```bash
# Cache personalizado
export TRANSFORMERS_CACHE="/custom/path/cache"

# Device específico
export CUDA_VISIBLE_DEVICES="0"

# Logging
export TRANSFORMERS_VERBOSITY="error"
```

### Optimización de Performance

```python
# Para batch processing
config = MedGemmaConfig(
    model_name=MedGemmaModel.MEDGEMMA_4B_IT,
    device="cuda",
    quantization=True,
    torch_dtype="bfloat16",
    max_tokens=150,  # Limitar para mayor velocidad
    temperature=0.7
)
```

### Fine-tuning (Avanzado)

```python
# Para fine-tuning personalizado
config = MedGemmaConfig(
    model_name=MedGemmaModel.MEDGEMMA_4B_PT,  # Pre-trained
    device="cuda",
    quantization=False,  # Sin quantización para training
    torch_dtype="float32"
)
```

## 📈 Benchmarks

### Performance Típica (RTX 4080)

| Modelo | Tokens/seg | Memoria | Latencia |
|--------|------------|---------|----------|
| 4B (sin quant) | ~50 | 8GB | 2-4s |
| 4B (con quant) | ~40 | 6GB | 2-5s |
| 27B (sin quant) | ~20 | 32GB | 5-10s |

### Comparación vs API

| Métrica | Local | API |
|---------|-------|-----|
| Primera consulta | 3-5s | 2-8s |
| Consultas cached | 0.1s | 2-8s |
| Costo por 1000 consultas | $0 | $10-50 |
| Privacidad | 100% | Depende |

## 🔒 Consideraciones de Seguridad

### Datos Médicos
- ✅ Todos los datos permanecen locales
- ✅ No hay transmisión a servicios externos
- ✅ Compatible con HIPAA/GDPR out-of-the-box
- ✅ Control total sobre logs y audit trails

### Modelo
- ⚠️ MedGemma no es "clinical-grade" por defecto
- ⚠️ Requiere validación médica antes de producción
- ⚠️ Debe complementarse con supervisión humana
- ✅ Diseñado específicamente para casos médicos

## 📚 Recursos Adicionales

- [MedGemma Official Documentation](https://developers.google.com/health-ai-developer-foundations/medgemma)
- [Hugging Face Model Hub](https://huggingface.co/collections/google/medgemma-release-680aade845f90bec6a3f60c4)
- [Fine-tuning Guide](https://github.com/google-deepmind/gemma/blob/main/examples/medgemma_fine_tuning.ipynb)
- [Vigia Medical Knowledge System](./medical_knowledge_system.md)

## 🆘 Soporte

Para problemas específicos:

1. **Verificar logs**: `tail -f logs/medgemma_local_client.log`
2. **Diagnosticar hardware**: `python scripts/setup_medgemma_local.py --check-only`
3. **Limpiar instalación**: Eliminar `~/.cache/huggingface/`
4. **Reportar issues**: [GitHub Issues](../../issues)

---

**Importante**: MedGemma Local es una herramienta poderosa pero debe usarse con supervisión médica apropiada en entornos de producción clínica.