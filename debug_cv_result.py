#!/usr/bin/env python3
"""Debug CV pipeline result type."""

import asyncio
from vigia_detect.cv_pipeline.medical_detector_factory import create_medical_detector

async def debug_cv_result():
    detector = create_medical_detector()
    
    try:
        result = await detector.detect_medical_condition(
            image_path="tests/fixtures/mock_lpp_image.jpg",
            token_id="debug-001",
            patient_context={"age": 75}
        )
        
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
        
        if hasattr(result, '__dict__'):
            print("Result attributes:")
            for attr, value in result.__dict__.items():
                print(f"  {attr}: {value}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_cv_result())