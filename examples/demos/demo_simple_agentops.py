#!/usr/bin/env python3
"""
Demo simple y funcional de AgentOps para Vigia LPP-Detect
"""

import os
import time
import uuid
from datetime import datetime
from vigia_detect.monitoring import AgentOpsClient

def main():
    """Demo simple pero completo de monitoreo médico"""
    
    print("🏥 DEMO AGENTOPS - VIGIA LPP-DETECT")
    print("=" * 50)
    
    # 1. Inicializar cliente AgentOps
    client = AgentOpsClient(
        api_key=os.getenv("AGENTOPS_API_KEY"),
        app_id="vigia-lpp-production",
        environment="production",
        enable_phi_protection=True,
        compliance_level="hipaa"
    )
    
    if not client.initialized:
        print("❌ Error: AgentOps no inicializado")
        return
    
    print("✅ Cliente AgentOps inicializado")
    
    # 2. Crear caso médico
    session_id = f"medical_session_{int(time.time())}"
    patient_context = {
        "patient_id": f"PAT_{uuid.uuid4().hex[:8].upper()}",
        "case_id": f"LPP_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "lpp_grade": 2,
        "anatomical_location": "sacrum",
        "risk_factors": ["diabetes", "limited_mobility"],
        "facility": "Hospital Regional"
    }
    
    print(f"📋 Caso médico: {patient_context['case_id']}")
    
    # 3. Iniciar sesión médica
    result = client.track_medical_session(
        session_id=session_id,
        patient_context=patient_context,
        session_type="lpp_analysis_complete_demo"
    )
    
    print(f"🔄 Sesión médica iniciada: {result}")
    
    # 4. Simular detección LPP
    print("\n🔍 ANÁLISIS DE IMAGEN MÉDICA...")
    time.sleep(2)
    
    detection_results = {
        "lpp_grade": 2,
        "confidence": 0.89,
        "anatomical_location": "sacrum",
        "area_cm2": 3.2,
        "model": "YOLOv5_medical_v2.1",
        "processing_time_ms": 2300
    }
    
    client.track_lpp_detection(
        session_id=session_id,
        image_path="/medical_images/pressure_ulcer_sacrum_001.jpg",
        detection_results=detection_results,
        confidence=0.89,
        lpp_grade=2
    )
    
    print(f"✅ LPP detectado: Grado {detection_results['lpp_grade']} (89% confianza)")
    
    # 5. Interacción con agente médico
    print("\n🤖 AGENTE MÉDICO ADK...")
    time.sleep(1)
    
    client.track_agent_interaction(
        agent_name="medical_decision_engine",
        action="recommend_treatment",
        input_data={
            "lpp_grade": 2,
            "patient_risk_factors": ["diabetes", "limited_mobility"],
            "evidence_guidelines": "NPUAP_EPUAP_2019"
        },
        output_data={
            "treatment_protocol": "Stage_2_LPP_Management",
            "evidence_level": "A",
            "monitoring_frequency": "daily",
            "specialist_referral": False
        },
        execution_time=1.2,
        success=True
    )
    
    print("✅ Recomendación médica generada por agente ADK")
    
    # 6. Tarea asíncrona
    print("\n⚡ PIPELINE ASÍNCRONO...")
    
    client.track_async_task(
        task_id=f"celery_{uuid.uuid4().hex[:12]}",
        task_type="medical_report_generation",
        queue="medical_priority",
        status="success",
        metadata={
            "patient_case": patient_context['case_id'],
            "report_type": "lpp_analysis_complete",
            "processing_time": 45
        }
    )
    
    print("✅ Reporte médico generado vía Celery")
    
    # 7. Escalación médica
    print("\n⚠️  ESCALACIÓN MÉDICA...")
    
    client.track_medical_error(
        error_type="complex_case_review",
        error_message="Caso con múltiples factores de riesgo requiere revisión especializada",
        context={
            "patient_case": patient_context['case_id'],
            "risk_score": 0.78,
            "complexity_factors": ["diabetes", "age_75+", "immobility"]
        },
        severity="medium",
        requires_escalation=True
    )
    
    print("✅ Escalación registrada para revisión humana")
    
    # 8. Finalizar
    print("\n📊 FINALIZANDO SESIÓN...")
    time.sleep(1)
    
    client.end_session(session_id)
    
    print("\n🎯 DEMO COMPLETADO!")
    print("=" * 30)
    print(f"📋 Caso: {patient_context['case_id']}")
    print("🔍 Eventos enviados a AgentOps:")
    print("  • Sesión médica iniciada")
    print("  • Detección LPP (Grado 2)")
    print("  • Decisión médica (ADK Agent)")
    print("  • Tarea asíncrona (Celery)")
    print("  • Escalación médica")
    print("  • Sesión finalizada")
    
    print("\n📈 REVISA EL DASHBOARD AGENTOPS:")
    print("🔗 https://app.agentops.ai/projects")
    print("✅ Sistema de monitoreo médico operativo!")


if __name__ == "__main__":
    main()