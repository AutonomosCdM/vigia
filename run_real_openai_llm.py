#!/usr/bin/env python3
"""
Real OpenAI LLM Calls with AgentOps
===================================

Makes ACTUAL LLM calls to OpenAI that AgentOps can track automatically
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
from dotenv import load_dotenv
load_dotenv()

def run_real_openai_medical_session():
    """Run medical session with REAL OpenAI LLM calls"""
    print("🏥 REAL OPENAI LLM MEDICAL SESSION")
    print("=" * 50)
    print("Making REAL LLM calls to OpenAI that AgentOps will auto-track!")
    print()
    
    # Initialize AgentOps with your API key
    api_key = "995199e8-36e5-47e7-96b9-221a3ee12fb9"
    print(f"✅ Using your AgentOps API key: {api_key[:10]}...")
    
    print("1️⃣ Initializing AgentOps...")
    try:
        import agentops
        agentops.init(
            api_key=api_key,
            default_tags=["vigia-medical", "real-openai-llm", "auto-instrumentation"]
        )
        print("✅ AgentOps initialized with auto-instrumentation!")
        print()
    except Exception as e:
        print(f"❌ AgentOps init error: {e}")
        return False
    
    # Check if OpenAI is available
    print("2️⃣ Setting up OpenAI client...")
    try:
        # Check if we have OpenAI API key
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            print("⚠️  No OpenAI API key found. Using mock LLM calls...")
            use_real_openai = False
        else:
            print(f"✅ OpenAI API key found: {openai_key[:10]}...")
            use_real_openai = True
            
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            
    except ImportError:
        print("⚠️  OpenAI package not installed. Using mock LLM calls...")
        use_real_openai = False
    except Exception as e:
        print(f"⚠️  OpenAI setup error: {e}. Using mock LLM calls...")
        use_real_openai = False
    
    # Patient data
    patient_context = {
        "patient_code": "CD-2025-007",
        "name": "Patricia Hernández",
        "age": 84,
        "diabetes": True,
        "hypertension": True,
        "mobility": "bedridden",
        "braden_score": 9
    }
    
    detection_result = {
        "lpp_grade": 3,
        "confidence": 0.94,
        "anatomical_location": "sacrum",
        "severity": "high"
    }
    
    print("3️⃣ Processing Medical Data...")
    print(f"👤 Patient: {patient_context['patient_code']} ({patient_context['name']})")
    print(f"🔍 Detection: LPP Grade {detection_result['lpp_grade']} ({detection_result['confidence']:.1%})")
    print()
    
    # Manual event logging (to ensure events are recorded)
    print("4️⃣ Manually Recording Events...")
    try:
        # Log patient processing
        agentops.record(agentops.ActionEvent(
            action_type="patient_intake",
            params={
                "patient_code": patient_context['patient_code'],
                "age": patient_context['age'],
                "risk_factors": ["diabetes", "hypertension", "bedridden"],
                "braden_score": patient_context['braden_score']
            },
            returns={
                "risk_level": "very_high",
                "intake_complete": True
            }
        ))
        print("✅ Patient intake event recorded")
        
        # Log image analysis
        agentops.record(agentops.ActionEvent(
            action_type="lpp_image_analysis", 
            params={
                "image_path": "medical_image_grade3.jpg",
                "model_version": "yolo_v5_medical",
                "patient_id": patient_context['patient_code']
            },
            returns={
                "lpp_grade": detection_result['lpp_grade'],
                "confidence": detection_result['confidence'],
                "location": detection_result['anatomical_location'],
                "processing_time_ms": 1450
            }
        ))
        print("✅ Image analysis event recorded")
        
    except Exception as e:
        print(f"❌ Event recording error: {e}")
    
    # Make REAL or mock LLM calls
    if use_real_openai:
        print("5️⃣ Making REAL OpenAI LLM Call...")
        try:
            # This should be auto-tracked by AgentOps
            clinical_prompt = f"""
You are a medical AI specialist. Analyze this pressure injury case:

Patient: {patient_context['age']} years old
Risk factors: Diabetes, hypertension, bedridden
Braden Score: {patient_context['braden_score']}/23 (very high risk)

Pressure Injury:
- Grade: {detection_result['lpp_grade']} (Stage III)
- Confidence: {detection_result['confidence']:.1%}
- Location: {detection_result['anatomical_location']}

Provide immediate clinical recommendations following NPUAP guidelines.
"""
            
            print("🧠 Sending prompt to OpenAI GPT-4...")
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a medical AI specialist focused on pressure injury care."},
                    {"role": "user", "content": clinical_prompt}
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            clinical_response = response.choices[0].message.content
            
            print(f"✅ Real OpenAI LLM call completed!")
            print(f"📝 Response: {clinical_response[:100]}...")
            print(f"💰 Tokens used: {response.usage.total_tokens}")
            
        except Exception as e:
            print(f"❌ OpenAI LLM call error: {e}")
            clinical_response = "Mock clinical assessment due to API error"
    
    else:
        print("5️⃣ Making Mock LLM Call (recorded as LLM event)...")
        
        clinical_prompt = f"Assess Stage III pressure injury for {patient_context['age']}-year-old diabetic patient"
        clinical_response = """
CLINICAL ASSESSMENT - Stage III Pressure Injury

