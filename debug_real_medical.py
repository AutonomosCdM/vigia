#!/usr/bin/env python3
"""Debug script to see real medical decision output."""

import json
from vigia_detect.systems.medical_decision_engine import MedicalDecisionEngine

def debug_real_medical_decision():
    engine = MedicalDecisionEngine()
    
    # Real Grade 4 LPP case
    patient_context = {
        "age": 75,
        "diabetes": True,
        "mobility": "bedbound",
        "braden_score": 12
    }
    
    decision = engine.make_clinical_decision(
        lpp_grade=4,
        confidence=0.95,
        anatomical_location="sacrum",
        patient_context=patient_context
    )
    
    print("=== REAL MEDICAL DECISION OUTPUT ===")
    print(json.dumps(decision, indent=2, default=str))
    print()
    print("=== DECISION KEYS ===")
    print(list(decision.keys()))

if __name__ == "__main__":
    debug_real_medical_decision()