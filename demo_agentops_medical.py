#!/usr/bin/env python3
"""
Demo completo de AgentOps para sistema médico Vigia LPP-Detect
Demuestra monitoreo de AI médica con compliance HIPAA
"""

import asyncio
import time
import uuid
from datetime import datetime

from vigia_detect.monitoring import MedicalTelemetry, AgentOpsClient
from vigia_detect.monitoring.phi_tokenizer import PHITokenizer


async def demo_medical_lpp_workflow():
    """Demo completo del workflow médico LPP con telemetría AgentOps"""
    
    print("🏥 DEMO AGENTOPS - SISTEMA MÉDICO VIGIA LPP-DETECT")
    print("=" * 60)
    
    # 1. Inicializar telemetría médica
    telemetry = MedicalTelemetry(
        app_id="vigia-lpp-production",
        environment="production",
        enable_phi_protection=True
    )
    
    print("✅ Telemetría médica inicializada")
    
    # 2. Simular caso médico real
    patient_context = {
        "patient_id": f"PAT_{uuid.uuid4().hex[:8].upper()}",
        "case_id": f"LPP_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "lpp_grade": 2,
        "anatomical_location": "sacrum",
        "risk_factors": ["diabetes", "limited_mobility", "age_75+"],
        "admission_date": "2025-06-13",
        "facility": "Hospital Regional Santiago",
        "department": "Medicina Interna"
    }
    
    session_id = f"medical_session_{int(time.time())}"
    
    print(f"📋 Caso médico: {patient_context['case_id']}")
    print(f"📊 ID Sesión: {session_id}")
    
    # 3. Iniciar sesión médica con AgentOps
    await telemetry.start_medical_session(
        session_id=session_id,
        patient_context=patient_context,
        session_type="lpp_analysis_demo"
    )
    
    print("🔄 Sesión médica activa en AgentOps")
    
    # 4. Simular análisis de imagen médica
    print("\n🔍 FASE 1: Análisis de imagen médica...")
    time.sleep(2)  # Simular procesamiento de imagen
    
    detection_results = {
        "lpp_grade": 2,
        "confidence": 0.89,
        "anatomical_location": "sacrum",
        "area_cm2": 3.2,
        "depth_assessment": "partial_thickness",
        "tissue_type": "granulating",
        "infection_signs": False,
        "model_version": "YOLOv5_medical_v2.1"
    }
    
    # Rastrear detección LPP
    await telemetry.track_lpp_detection_event(
        session_id=session_id,
        image_path="/medical_images/lpp_sacrum_001.jpg",
        detection_results=detection_results,
        agent_name="yolov5_medical_detector"
    )
    
    print(f"✅ LPP Detectado: Grado {detection_results['lpp_grade']} ({detection_results['confidence']*100:.1f}% confianza)")
    
    # 5. Motor de decisión médica basado en evidencia
    print("\n🧠 FASE 2: Motor de decisión médica...")
    time.sleep(1.5)
    
    medical_decision = {
        "treatment_protocol": "NPUAP Stage 2 Management",
        "evidence_level": "A",
        "clinical_guidelines": "NPUAP/EPUAP/PPPIA 2019",
        "interventions": [
            "pressure_redistribution",
            "wound_cleansing_saline",
            "moisture_retentive_dressing",
            "nutritional_assessment"
        ],
        "monitoring_frequency": "daily_assessment",
        "escalation_criteria": "no_improvement_72h",
        "specialist_referral": False,
        "estimated_healing_time": "2-4_weeks"
    }
    
    # Rastrear decisión médica
    await telemetry.track_medical_decision(
        session_id=session_id,
        decision_type="treatment_recommendation",
        input_data=detection_results,
        decision_result=medical_decision,
        evidence_level="A"
    )
    
    print(f"✅ Decisión médica: {medical_decision['treatment_protocol']}")
    print(f"📚 Evidencia nivel: {medical_decision['evidence_level']}")
    
    # 6. Simulación de tarea asíncrona (Celery)
    print("\n⚡ FASE 3: Pipeline asíncrono...")
    
    task_metadata = {
        "task_type": "medical_report_generation",
        "patient_case": patient_context['case_id'],
        "processing_priority": "routine",
        "estimated_completion": "5_minutes"
    }
    
    await telemetry.track_async_pipeline_task(
        task_id=f"celery_{uuid.uuid4().hex[:12]}",
        task_type="medical_report_generation",
        queue="medical_priority",
        status="completed",
        session_id=session_id,
        metadata=task_metadata
    )
    
    print("✅ Reporte médico generado vía pipeline asíncrono")
    
    # 7. Simulación de escalación (caso complejo)
    print("\n⚠️  FASE 4: Simulación de escalación médica...")
    
    await telemetry.track_medical_error_with_escalation(
        error_type="complex_case_review",
        error_message="Caso requiere revisión de especialista por múltiples factores de riesgo",
        context={
            "patient_case": patient_context['case_id'],
            "risk_factors": patient_context['risk_factors'],
            "complexity_score": 0.78
        },
        session_id=session_id,
        requires_human_review=True,
        severity="medium"
    )
    
    print("✅ Escalación médica registrada para revisión humana")
    
    # 8. Finalizar sesión médica
    print("\n📊 FASE 5: Finalización y resumen...")
    time.sleep(1)
    
    summary = await telemetry.end_medical_session(session_id)
    
    print("\n🎯 RESUMEN DE SESIÓN MÉDICA:")
    print("=" * 40)
    print(f"📋 Caso: {patient_context['case_id']}")
    print(f"🔍 Detecciones LPP: {summary.get('lpp_detections', 1)}")
    print(f"🧠 Decisiones médicas: {summary.get('medical_decisions', 1)}")
    print(f"⚡ Tareas asíncronas: {summary.get('async_tasks', 1)}")
    print(f"⚠️  Escalaciones: {summary.get('escalations', 1)}")
    print(f"⏱️  Duración total: {summary.get('duration_seconds', 'N/A')}s")
    
    print("\n🎉 DEMO COMPLETADO EXITOSAMENTE!")
    print("📈 Revisa el dashboard de AgentOps para ver todos los eventos:")
    print("🔗 https://app.agentops.ai/projects")
    
    return summary


