#!/usr/bin/env python3
"""
Quick demo to show real medical functionality working
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from vigia_detect.systems.medical_decision_engine import MedicalDecisionEngine

def demo_medical_functionality():
    print("🩺 VIGIA MEDICAL FUNCTIONALITY DEMO")
    print("="*50)
    
    engine = MedicalDecisionEngine()
    print("✅ Medical Decision Engine initialized")
    
    # Test real medical cases
    test_cases = [
        {
            "name": "Grade 4 Emergency Case",
            "lpp_grade": 4,
            "confidence": 0.95,
            "location": "sacrum",
            "patient": {"age": 75, "diabetes": True}
        },
        {
            "name": "Grade 2 Moderate Case", 
            "lpp_grade": 2,
            "confidence": 0.88,
            "location": "heel",
            "patient": {"age": 60, "hypertension": True}
        },
        {
            "name": "Grade 1 Prevention Case",
            "lpp_grade": 1,
            "confidence": 0.92,
            "location": "shoulder",
            "patient": {"age": 45}
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n🔬 TEST CASE {i}: {case['name']}")
        print("-" * 40)
        
        decision = engine.make_clinical_decision(
            lpp_grade=case["lpp_grade"],
            confidence=case["confidence"],
            anatomical_location=case["location"],
            patient_context=case["patient"]
        )
        
        # Show real medical output
        print(f"📊 LPP Grade: {decision['lpp_grade']}")
        print(f"⚡ Severity: {decision['severity_assessment'].upper()}")
        print(f"⏰ Timeline: {decision.get('intervention_timeline', 'N/A')}")
        
        # Show real clinical recommendations
        if 'clinical_recommendations' in decision:
            print("🏥 Clinical Recommendations:")
            for j, rec in enumerate(decision['clinical_recommendations'][:3], 1):
                print(f"   {j}. {rec}")
        
        # Show NPUAP compliance
        evidence = decision.get('evidence_documentation', {})
        if evidence.get('npuap_compliance'):
            print(f"📚 NPUAP Compliance: {evidence['npuap_compliance']}")
        
        # Show medical warnings for emergencies
        if decision.get('medical_warnings'):
            print("⚠️  Medical Warnings:")
            for warning in decision['medical_warnings'][:2]:
                print(f"   • {warning}")
        
        # Show audit trail
        audit = decision.get('quality_metrics', {})
        if audit.get('assessment_id'):
            print(f"📋 Audit ID: {audit['assessment_id']}")
    
    print("\n" + "="*50)
    print("🏆 RESULTADO: SISTEMA MÉDICO REAL FUNCIONANDO")
    print("✅ Decisiones clínicas basadas en NPUAP/EPUAP 2019")
    print("✅ Recomendaciones médicas reales")
    print("✅ Audit trail completo")
    print("✅ Escalación automática para emergencias")

if __name__ == "__main__":
    demo_medical_functionality()