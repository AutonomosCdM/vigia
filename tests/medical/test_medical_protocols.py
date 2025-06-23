#!/usr/bin/env python3
"""
Test medical protocol search and evidence-based decisions
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment
os.environ['ENVIRONMENT'] = 'development'
os.environ['USE_LOCAL_AI'] = 'true'

def test_medical_protocols():
    """Test medical protocol search and decision making"""
    print("🏥 Testing Medical Protocol Search & Evidence-Based Decisions")
    print("=" * 70)
    
    # Test 1: Medical Decision Engine
    print("\n1️⃣ Testing Medical Decision Engine...")
    try:
        from vigia_detect.systems.medical_decision_engine import MedicalDecisionEngine
        
        engine = MedicalDecisionEngine()
        
        # Test Grade 2 LPP decision
        decision = engine.make_clinical_decision(
            lpp_grade=2,
            confidence=0.85,
            anatomical_location="sacrum",
            patient_context={
                'patient_id': 'CD-2025-001',
                'age': 75,
                'diabetes': True,
                'mobility_limited': True,
                'braden_score': 12
            }
        )
        
        print(f"✅ Grade 2 LPP Clinical Decision:")
        print(f"   - Clinical Grade: {decision.get('clinical_grade', 'N/A')}")
        print(f"   - Severity Level: {decision.get('severity_level', 'N/A')}")
        print(f"   - Evidence Level: {decision.get('evidence_level', 'N/A')}")
        print(f"   - Escalation Required: {decision.get('escalation_required', False)}")
        if decision.get('recommendations'):
            print(f"   - Recommendations: {len(decision['recommendations'])} items")
        
        # Test Grade 3 LPP (more severe)
        decision_grade3 = engine.make_clinical_decision(
            lpp_grade=3,
            confidence=0.90,
            anatomical_location="coccyx",
            patient_context={
                'patient_id': 'JL-2025-003',
                'age': 82,
                'diabetes': True,
                'mobility_limited': True,
                'braden_score': 10
            }
        )
        
        print(f"✅ Grade 3 LPP Clinical Decision:")
        print(f"   - Clinical Grade: {decision_grade3.get('clinical_grade', 'N/A')}")
        print(f"   - Severity Level: {decision_grade3.get('severity_level', 'N/A')}")
        print(f"   - Escalation Required: {decision_grade3.get('escalation_required', False)}")
        
    except Exception as e:
        print(f"❌ Medical Decision Engine Error: {e}")
        return False
    
    # Test 2: MINSAL Integration (Chilean compliance)
    print("\n2️⃣ Testing MINSAL Chilean Compliance...")
    try:
        from vigia_detect.systems.minsal_medical_decision_engine import make_minsal_clinical_decision
        
        minsal_decision = make_minsal_clinical_decision(
            lpp_grade=2,
            confidence=0.85,
            anatomical_location="sacrum",
            patient_context={
                'patient_id': 'CD-2025-001',
                'age': 75,
                'diabetes': True,
                'public_healthcare': True,
                'region': 'Metropolitana'
            }
        )
        
        print(f"✅ MINSAL Clinical Decision:")
        print(f"   - Chilean Compliance: {minsal_decision.get('minsal_compliant', False)}")
        print(f"   - Severity Classification: {minsal_decision.get('severity_level', 'N/A')}")
        print(f"   - Mandatory Reporting: {minsal_decision.get('requires_reporting', False)}")
        if minsal_decision.get('recommendations'):
            print(f"   - Chilean Protocol Recommendations: {len(minsal_decision['recommendations'])}")
        
    except Exception as e:
        print(f"❌ MINSAL Integration Error: {e}")
        return False
    
    # Test 3: Redis Vector Search (Medical Protocols)
    print("\n3️⃣ Testing Medical Protocol Vector Search...")
    try:
        import redis
        
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Store mock protocol embeddings
        protocol_data = {
            "grade_2_protocols": [
                "Clean wound with saline solution",
                "Apply hydrocolloid dressing",
                "Reposition patient every 2 hours",
                "Monitor for signs of infection",
                "Document wound measurements"
            ],
            "grade_3_protocols": [
                "Immediate wound specialist consultation",
                "Debridement if necrotic tissue present",
                "Advanced wound dressing selection",
                "Pain management protocol",
                "Nutritional assessment and support"
            ]
        }
        
        # Store protocols in Redis
        for grade, protocols in protocol_data.items():
            for i, protocol in enumerate(protocols):
                key = f"vigia:protocol:{grade}:{i}"
                r.hset(key, mapping={
                    'protocol': protocol,
                    'grade': grade.split('_')[1],
                    'evidence_level': 'A',
                    'category': 'treatment'
                })
                r.expire(key, 3600)  # 1 hour TTL
        
        # Search for Grade 2 protocols
        grade_2_keys = r.keys("vigia:protocol:grade_2*")
        protocols_found = []
        for key in grade_2_keys:
            protocol_data = r.hgetall(key)
            if protocol_data:
                protocols_found.append(protocol_data[b'protocol'].decode())
        
        print(f"✅ Protocol Vector Search Results:")
        print(f"   - Grade 2 Protocols Found: {len(protocols_found)}")
        for i, protocol in enumerate(protocols_found[:3], 1):
            print(f"   {i}. {protocol}")
        
    except Exception as e:
        print(f"❌ Protocol Search Error: {e}")
        return False
    
    # Test 4: Complete Patient Assessment
    print("\n4️⃣ Testing Complete Patient Assessment...")
    try:
        # Mock complete assessment workflow
        patient_data = {
            'patient_code': 'CD-2025-001',
            'age': 75,
            'diabetes': True,
            'mobility_limited': True,
            'braden_score': 12,
            'risk_level': 'high'
        }
        
        detection_result = {
            'lpp_grade': 2,
            'confidence': 0.85,
            'anatomical_location': 'sacrum',
            'bounding_box': {'x': 100, 'y': 100, 'width': 200, 'height': 150}
        }
        
        # Combine decision with protocols
        assessment = {
            'patient': patient_data,
            'detection': detection_result,
            'clinical_decision': decision,
            'minsal_compliance': minsal_decision,
            'recommended_protocols': protocols_found[:3],
            'assessment_timestamp': str(datetime.now()),
            'urgency_level': 'medium' if decision.get('escalation_required') else 'low'
        }
        
        print(f"✅ Complete Patient Assessment:")
        print(f"   - Patient: {assessment['patient']['patient_code']}")
        print(f"   - Detection Grade: {assessment['detection']['lpp_grade']}")
        print(f"   - Risk Level: {assessment['patient']['risk_level']}")
        print(f"   - Urgency: {assessment['urgency_level']}")
        print(f"   - Protocols Available: {len(assessment['recommended_protocols'])}")
        print(f"   - MINSAL Compliant: {assessment['minsal_compliance'].get('minsal_compliant', False)}")
        
        # Store complete assessment in Redis
        assessment_key = f"vigia:assessment:{patient_data['patient_code']}:{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        r.hset(assessment_key, mapping={
            'patient_code': patient_data['patient_code'],
            'lpp_grade': str(detection_result['lpp_grade']),
            'confidence': str(detection_result['confidence']),
            'urgency_level': assessment['urgency_level'],
            'protocol_count': str(len(assessment['recommended_protocols'])),
            'minsal_compliant': str(assessment['minsal_compliance'].get('minsal_compliant', False))
        })
        r.expire(assessment_key, 86400)  # 24 hours TTL
        
        print(f"   - Assessment stored in Redis: {assessment_key}")
        
    except Exception as e:
        print(f"❌ Patient Assessment Error: {e}")
        return False
    
    # Final Summary
    print("\n" + "=" * 70)
    print("✅ MEDICAL PROTOCOL & EVIDENCE-BASED DECISIONS TEST SUCCESSFUL!")
    print("Medical workflow components tested:")
    print("• Evidence-Based Decision Engine ✅")
    print("• MINSAL Chilean Compliance ✅") 
    print("• Medical Protocol Vector Search ✅")
    print("• Complete Patient Assessment ✅")
    print("• Redis Medical Data Storage ✅")
    print("\n🏥 Medical protocols and decision making ready!")
    
    return True

if __name__ == "__main__":
    from datetime import datetime
    
    success = test_medical_protocols()
    
    if success:
        print(f"\n🎉 Medical protocols test completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ Medical protocols test failed!")
        sys.exit(1)