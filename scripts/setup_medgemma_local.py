#!/usr/bin/env python3
"""
Setup MedGemma Local - Script para configurar MedGemma localmente
Descarga y configura modelos MedGemma desde Hugging Face para uso local.

Uso:
    python scripts/setup_medgemma_local.py --model 4b --download
    python scripts/setup_medgemma_local.py --model 27b --check-only
"""

import os
import sys
import argparse
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Agregar path del proyecto
sys.path.append(str(Path(__file__).parent.parent))

from vigia_detect.ai.medgemma_local_client import (
    MedGemmaLocalClient,
    MedGemmaConfig,
    MedGemmaModel,
    MedGemmaLocalFactory
)
from vigia_detect.utils.secure_logger import SecureLogger

logger = SecureLogger("medgemma_setup")


class MedGemmaSetup:
    """Configurador de MedGemma local."""
    
    def __init__(self):
        self.models_dir = Path.home() / ".cache" / "huggingface" / "transformers"
        self.config_file = Path(__file__).parent.parent / "config" / "medgemma_config.json"
        
    def check_requirements(self) -> Dict[str, Any]:
        """Verificar requisitos del sistema."""
        print("🔍 Verificando requisitos del sistema...")
        
        requirements = MedGemmaLocalFactory.check_requirements()
        
        print(f"✅ PyTorch disponible: {requirements['torch_available']}")
        print(f"✅ Transformers disponible: {requirements['transformers_available']}")
        print(f"🎮 CUDA disponible: {requirements['cuda_available']}")
        print(f"💾 Memoria suficiente: {requirements['sufficient_memory']}")
        
        if requirements['cuda_available']:
            import torch
            device_name = torch.cuda.get_device_name(0)
            memory_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"   GPU: {device_name}")
            print(f"   Memoria GPU: {memory_gb:.1f} GB")
        
        return requirements
    
    def install_dependencies(self):
        """Instalar dependencias necesarias."""
        print("📦 Instalando dependencias...")
        
        dependencies = [
            "torch>=2.0.0",
            "transformers>=4.50.0",
            "accelerate",
            "bitsandbytes",  # Para quantización
            "pillow",  # Para procesamiento de imágenes
            "sentencepiece",  # Para tokenización
        ]
        
        for dep in dependencies:
            print(f"   Instalando {dep}...")
            os.system(f"pip install '{dep}' --quiet")
        
        print("✅ Dependencias instaladas")
    
    def download_model(self, model_size: str) -> bool:
        """Descargar modelo MedGemma."""
        model_map = {
            "4b": MedGemmaModel.MEDGEMMA_4B_IT,
            "4b-pt": MedGemmaModel.MEDGEMMA_4B_PT,
            "27b": MedGemmaModel.MEDGEMMA_27B_TEXT
        }
        
        if model_size not in model_map:
            print(f"❌ Modelo '{model_size}' no válido. Opciones: {list(model_map.keys())}")
            return False
        
        model = model_map[model_size]
        print(f"📥 Descargando modelo {model.value}...")
        
        try:
            # Importar aquí para evitar errores si no están instaladas las dependencias
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            # Crear directorio de cache si no existe
            cache_dir = self.models_dir / model.value.replace("/", "_")
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            print("   Descargando tokenizer...")
            tokenizer = AutoTokenizer.from_pretrained(
                model.value,
                cache_dir=str(cache_dir)
            )
            
            print("   Descargando modelo (esto puede tomar varios minutos)...")
            model_obj = AutoModelForCausalLM.from_pretrained(
                model.value,
                cache_dir=str(cache_dir),
                torch_dtype="auto"  # Detectar automáticamente
            )
            
            print(f"✅ Modelo {model.value} descargado exitosamente")
            print(f"   Ubicación: {cache_dir}")
            
            # Guardar configuración
            self._save_model_config(model, str(cache_dir))
            
            return True
            
        except Exception as e:
            print(f"❌ Error descargando modelo: {e}")
            return False
    
    def _save_model_config(self, model: MedGemmaModel, cache_dir: str):
        """Guardar configuración del modelo."""
        config = {
            "model_name": model.value,
            "cache_dir": cache_dir,
            "downloaded_at": str(asyncio.get_event_loop().time()),
            "local_files_only": True
        }
        
        # Crear directorio de configuración
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"📝 Configuración guardada en {self.config_file}")
    
    def check_model_availability(self, model_size: str) -> bool:
        """Verificar si el modelo está disponible localmente."""
        model_map = {
            "4b": MedGemmaModel.MEDGEMMA_4B_IT,
            "4b-pt": MedGemmaModel.MEDGEMMA_4B_PT,
            "27b": MedGemmaModel.MEDGEMMA_27B_TEXT
        }
        
        if model_size not in model_map:
            return False
        
        model = model_map[model_size]
        cache_dir = self.models_dir / model.value.replace("/", "_")
        
        # Verificar archivos esenciales
        essential_files = [
            "config.json",
            "tokenizer.json",
            "pytorch_model.bin"  # o model.safetensors
        ]
        
        for file in essential_files:
            if not (cache_dir / file).exists():
                # Probar con safetensors
                if file == "pytorch_model.bin" and (cache_dir / "model.safetensors").exists():
                    continue
                print(f"❌ Archivo faltante: {file}")
                return False
        
        print(f"✅ Modelo {model.value} disponible localmente")
        return True
    
    async def test_model(self, model_size: str) -> bool:
        """Probar modelo descargado."""
        model_map = {
            "4b": MedGemmaModel.MEDGEMMA_4B_IT,
            "4b-pt": MedGemmaModel.MEDGEMMA_4B_PT,
            "27b": MedGemmaModel.MEDGEMMA_27B_TEXT
        }
        
        if model_size not in model_map:
            return False
        
        print(f"🧪 Probando modelo {model_size}...")
        
        try:
            # Configurar cliente
            config = MedGemmaConfig(
                model_name=model_map[model_size],
                local_files_only=True,
                max_tokens=50  # Corto para prueba rápida
            )
            
            # Crear cliente
            client = MedGemmaLocalClient(config)
            await client.initialize()
            
            # Probar conexión
            is_valid = await client.validate_connection()
            
            if is_valid:
                print("✅ Modelo funcionando correctamente")
                
                # Mostrar estadísticas
                stats = await client.get_stats()
                print(f"   Dispositivo: {stats['device']}")
                print(f"   Memoria GPU: {stats.get('memory_usage', {})}")
            else:
                print("❌ Modelo no responde correctamente")
            
            # Limpiar
            await client.cleanup()
            
            return is_valid
            
        except Exception as e:
            print(f"❌ Error probando modelo: {e}")
            return False
    
    def list_models(self):
        """Listar modelos disponibles."""
        print("📋 Modelos MedGemma disponibles:")
        print()
        
        models_info = [
            {
                "size": "4b",
                "name": "google/medgemma-4b-it",
                "type": "Multimodal (texto + imagen)",
                "memory": "~8GB GPU",
                "description": "Modelo instruction-tuned para texto e imágenes médicas"
            },
            {
                "size": "4b-pt",
                "name": "google/medgemma-4b-pt",
                "type": "Multimodal (pre-trained)",
                "memory": "~8GB GPU",
                "description": "Modelo pre-entrenado para fine-tuning"
            },
            {
                "size": "27b",
                "name": "google/medgemma-27b-text-it",
                "type": "Solo texto",
                "memory": "~32GB GPU",
                "description": "Modelo grande instruction-tuned solo para texto"
            }
        ]
        
        for model in models_info:
            print(f"🔸 {model['size']}: {model['name']}")
            print(f"   Tipo: {model['type']}")
            print(f"   Memoria: {model['memory']}")
            print(f"   Descripción: {model['description']}")
            
            # Verificar disponibilidad
            if self.check_model_availability(model['size']):
                print("   Estado: ✅ Disponible localmente")
            else:
                print("   Estado: ❌ No descargado")
            print()
    
    def get_recommended_model(self) -> str:
        """Obtener modelo recomendado según hardware."""
        requirements = self.check_requirements()
        
        if not requirements['cuda_available']:
            print("💡 Recomendación: Modelo 4b (CPU)")
            return "4b"
        
        try:
            import torch
            memory_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
            
            if memory_gb >= 32:
                print("💡 Recomendación: Modelo 27b (GPU con mucha memoria)")
                return "27b"
            elif memory_gb >= 8:
                print("💡 Recomendación: Modelo 4b (GPU estándar)")
                return "4b"
            else:
                print("💡 Recomendación: Modelo 4b con quantización (GPU limitada)")
                return "4b"
                
        except Exception:
            return "4b"