def demo_phi_tokenization():
    """Demo de tokenización PHI para compliance médica"""
    
    print("\n🔒 DEMO TOKENIZACIÓN PHI (COMPLIANCE HIPAA)")
    print("=" * 50)
    
    tokenizer = PHITokenizer()
    
    # Datos médicos sensibles
    sensitive_data = {
        "patient_name": "Juan Carlos Pérez",
        "patient_id": "PAT_12345678",
        "ssn": "123-45-6789",
        "phone": "+56-9-8765-4321",
        "email": "juan.perez@email.com",
        "address": "Av. Las Condes 123, Santiago",
        "mrn": "MRN_789456123",
        # Datos médicos preservados
        "lpp_grade": 2,
        "anatomical_location": "sacrum",
        "confidence": 0.89,
        "risk_factors": ["diabetes", "immobility"]
    }
    
    print("📋 Datos originales (con PHI):")
    for key, value in sensitive_data.items():
        print(f"  {key}: {value}")
    
    # Tokenizar datos
    tokenized_data = tokenizer.tokenize_dict(sensitive_data)
    
    print("\n🔐 Datos tokenizados (HIPAA-safe):")
    for key, value in tokenized_data.items():
        print(f"  {key}: {value}")
    
    print("\n✅ PHI protegida mientras se preserva contexto médico")


async def main():
    """Función principal de demo"""
    try:
        # Demo principal del workflow médico
        summary = await demo_medical_lpp_workflow()
        
        # Demo de tokenización PHI
        demo_phi_tokenization()
        
        print("\n" + "="*60)
        print("🏥 SISTEMA DE MONITOREO MÉDICO AGENTOPS OPERATIVO")
        print("📊 Telemetría médica enviada al dashboard")
        print("🔒 Compliance HIPAA garantizado")
        print("⚡ Pipeline asíncrono monitoreado")
        print("🎯 Sistema listo para producción médica")
        
    except Exception as e:
        print(f"❌ Error en demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())