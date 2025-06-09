#!/usr/bin/env python3
"""
Demo MedGemma Local - Demostración de MedGemma ejecutando localmente
Ejemplo completo de uso de MedGemma local para análisis médico.

Requisitos:
1. Ejecutar: python scripts/setup_medgemma_local.py --install-deps
2. Ejecutar: python scripts/setup_medgemma_local.py --model 4b --download
3. Ejecutar: python examples/medgemma_local_demo.py
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any

# Agregar path del proyecto
sys.path.append(str(Path(__file__).parent.parent))

from vigia_detect.ai.medgemma_local_client import (
    MedGemmaLocalClient,
    MedGemmaConfig,
    MedGemmaModel,
    MedGemmaRequest,
    MedicalContext,
    InferenceMode,
    MedGemmaLocalFactory
)


class MedGemmaLocalDemo:
    """Demo de MedGemma Local."""
    
    def __init__(self):
        self.client = None
    
    async def initialize(self):
        """Inicializar cliente MedGemma."""
        print("🤖 Inicializando MedGemma Local...")
        
        # Verificar requisitos
        requirements = MedGemmaLocalFactory.check_requirements()
        
        if not requirements['torch_available']:
            print("❌ PyTorch no disponible. Instalar con: pip install torch")
            return False
        
        if not requirements['transformers_available']:
            print("❌ Transformers no disponible. Instalar con: pip install transformers")
            return False
        
        print("✅ Requisitos verificados")
        
        # Configurar cliente
        config = MedGemmaConfig(
            model_name=MedGemmaModel.MEDGEMMA_4B_IT,
            device="auto",  # auto-detectar mejor dispositivo
            quantization=True,  # Usar quantización para menor memoria
            max_tokens=200,
            temperature=0.7,
            local_files_only=True  # Solo usar archivos descargados
        )
        
        try:
            self.client = await MedGemmaLocalFactory.create_client(config)
            print("✅ MedGemma Local inicializado correctamente")
            
            # Mostrar estadísticas
            stats = await self.client.get_stats()
            print(f"   Modelo: {stats['model_name']}")
            print(f"   Dispositivo: {stats['device']}")
            
            if 'memory_usage' in stats:
                memory = stats['memory_usage']
                if 'cuda_allocated' in memory:
                    print(f"   Memoria GPU: {memory['cuda_allocated']:.1f} GB")
            
            return True
            
        except Exception as e:
            print(f"❌ Error inicializando MedGemma: {e}")
            print("💡 Asegúrate de haber descargado el modelo con:")
            print("   python scripts/setup_medgemma_local.py --model 4b --download")
            return False
    
    async def demo_basic_consultation(self):
        """Demo de consulta médica básica."""
        print("\n" + "="*60)
        print("🩺 DEMO 1: Consulta Médica Básica")
        print("="*60)
        
        request = MedGemmaRequest(
            text_prompt="¿Cuáles son los signos de una lesión por presión grado 2?",
            inference_mode=InferenceMode.TEXT_ONLY,
            max_tokens=150
        )
        
        print(f"Consulta: {request.text_prompt}")
        print("\n🤖 Respuesta de MedGemma:")
        print("-" * 40)
        
        response = await self.client.generate_medical_response(request)
        
        if response.success:
            print(response.generated_text)
            print(f"\n📊 Confianza: {response.confidence_score:.2f}")
            print(f"⏱️ Tiempo: {response.processing_time:.2f}s")
            
            if response.warnings:
                print(f"⚠️ Advertencias: {', '.join(response.warnings)}")
        else:
            print(f"❌ Error: {response.error_message}")
    
    async def demo_with_context(self):
        """Demo con contexto médico."""
        print("\n" + "="*60)
        print("🏥 DEMO 2: Consulta con Contexto Médico")
        print("="*60)
        
        # Crear contexto médico
        context = MedicalContext(
            patient_age=75,
            patient_gender="femenino",
            medical_history="Diabetes tipo 2, hipertensión arterial",
            current_medications=["Metformina", "Enalapril"],
            symptoms="Eritema en región sacra, no blanqueable",
            urgency_level="urgent"
        )
        
        request = MedGemmaRequest(
            text_prompt="Evalúa esta posible lesión por presión y recomienda tratamiento",
            medical_context=context,
            inference_mode=InferenceMode.TEXT_ONLY,
            max_tokens=250
        )
        
        print("👤 Contexto del paciente:")
        print(f"   Edad: {context.patient_age} años")
        print(f"   Género: {context.patient_gender}")
        print(f"   Historia: {context.medical_history}")
        print(f"   Medicamentos: {', '.join(context.current_medications)}")
        print(f"   Síntomas: {context.symptoms}")
        print(f"   Urgencia: {context.urgency_level}")
        
        print(f"\nConsulta: {request.text_prompt}")
        print("\n🤖 Respuesta de MedGemma:")
        print("-" * 40)
        
        response = await self.client.generate_medical_response(request)
        
        if response.success:
            print(response.generated_text)
            
            print(f"\n📊 Análisis médico:")
            analysis = response.medical_analysis
            print(f"   Confianza: {response.confidence_score:.2f}")
            print(f"   Urgencia detectada: {analysis.get('urgency_assessment', 'N/A')}")
            
            if analysis.get('recommendations'):
                print("   Recomendaciones extraídas:")
                for rec in analysis['recommendations'][:3]:
                    print(f"     • {rec}")
            
            print(f"\n⏱️ Tiempo de procesamiento: {response.processing_time:.2f}s")
        else:
            print(f"❌ Error: {response.error_message}")
    
    async def demo_cache_performance(self):
        """Demo de performance con cache."""
        print("\n" + "="*60)
        print("⚡ DEMO 3: Performance y Cache")
        print("="*60)
        
        request = MedGemmaRequest(
            text_prompt="¿Cuál es el protocolo de prevención de LPP en UCI?",
            inference_mode=InferenceMode.TEXT_ONLY,
            max_tokens=100
        )
        
        print("🔄 Primera consulta (sin cache):")
        response1 = await self.client.generate_medical_response(request)
        print(f"   Tiempo: {response1.processing_time:.2f}s")
        
        print("\n🔄 Segunda consulta idéntica (con cache):")
        response2 = await self.client.generate_medical_response(request)
        print(f"   Tiempo: {response2.processing_time:.2f}s")
        
        # Mostrar estadísticas
        stats = await self.client.get_stats()
        print(f"\n📈 Estadísticas:")
        print(f"   Consultas procesadas: {stats['requests_processed']}")
        print(f"   Cache hits: {stats['cache_hits']}")
        print(f"   Tasa de cache: {stats['cache_hit_rate']:.2%}")
        print(f"   Tiempo promedio: {stats['average_processing_time']:.2f}s")
        print(f"   Tokens generados: {stats['total_tokens_generated']}")
    
    async def demo_error_handling(self):
        """Demo de manejo de errores."""
        print("\n" + "="*60)
        print("🛡️ DEMO 4: Manejo de Errores")
        print("="*60)
        
        # Consulta con tokens excesivos
        request = MedGemmaRequest(
            text_prompt="Explica todo sobre medicina",
            inference_mode=InferenceMode.TEXT_ONLY,
            max_tokens=10000  # Excesivo intencionalmente
        )
        
        print("🚫 Consulta con parámetros extremos:")
        response = await self.client.generate_medical_response(request)
        
        if response.success:
            print("✅ Manejado correctamente - respuesta generada")
            print(f"   Longitud: {len(response.generated_text)} caracteres")
        else:
            print(f"❌ Error controlado: {response.error_message}")
        
        # Consulta ambigua
        ambiguous_request = MedGemmaRequest(
            text_prompt="¿Qué hago?",
            inference_mode=InferenceMode.TEXT_ONLY,
            max_tokens=100
        )
        
        print("\n❓ Consulta ambigua:")
        print(f"   Consulta: {ambiguous_request.text_prompt}")
        
        response = await self.client.generate_medical_response(ambiguous_request)
        
        if response.success:
            print(f"   Respuesta: {response.generated_text[:100]}...")
            print(f"   Confianza: {response.confidence_score:.2f}")
            
            if response.warnings:
                print(f"   ⚠️ Advertencias: {', '.join(response.warnings)}")
        else:
            print(f"❌ Error: {response.error_message}")
    
    async def run_all_demos(self):
        """Ejecutar todas las demostraciones."""
        print("🚀 MedGemma Local - Demostración Completa")
        print("="*70)
        
        # Inicializar
        if not await self.initialize():
            return
        
        try:
            # Ejecutar demos
            await self.demo_basic_consultation()
            await self.demo_with_context()
            await self.demo_cache_performance()
            await self.demo_error_handling()
            
            print("\n" + "="*70)
            print("✅ Demostración completada exitosamente")
            
            # Estadísticas finales
            stats = await self.client.get_stats()
            print(f"\n📊 Estadísticas finales:")
            print(f"   Total de consultas: {stats['requests_processed']}")
            print(f"   Tiempo promedio: {stats['average_processing_time']:.2f}s")
            print(f"   Tokens generados: {stats['total_tokens_generated']}")
            print(f"   Errores: {stats['errors']}")
            
        except KeyboardInterrupt:
            print("\n⏹️ Demo interrumpida por usuario")
        
        except Exception as e:
            print(f"\n❌ Error en demo: {e}")
        
        finally:
            # Limpiar recursos
            if self.client:
                await self.client.cleanup()
                print("🧹 Recursos liberados")


async def main():
    """Función principal."""
    demo = MedGemmaLocalDemo()
    await demo.run_all_demos()


if __name__ == "__main__":
    print("🤖 MedGemma Local Demo")
    print("Asegúrate de haber instalado dependencias y descargado el modelo:")
    print("1. python scripts/setup_medgemma_local.py --install-deps")
    print("2. python scripts/setup_medgemma_local.py --model 4b --download")
    print("\nPresiona Ctrl+C para interrumpir en cualquier momento\n")
    
    asyncio.run(main())