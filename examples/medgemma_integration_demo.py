#!/usr/bin/env python3
"""
Demo de integración MedGemma en Vigia
Ejemplo de uso del sistema de triage mejorado con análisis médico AI.
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

# Agregar path del proyecto
sys.path.append(str(Path(__file__).parent.parent))

from vigia_detect.core.triage_engine import MedicalTriageEngine
from vigia_detect.core.input_packager import InputPackager, InputType
from vigia_detect.ai.medgemma_client import MedicalContext
from config.settings import get_settings

settings = get_settings()


async def demo_basic_triage():
    """Demo del triage básico (sin MedGemma)"""
    print("🔍 DEMO: Triage Básico (Reglas + Patrones)")
    print("=" * 50)
    
    # Inicializar motor de triage básico
    triage_engine = MedicalTriageEngine(use_medgemma=False)
    
    # Crear input estandarizado
    packager = InputPackager()
    
    input_data = {
        "text": "Hola doctora, tengo una úlcera en el talón que me duele mucho y está sangrando un poco. ¿Es grave?",
        "session_id": "demo-basic-001",
        "timestamp": datetime.now(),
        "source": "whatsapp"
    }
    
    standardized_input = await packager.package_input(
        input_data, InputType.TEXT_MESSAGE
    )
    
    # Realizar triage básico
    result = await triage_engine.perform_triage(standardized_input)
    
    print(f"✅ Resultado del Triage Básico:")
    print(f"   Urgencia: {result.urgency.value}")
    print(f"   Contexto: {result.context.value}")
    print(f"   Confianza: {result.confidence:.2f}")
    print(f"   Reglas aplicadas: {result.matched_rules}")
    print(f"   Ruta recomendada: {result.recommended_route}")
    print(f"   Flags clínicos: {result.clinical_flags}")
    print(f"   Requiere revisión humana: {result.requires_human_review}")
    print(f"   Explicación: {result.explanation}")
    print()


async def demo_enhanced_triage():
    """Demo del triage mejorado con MedGemma"""
    print("🧠 DEMO: Triage Mejorado (MedGemma + IA Médica)")
    print("=" * 50)
    
    # Verificar si MedGemma está habilitado
    if not settings.medgemma_enabled:
        print("⚠️  MedGemma no está habilitado en la configuración.")
        print("   Para habilitar, configura: MEDGEMMA_ENABLED=true")
        print("   Y configura tu GOOGLE_API_KEY")
        return
    
    # Inicializar motor de triage mejorado
    triage_engine = MedicalTriageEngine(use_medgemma=True)
    
    # Crear input estandarizado con contexto médico
    packager = InputPackager()
    
    input_data = {
        "text": "Doctora, mi abuela de 85 años tiene una lesión en el coxis que empezó como una mancha roja y ahora tiene una abertura profunda. Está postrada en cama desde hace 3 meses por fractura de cadera. Le duele mucho cuando la movemos y hoy noté que huele mal. ¿Debo llevarla al hospital?",
        "session_id": "demo-enhanced-001", 
        "timestamp": datetime.now(),
        "source": "whatsapp",
        "metadata": {
            "patient_age": 85,
            "medical_history": ["fractura_cadera", "inmovilidad_prolongada"],
            "mobility_status": "postrada_en_cama",
            "risk_factors": ["edad_avanzada", "inmovilidad", "fractura_reciente"],
            "has_media": False
        }
    }
    
    standardized_input = await packager.package_input(
        input_data, InputType.TEXT_MESSAGE
    )
    
    # Realizar triage mejorado
    print("🔄 Procesando con MedGemma...")
    result = await triage_engine.perform_enhanced_triage(standardized_input)
    
    print(f"✅ Resultado del Triage Mejorado:")
    print(f"   Urgencia: {result.urgency.value}")
    print(f"   Contexto: {result.context.value}")
    print(f"   Confianza: {result.confidence:.2f}")
    print(f"   Reglas aplicadas: {result.matched_rules}")
    print(f"   Ruta recomendada: {result.recommended_route}")
    print(f"   Flags clínicos: {result.clinical_flags}")
    print(f"   Requiere revisión humana: {result.requires_human_review}")
    print(f"   Explicación: {result.explanation}")
    
    # Mostrar metadata de MedGemma si está disponible
    if result.metadata and "medgemma_analysis" in result.metadata:
        medgemma_data = result.metadata["medgemma_analysis"]
        print(f"\n🧠 Análisis MedGemma:")
        print(f"   Nivel de urgencia: {medgemma_data.get('urgency_level')}")
        print(f"   Disposición: {medgemma_data.get('disposition')}")
        print(f"   Confianza MedGemma: {medgemma_data.get('confidence', 0):.2f}")
        print(f"   Razonamiento clínico: {medgemma_data.get('clinical_reasoning', 'No disponible')}")
    
    print()


async def demo_lpp_analysis():
    """Demo de análisis específico de LPP con MedGemma"""
    print("🩺 DEMO: Análisis LPP Especializado")
    print("=" * 50)
    
    if not settings.medgemma_enabled:
        print("⚠️  MedGemma no está habilitado en la configuración.")
        return
    
    try:
        from vigia_detect.ai.medgemma_client import MedGemmaClient, MedicalContext
        
        # Inicializar cliente MedGemma
        medgemma_client = MedGemmaClient()
        
        # Contexto médico del paciente
        medical_context = MedicalContext(
            patient_age=78,
            medical_history=["diabetes_tipo2", "insuficiencia_cardiaca"],
            current_medications=["metformina", "enalapril", "furosemida"],
            mobility_status="ambulatorio_limitado",
            risk_factors=["diabetes", "edad_avanzada", "edema"],
            previous_lpp_history=False
        )
        
        # Observaciones clínicas
        clinical_observations = """
        Paciente de 78 años con lesión en región sacra de aproximadamente 3 cm de diámetro.
        La lesión presenta pérdida de espesor completo de la piel con exposición del tejido subcutáneo.
        Bordes bien definidos, lecho de la herida con tejido de granulación rojo y pequeñas áreas de esfacelo.
        Exudado seroso moderado, sin mal olor. Piel circundante eritematosa pero sin induración.
        Paciente refiere dolor 6/10 durante la limpieza, mejora con analgésicos.
        """
        
        # Hallazgos visuales simulados (del pipeline de CV)
        visual_findings = {
            "detections": ["lesion_sacra"],
            "features": {
                "diameter_cm": 3.2,
                "depth": "full_thickness",
                "tissue_type": "granulation_with_slough"
            },
            "confidence": 0.87
        }
        
        print("🔄 Analizando hallazgos de LPP con MedGemma...")
        
        # Realizar análisis de LPP
        lpp_analysis = await medgemma_client.analyze_lpp_findings(
            clinical_observations=clinical_observations,
            visual_findings=visual_findings,
            medical_context=medical_context
        )
        
        if lpp_analysis:
            print(f"✅ Análisis de LPP completado:")
            print(f"   Tipo de análisis: {lpp_analysis.analysis_type.value}")
            print(f"   Confianza: {lpp_analysis.confidence_score:.2f}")
            print(f"   Nivel de riesgo: {lpp_analysis.risk_level}")
            print(f"   Seguimiento necesario: {lpp_analysis.follow_up_needed}")
            
            print(f"\n📋 Hallazgos clínicos:")
            for key, value in lpp_analysis.clinical_findings.items():
                print(f"   {key}: {value}")
            
            print(f"\n💡 Recomendaciones:")
            for rec in lpp_analysis.recommendations:
                print(f"   • {rec}")
            
            if lpp_analysis.audit_trail:
                print(f"\n📝 Información de auditoría:")
                for key, value in lpp_analysis.audit_trail.items():
                    print(f"   {key}: {value}")
        else:
            print("❌ No se pudo completar el análisis de LPP")
            
    except Exception as e:
        print(f"❌ Error en el análisis LPP: {e}")
    
    print()


async def demo_comparison():
    """Demo comparativo: Triage básico vs mejorado"""
    print("⚖️  DEMO: Comparación Triage Básico vs Mejorado")
    print("=" * 50)
    
    # Caso clínico complejo
    complex_case = {
        "text": "Doctor, soy enfermera en un hogar de ancianos. Tengo un paciente de 92 años con demencia que desarrolló una lesión profunda en el talón derecho. La lesión tiene tejido negro en el centro y está sangrando. El paciente no puede comunicar dolor pero se agita cuando tocamos el área. Tiene antecedentes de diabetes y problemas circulatorios. ¿Qué tan urgente es esto?",
        "session_id": "demo-comparison-001",
        "timestamp": datetime.now(),
        "source": "whatsapp",
        "metadata": {
            "patient_age": 92,
            "medical_history": ["demencia", "diabetes", "enfermedad_vascular_periferica"],
            "mobility_status": "postrado",
            "risk_factors": ["edad_muy_avanzada", "diabetes", "inmovilidad", "demencia"],
            "previous_lpp_history": True,
            "has_media": False
        }
    }
    
    packager = InputPackager()
    standardized_input = await packager.package_input(
        complex_case, InputType.TEXT_MESSAGE
    )
    
    # Triage básico
    print("🔍 Triage Básico:")
    basic_engine = MedicalTriageEngine(use_medgemma=False)
    basic_result = await basic_engine.perform_triage(standardized_input)
    
    print(f"   Urgencia: {basic_result.urgency.value}")
    print(f"   Confianza: {basic_result.confidence:.2f}")
    print(f"   Ruta: {basic_result.recommended_route}")
    print(f"   Humano requerido: {basic_result.requires_human_review}")
    
    # Triage mejorado (si está disponible)
    if settings.medgemma_enabled:
        print("\n🧠 Triage Mejorado con MedGemma:")
        enhanced_engine = MedicalTriageEngine(use_medgemma=True)
        enhanced_result = await enhanced_engine.perform_enhanced_triage(standardized_input)
        
        print(f"   Urgencia: {enhanced_result.urgency.value}")
        print(f"   Confianza: {enhanced_result.confidence:.2f}")
        print(f"   Ruta: {enhanced_result.recommended_route}")
        print(f"   Humano requerido: {enhanced_result.requires_human_review}")
        
        # Comparación
        print(f"\n📊 Diferencias:")
        print(f"   Mejora en confianza: {enhanced_result.confidence - basic_result.confidence:.2f}")
        print(f"   Cambio de urgencia: {basic_result.urgency.value} → {enhanced_result.urgency.value}")
        
        if enhanced_result.metadata and "medgemma_analysis" in enhanced_result.metadata:
            print(f"   Análisis MedGemma disponible: ✅")
        else:
            print(f"   Análisis MedGemma disponible: ❌")
    else:
        print("\n⚠️  Triage mejorado no disponible (MedGemma no configurado)")
    
    print()


async def main():
    """Función principal del demo"""
    print("🏥 VIGIA - DEMO INTEGRACIÓN MEDGEMMA")
    print("=" * 60)
    print(f"Configuración actual:")
    print(f"   MedGemma habilitado: {settings.medgemma_enabled}")
    print(f"   Modelo MedGemma: {settings.medgemma_model}")
    print(f"   Google Cloud Project: {settings.google_cloud_project}")
    print()
    
    try:
        # Ejecutar demos
        await demo_basic_triage()
        await demo_enhanced_triage()
        await demo_lpp_analysis()
        await demo_comparison()
        
        print("✅ Demo completado exitosamente")
        
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante el demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Configurar logging básico
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Ejecutar demo
    asyncio.run(main())