#!/usr/bin/env python3
"""
Demo simplificado de integración MedGemma en Vigia
Este demo muestra el funcionamiento básico sin dependencias complejas.
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Agregar path del proyecto  
sys.path.append(str(Path(__file__).parent.parent))

# Importaciones mínimas necesarias
import logging
logging.basicConfig(level=logging.INFO)


async def demo_medgemma_basic():
    """Demo básico de MedGemma sin dependencias complejas"""
    print("🧠 DEMO SIMPLIFICADO: MedGemma Integration")
    print("=" * 60)
    
    try:
        # Importar solo lo necesario
        from vigia_detect.ai.medgemma_client import MedGemmaClient, MedicalContext, MedicalAnalysisType
        
        print("✅ MedGemma client importado correctamente")
        
        # Crear cliente
        client = MedGemmaClient()
        print("✅ Cliente MedGemma inicializado")
        
        # Crear contexto médico de prueba
        medical_context = MedicalContext(
            patient_age=75,
            medical_history=["diabetes", "hipertensión"],
            current_medications=["metformina", "losartán"],
            mobility_status="parcialmente_móvil",
            risk_factors=["edad_avanzada", "diabetes", "movilidad_reducida"],
            previous_lpp_history=False
        )
        
        print("\n📋 Caso clínico de prueba:")
        print("   Paciente de 75 años con diabetes e hipertensión")
        print("   Presenta lesión en región sacra con signos de presión")
        
        # Observaciones clínicas
        clinical_observations = """
        Paciente de 75 años con lesión en zona sacra. La lesión presenta:
        - Eritema no blanqueable de 4x3 cm
        - Piel intacta pero con cambio de coloración
        - Dolor localizado al tacto (escala 4/10)
        - Zona caliente al tacto
        - Sin exudado ni mal olor
        El paciente pasa largos períodos sentado debido a movilidad limitada.
        """
        
        print("\n🔄 Analizando con MedGemma...")
        
        # Realizar análisis de LPP
        result = await client.analyze_lpp_findings(
            clinical_observations=clinical_observations,
            medical_context=medical_context
        )
        
        if result:
            print("\n✅ Análisis completado exitosamente:")
            print(f"   Confianza: {result.confidence_score:.2%}")
            print(f"   Nivel de riesgo: {result.risk_level}")
            print(f"   Seguimiento necesario: {'Sí' if result.follow_up_needed else 'No'}")
            
            print("\n📊 Hallazgos clínicos:")
            for key, value in result.clinical_findings.items():
                if value:
                    print(f"   • {key}: {value}")
            
            print("\n💡 Recomendaciones:")
            for rec in result.recommendations[:3]:  # Mostrar solo las primeras 3
                print(f"   • {rec}")
                
        else:
            print("❌ No se pudo completar el análisis")
            
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("   Asegúrate de tener configurado Google Generative AI")
    except Exception as e:
        print(f"❌ Error durante el demo: {e}")
        import traceback
        traceback.print_exc()


async def demo_triage_simple():
    """Demo simple de triage sin todas las dependencias"""
    print("\n🔍 DEMO: Análisis de Triage Médico")
    print("=" * 60)
    
    try:
        from vigia_detect.ai.medgemma_client import MedGemmaClient
        
        client = MedGemmaClient()
        
        # Caso de urgencia para triage
        patient_message = """
        Doctora, mi madre de 82 años tiene una herida en el talón que no mejora.
        Empezó hace 2 semanas como una ampolla y ahora es una úlcera profunda.
        Está sangrando un poco y huele mal. Tiene diabetes desde hace 20 años.
        ¿Debo llevarla a urgencias o puedo esperar a la cita del lunes?
        """
        
        symptoms = "Úlcera en talón con mal olor, sangrado leve, paciente diabética"
        
        print("📋 Mensaje del paciente recibido")
        print("🔄 Realizando triage clínico...")
        
        result = await client.perform_clinical_triage(
            patient_message=patient_message,
            symptoms_description=symptoms
        )
        
        if result:
            findings = result.clinical_findings
            print(f"\n✅ Triage completado:")
            print(f"   Nivel de urgencia: {findings.get('urgency_level', 'No determinado')}")
            print(f"   Confianza: {result.confidence_score:.2%}")
            
            if findings.get('alarm_signs'):
                print("\n⚠️  Signos de alarma detectados:")
                for sign in findings['alarm_signs']:
                    print(f"   • {sign}")
            
            print(f"\n🏥 Recomendación: {findings.get('recommended_care_level', 'Evaluación médica')}")
            print(f"   Tiempo recomendado: Dentro de {findings.get('timeframe_hours', 24)} horas")
            
            if result.recommendations:
                print("\n📋 Acciones inmediatas:")
                for action in result.recommendations[:3]:
                    print(f"   • {action}")
                    
        else:
            print("❌ No se pudo completar el triage")
            
    except Exception as e:
        print(f"❌ Error en el triage: {e}")


async def demo_health_check():
    """Verificar estado del cliente MedGemma"""
    print("\n🏥 HEALTH CHECK: MedGemma Service")
    print("=" * 60)
    
    try:
        from vigia_detect.ai.medgemma_client import MedGemmaClient
        from config.settings import get_settings
        
        settings = get_settings()
        
        print(f"📋 Configuración actual:")
        print(f"   MedGemma habilitado: {getattr(settings, 'medgemma_enabled', False)}")
        print(f"   Modelo: {getattr(settings, 'medgemma_model', 'No configurado')}")
        print(f"   Google API Key: {'Configurada' if getattr(settings, 'google_api_key', None) else 'No configurada'}")
        
        client = MedGemmaClient()
        health = await client.health_check()
        
        print(f"\n✅ Estado del servicio:")
        print(f"   Status: {health.get('status', 'unknown')}")
        print(f"   Modelo: {health.get('model', 'No disponible')}")
        print(f"   Timestamp: {health.get('timestamp', 'N/A')}")
        
        if health.get('status') == 'healthy':
            print("\n🎉 MedGemma está funcionando correctamente!")
        else:
            print(f"\n⚠️  MedGemma presenta problemas: {health.get('error', 'Error desconocido')}")
            
    except Exception as e:
        print(f"❌ Error en health check: {e}")


async def main():
    """Función principal del demo simplificado"""
    print("🏥 VIGIA - DEMO MEDGEMMA SIMPLIFICADO")
    print("=" * 60)
    print("Este demo muestra la funcionalidad básica de MedGemma")
    print("sin requerir todas las dependencias del sistema completo.\n")
    
    try:
        # Ejecutar demos en orden
        await demo_health_check()
        await demo_medgemma_basic()
        await demo_triage_simple()
        
        print("\n✅ Demo completado exitosamente")
        print("\n💡 Para usar MedGemma en producción:")
        print("   1. Configura GOOGLE_API_KEY en tu archivo .env")
        print("   2. Establece MEDGEMMA_ENABLED=true")
        print("   3. Opcionalmente ajusta MEDGEMMA_MODEL (default: gemini-1.5-pro)")
        
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante el demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())