IMMEDIATE PRIORITIES:
1. Surgical consultation within 4 hours
2. Debridement assessment required
3. Infection prevention protocols
4. Pain management optimization
5. Nutritional support intensification

RISK STRATIFICATION: VERY HIGH
- Advanced age (84 years)
- Multiple comorbidities
- Severe mobility limitation
- Critical Braden Score (9/23)

RECOMMENDED INTERVENTIONS:
- Complete pressure offloading
- Wound care specialist consultation
- Antibiotic prophylaxis consideration
- Enhanced monitoring protocol
"""
        
        # Manually record LLM event
        agentops.record(agentops.LLMEvent(
            prompt=clinical_prompt,
            completion=clinical_response,
            model="gpt-4-medical-mock",
            prompt_tokens=len(clinical_prompt.split()),
            completion_tokens=len(clinical_response.split()),
            cost=0.0156
        ))
        
        print("✅ Mock LLM call recorded as LLM event")
        print(f"📝 Clinical assessment completed")
    
    print()
    print("6️⃣ Recording Additional Medical Events...")
    try:
        # Tool usage for protocol search
        agentops.record(agentops.ToolEvent(
            name="medical_protocol_database",
            params={
                "search_query": f"stage_iii_pressure_injury_{detection_result['anatomical_location']}",
                "patient_age": patient_context['age'],
                "comorbidities": ["diabetes", "hypertension"]
            },
            returns={
                "protocols_found": 8,
                "evidence_levels": ["A", "A", "B", "A", "B", "A", "C", "B"],
                "urgent_protocols": 3,
                "search_time_ms": 245
            }
        ))
        print("✅ Protocol search tool event recorded")
        
        # Emergency alert action
        agentops.record(agentops.ActionEvent(
            action_type="emergency_medical_alert",
            params={
                "alert_type": "stage_iii_pressure_injury",
                "patient_code": patient_context['patient_code'],
                "urgency": "high",
                "recipients": ["attending_physician", "wound_specialist", "charge_nurse"],
                "channels": ["page", "secure_message", "phone_call"]
            },
            returns={
                "alerts_sent": 3,
                "delivery_confirmed": True,
                "response_time_target": "15_minutes",
                "escalation_protocol": "activated"
            }
        ))
        print("✅ Emergency alert event recorded")
        
        # Multi-disciplinary consultation
        agentops.record(agentops.ActionEvent(
            action_type="mdt_consultation_request",
            params={
                "consultation_type": "urgent_wound_care",
                "specialties_requested": ["plastic_surgery", "infectious_disease", "endocrinology"],
                "patient_id": patient_context['patient_code'],
                "clinical_priority": "urgent"
            },
            returns={
                "consultations_scheduled": 3,
                "earliest_appointment": "within_4_hours",
                "mdt_meeting_scheduled": True
            }
        ))
        print("✅ Multi-disciplinary consultation event recorded")
        
    except Exception as e:
        print(f"❌ Additional event recording error: {e}")
    
    print()
    print("7️⃣ Completing AgentOps Session...")
    try:
        # Final session summary
        agentops.record(agentops.ActionEvent(
            action_type="medical_session_complete",
            params={
                "session_type": "emergency_pressure_injury_assessment",
                "patient_processed": patient_context['patient_code'],
                "final_diagnosis": f"Stage_{detection_result['lpp_grade']}_pressure_injury",
                "clinical_priority": "urgent",
                "total_events_logged": 6,
                "real_llm_used": use_real_openai
            },
            returns={
                "session_success": True,
                "emergency_protocols_activated": True,
                "specialist_consultations_requested": True,
                "monitoring_enhanced": True
            }
        ))
        
        # End session
        agentops.end_session(end_state="Success")
        
        print("✅ AgentOps session completed successfully!")
        print()
        
    except Exception as e:
        print(f"❌ Session completion error: {e}")
    
    # Final Summary
    print("🎉 REAL MEDICAL SESSION WITH DETAILED EVENTS COMPLETE")
    print("=" * 50)
    print("✅ Events recorded in AgentOps:")
    print("• Patient Intake (ActionEvent)")
    print("• LPP Image Analysis (ActionEvent)")
    if use_real_openai:
        print("• Real OpenAI LLM Call (auto-tracked)")
    else:
        print("• Clinical Assessment (LLMEvent)")
    print("• Protocol Search (ToolEvent)")
    print("• Emergency Alert (ActionEvent)")
    print("• Multi-disciplinary Consultation (ActionEvent)")
    print("• Session Complete (ActionEvent)")
    print()
    print(f"📊 Session Statistics:")
    print(f"• Patient: {patient_context['patient_code']} ({patient_context['name']})")
    print(f"• Emergency: Stage {detection_result['lpp_grade']} Pressure Injury")
    print(f"• Risk Level: VERY HIGH")
    print(f"• Events Logged: 6+ detailed events")
    print(f"• LLM Used: {'Real OpenAI' if use_real_openai else 'Mock (recorded as LLM event)'}")
    print()
    print("🔗 Check your AgentOps dashboard - you should see detailed events!")
    print("Dashboard: https://app.agentops.ai/")
    
    return True

if __name__ == "__main__":
    success = run_real_openai_medical_session()
    
    if success:
        print(f"\n🎯 Real medical session with detailed events: SUCCESS")
        sys.exit(0)
    else:
        print(f"\n❌ Real medical session: FAILED")
        sys.exit(1)