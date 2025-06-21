#!/usr/bin/env python3
"""
Add LPP Detection for existing Bruce Wayne patient
================================================
"""

import requests
import json

def add_bruce_wayne_detection():
    """Add detection for existing Bruce Wayne patient"""
    
    print("🔍 ADDING LPP DETECTION FOR BRUCE WAYNE")
    print("=" * 60)
    
    # Supabase configuration from environment
    import os
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("❌ ERROR: SUPABASE_URL and SUPABASE_ANON_KEY environment variables required")
        print("   Run: source scripts/quick_env_setup.sh")
        return False
    
    headers = {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    
    # Get Bruce Wayne patient ID
    print("🔍 Finding Bruce Wayne patient...")
    
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/patients?patient_code=eq.%2B56961797823",
        headers=headers
    )
    
    if response.status_code == 200 and response.json():
        patient = response.json()[0]
        patient_id = patient['id']
        
        print(f"✅ Found Bruce Wayne: {patient_id}")
        print(f"   🦇 Name: {patient['anonymized_name']}")
        print(f"   📱 Code: {patient['patient_code']}")
        
        # Insert detection
        detection_data = {
            "patient_id": patient_id,
            "image_path": "/Users/autonomos_dev/Projects/vigia/vigia_detect/data/input/bruce_wayne_talon.jpg",
            "lpp_grade": 1,
            "confidence": 0.75,
            "anatomical_location": "heel",
            "severity": "low",
            "requires_medical_attention": True,
            "evidence_level": "B",
            "analysis_model": "vigia_lpp_detector_v2",
            "medical_validated": True,
            "status": "completed"
        }
        
        print(f"\n🔍 Inserting LPP detection...")
        
        detection_response = requests.post(
            f"{SUPABASE_URL}/rest/v1/lpp_detections",
            headers=headers,
            json=detection_data
        )
        
        print(f"📡 Response: {detection_response.status_code}")
        
        if detection_response.status_code == 201:
            detection = detection_response.json()[0]
            detection_id = detection['id']
            
            print(f"✅ Detection created: {detection_id}")
            print(f"   🎯 LPP Grade: {detection['lpp_grade']}")
            print(f"   📍 Location: {detection['anatomical_location']}")
            print(f"   🎲 Confidence: {detection['confidence']}")
            
            print(f"\n🎉 COMPLETE BRUCE WAYNE MEDICAL RECORD")
            print("=" * 60)
            print(f"🦇 Patient ID: {patient_id}")
            print(f"🔍 Detection ID: {detection_id}")
            print(f"💾 Database: REAL Supabase (vigia-medical)")
            print(f"🔒 PHI: TOKENIZED")
            print(f"🏥 Medical Data: COMPLETE")
            
            return True
        else:
            print(f"❌ Detection failed: {detection_response.text}")
            return False
    else:
        print(f"❌ Bruce Wayne patient not found: {response.text}")
        return False


if __name__ == "__main__":
    success = add_bruce_wayne_detection()
    
    if success:
        print("\n✅ Bruce Wayne's complete medical record is now in REAL Supabase!")
    else:
        print("\n❌ Failed to add detection")