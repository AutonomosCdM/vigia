#!/usr/bin/env python3
"""
Demo detallado de MedGemma mostrando proceso completo y resultados.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from pprint import pprint

sys.path.append(str(Path(__file__).parent.parent))

from vigia_detect.ai.medgemma_client import MedGemmaClient, MedicalContext, MedicalAnalysisType
from vigia_detect.ai.medical_prompts import MedicalPromptBuilder, PromptTemplate, MedicalPromptContext


async def demo_detailed_process():
    """Demo mostrando todo el proceso paso a paso"""
    
    print("="*80)
    print("🏥 DEMO DETALLADO MEDGEMMA - PROCESO COMPLETO")
    print("="*80)
    
    # 1. CONFIGURACIÓN
    print("\n1️⃣ CONFIGURACIÓN:")
    print("-"*40)
    print(f"   API Key configurada: {'✅' if os.environ.get('GOOGLE_API_KEY') else '❌'}")
    print(f"   Modelo: {os.environ.get('MEDGEMMA_MODEL', 'gemini-1.5-flash')}")
    print(f"   Timestamp: {datetime.now().isoformat()}")
    
    # 2. INICIALIZACIÓN
    print("\n2️⃣ INICIALIZACIÓN DEL CLIENTE:")
    print("-"*40)
    
    try:
        client = MedGemmaClient()
        print("   ✅ Cliente MedGemma inicializado correctamente")
        print(f"   Modelo activo: {client.model_name}")
        print(f"   Temperature: {client.generation_config['temperature']}")
        print(f"   Max tokens: {client.generation_config['max_output_tokens']}")
    except Exception as e:
        print(f"   ❌ Error al inicializar: {e}")
        return
    
    # 3. CASO CLÍNICO
    print("\n3️⃣ CASO CLÍNICO DE ENTRADA:")
    print("-"*40)
    
    clinical_observations = """
    Paciente masculino de 78 años, postrado en cama desde hace 3 meses tras ACV.
    
    HALLAZGOS EN EXAMEN FÍSICO:
    - Lesión en región sacra de 5x4 cm
    - Pérdida de espesor total de la piel
    - Tejido de granulación visible en el 60% del lecho
    - Esfacelo amarillento en el 40% restante
    - Bordes socavados en zona lateral derecha
    - Exudado seroso moderado
    - Piel perilesional macerada
    - Sin mal olor
    
    ANTECEDENTES:
    - Diabetes tipo 2 (HbA1c 8.5%)
    - Hipertensión arterial
    - Incontinencia urinaria
    - Albumina sérica: 2.8 g/dL
    """
    
    print(clinical_observations)
    
    medical_context = MedicalContext(
        patient_age=78,
        medical_history=["ACV", "diabetes_tipo_2", "hipertension", "incontinencia_urinaria"],
        current_medications=["metformina", "insulina", "enalapril", "furosemida"],
        mobility_status="postrado",
        risk_factors=["inmovilidad", "diabetes", "desnutricion", "incontinencia"],
        previous_lpp_history=False
    )
    
    print("\n   CONTEXTO MÉDICO:")
    print(f"   - Edad: {medical_context.patient_age} años")
    print(f"   - Historia médica: {', '.join(medical_context.medical_history)}")
    print(f"   - Medicamentos: {', '.join(medical_context.current_medications)}")
    print(f"   - Movilidad: {medical_context.mobility_status}")
    print(f"   - Factores de riesgo: {', '.join(medical_context.risk_factors)}")
    
    # 4. CONSTRUCCIÓN DEL PROMPT
    print("\n4️⃣ CONSTRUCCIÓN DEL PROMPT MÉDICO:")
    print("-"*40)
    
    prompt = MedicalPromptBuilder.build_lpp_staging_prompt(
        clinical_observations=clinical_observations,
        image_findings=None,
        context=MedicalPromptContext(language_preference="es")
    )
    
    print("   ESTRUCTURA DEL PROMPT:")
    print("   - Rol: Especialista en medicina interna y cuidado de heridas")
    print("   - Sistema de clasificación: NPUAP/EPUAP")
    print("   - Formato de respuesta: JSON estructurado")
    print("\n   PREVIEW DEL PROMPT (primeras 500 caracteres):")
    print("   " + prompt[:500].replace('\n', '\n   ') + "...")
    
    # 5. LLAMADA A MEDGEMMA
    print("\n5️⃣ LLAMADA A MEDGEMMA API:")
    print("-"*40)
    print("   🔄 Enviando consulta médica...")
    
    start_time = datetime.now()
    
    try:
        result = await client.analyze_lpp_findings(
            clinical_observations=clinical_observations,
            visual_findings=None,
            medical_context=medical_context
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"   ✅ Respuesta recibida en {duration:.2f} segundos")
        
    except Exception as e:
        print(f"   ❌ Error en la llamada: {e}")
        return
    
    # 6. RESPUESTA COMPLETA
    print("\n6️⃣ RESPUESTA COMPLETA DE MEDGEMMA:")
    print("-"*40)
    
    if result:
        print(f"\n   TIPO DE ANÁLISIS: {result.analysis_type.value}")
        print(f"   CONFIANZA: {result.confidence_score:.2%}")
        print(f"   NIVEL DE RIESGO: {result.risk_level}")
        print(f"   SEGUIMIENTO NECESARIO: {'Sí' if result.follow_up_needed else 'No'}")
        
        print("\n   HALLAZGOS CLÍNICOS:")
        for key, value in result.clinical_findings.items():
            print(f"\n   📌 {key.upper()}:")
            if isinstance(value, list):
                for item in value:
                    print(f"      • {item}")
            else:
                # Formatear texto largo
                if isinstance(value, str) and len(value) > 80:
                    words = value.split()
                    line = "      "
                    for word in words:
                        if len(line + word) > 80:
                            print(line)
                            line = "      " + word
                        else:
                            line += " " + word
                    print(line)
                else:
                    print(f"      {value}")
        
        print("\n   RECOMENDACIONES:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"   {i}. {rec}")
        
        print("\n   INFORMACIÓN DE AUDITORÍA:")
        for key, value in result.audit_trail.items():
            print(f"   - {key}: {value}")
    
    # 7. ANÁLISIS DE INTERVENCIONES
    print("\n7️⃣ GENERANDO PLAN DE INTERVENCIÓN:")
    print("-"*40)
    
    if result and result.clinical_findings.get('lpp_grade'):
        lpp_grade = result.clinical_findings['lpp_grade']
        risk_factors = result.audit_trail.get('risk_factors_identified', [])
        
        print(f"   Generando plan para: {lpp_grade}")
        print(f"   Factores de riesgo considerados: {', '.join(risk_factors)}")
        
        intervention_plan = await client.generate_intervention_plan(
            lpp_grade=lpp_grade,
            risk_factors=risk_factors,
            patient_limitations=["postrado", "incontinencia"],
            medical_context=medical_context
        )
        
        if intervention_plan:
            print("\n   PLAN DE INTERVENCIÓN GENERADO:")
            
            # Mostrar el plan estructurado
            if 'primary_interventions' in intervention_plan.clinical_findings:
                print("\n   INTERVENCIONES PRIMARIAS:")
                for interv in intervention_plan.clinical_findings['primary_interventions']:
                    print(f"   • {interv['intervention']}")
                    print(f"     - Frecuencia: {interv.get('frequency', 'No especificada')}")
                    print(f"     - Duración: {interv.get('duration', 'Continua')}")
                    print(f"     - Instrucciones: {interv.get('instructions', 'Ver protocolo')}")
            
            if 'prevention_strategies' in intervention_plan.clinical_findings:
                print("\n   ESTRATEGIAS DE PREVENCIÓN:")
                for strategy in intervention_plan.clinical_findings['prevention_strategies']:
                    print(f"   • {strategy}")
            
            if 'resources_needed' in intervention_plan.audit_trail:
                print("\n   RECURSOS NECESARIOS:")
                for resource in intervention_plan.audit_trail['resources_needed']:
                    print(f"   • {resource}")
    
    # 8. TRIAGE DE URGENCIA
    print("\n8️⃣ EVALUACIÓN DE TRIAGE:")
    print("-"*40)
    
    patient_message = f"""
    Doctor, mi {medical_context.patient_age} años tiene la herida que describí arriba.
    Noté que ha crecido en la última semana y ahora hay más líquido saliendo.
    ¿Qué tan urgente es que lo vea un médico?
    """
    
    triage_result = await client.perform_clinical_triage(
        patient_message=patient_message,
        symptoms_description="Úlcera sacra con pérdida total de espesor, exudado moderado",
        medical_context=medical_context
    )
    
    if triage_result:
        findings = triage_result.clinical_findings
        
        print(f"\n   NIVEL DE URGENCIA: {findings.get('urgency_level', 'No determinado')}")
        print(f"   CONFIANZA EN TRIAGE: {triage_result.confidence_score:.2%}")
        print(f"   TIEMPO RECOMENDADO: Dentro de {findings.get('timeframe_hours', 'N/A')} horas")
        print(f"   NIVEL DE ATENCIÓN: {findings.get('recommended_care_level', 'No especificado')}")
        
        if findings.get('alarm_signs'):
            print("\n   ⚠️  SIGNOS DE ALARMA:")
            for sign in findings['alarm_signs']:
                print(f"      • {sign}")
        
        print(f"\n   RAZONAMIENTO CLÍNICO:")
        reasoning = findings.get('clinical_reasoning', 'No disponible')
        if len(reasoning) > 80:
            words = reasoning.split()
            line = "   "
            for word in words:
                if len(line + word) > 80:
                    print(line)
                    line = "   " + word
                else:
                    line += " " + word
            print(line)
        else:
            print(f"   {reasoning}")
    
    # 9. RESUMEN FINAL
    print("\n9️⃣ RESUMEN DEL ANÁLISIS:")
    print("-"*40)
    if result:
        print(f"   ✅ Diagnóstico LPP: {result.clinical_findings.get('lpp_grade', 'No determinado')}")
        print(f"   ✅ Confianza diagnóstica: {result.confidence_score:.2%}")
        print(f"   ✅ Total recomendaciones: {len(result.recommendations)}")
        print(f"   ✅ Requiere seguimiento: {'Sí' if result.follow_up_needed else 'No'}")
    else:
        print("   ❌ No se pudo completar el análisis LPP")
    
    if triage_result:
        print(f"   ✅ Urgencia clínica: {triage_result.clinical_findings.get('urgency_level', 'No determinado')}")
    else:
        print("   ❌ No se pudo completar el triage")
    
    print("\n" + "="*80)
    print("✅ DEMO COMPLETADO")
    print("="*80)


async def main():
    """Función principal"""
    # Configurar API key temporalmente si no está en el ambiente
    if not os.environ.get('GOOGLE_API_KEY'):
        os.environ['GOOGLE_API_KEY'] = 'AIzaSyBqAPpzFkpBuLiVPkSCSuUDcRiO4GQDoHk'
    
    # Usar modelo Flash para evitar límites de cuota
    os.environ['MEDGEMMA_MODEL'] = 'gemini-1.5-flash'
    
    try:
        await demo_detailed_process()
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante el demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.WARNING,  # Solo mostrar warnings y errores
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())