async def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description="Configurar MedGemma local")
    parser.add_argument("--model", choices=["4b", "4b-pt", "27b"], 
                       help="Modelo a descargar/verificar")
    parser.add_argument("--download", action="store_true",
                       help="Descargar modelo")
    parser.add_argument("--test", action="store_true",
                       help="Probar modelo")
    parser.add_argument("--check-only", action="store_true",
                       help="Solo verificar requisitos")
    parser.add_argument("--list", action="store_true",
                       help="Listar modelos disponibles")
    parser.add_argument("--install-deps", action="store_true",
                       help="Instalar dependencias")
    
    args = parser.parse_args()
    
    setup = MedGemmaSetup()
    
    print("🤖 MedGemma Local Setup")
    print("=" * 50)
    
    if args.list:
        setup.list_models()
        return
    
    if args.install_deps:
        setup.install_dependencies()
        return
    
    # Verificar requisitos
    requirements = setup.check_requirements()
    
    if args.check_only:
        return
    
    if not requirements['torch_available'] or not requirements['transformers_available']:
        print("❌ Dependencias faltantes. Ejecuta: --install-deps")
        return
    
    if not args.model:
        # Recomendar modelo
        recommended = setup.get_recommended_model()
        print(f"💡 Usar: --model {recommended}")
        return
    
    if args.download:
        print(f"📥 Descargando modelo {args.model}...")
        success = setup.download_model(args.model)
        if not success:
            return
    
    if args.test:
        print(f"🧪 Probando modelo {args.model}...")
        success = await setup.test_model(args.model)
        if success:
            print("✅ Modelo listo para usar")
        else:
            print("❌ Modelo no funciona correctamente")


if __name__ == "__main__":
    asyncio.run(main())