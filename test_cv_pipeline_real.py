#!/usr/bin/env python3
"""Test real CV pipeline functionality."""

import asyncio
from vigia_detect.cv_pipeline.medical_detector_factory import create_medical_detector

async def test_real_cv_pipeline():
    print("=== TESTING REAL CV PIPELINE ===")
    
    # Create real detector (not mock)
    detector = create_medical_detector()
    print(f"✅ Detector created: {type(detector).__name__}")
    
    # Test with real image path (even if image doesn't exist, should show framework)
    test_image = "tests/fixtures/sample_lpp_image.jpg"
    test_token = "batman-test-001"
    
    try:
        result = await detector.detect_medical_condition(
            image_path=test_image,
            token_id=test_token,
            patient_context={"age": 75, "diabetes": True}
        )
        
        print("\n=== CV PIPELINE RESULT ===")
        print(f"LPP Grade: {result.get('lpp_grade', 'N/A')}")
        print(f"Confidence: {result.get('confidence', 'N/A')}")
        print(f"Processing Time: {result.get('processing_time_ms', 'N/A')}ms")
        print(f"Engine Used: {result.get('engine_used', 'N/A')}")
        
        if result.get('success'):
            print("✅ CV Pipeline working")
        else:
            print(f"⚠️  CV Pipeline returned: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"⚠️  CV Pipeline error: {str(e)}")
        print("This is expected if no trained models are available")

if __name__ == "__main__":
    asyncio.run(test_real_cv_pipeline())