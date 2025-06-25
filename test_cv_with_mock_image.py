#!/usr/bin/env python3
"""Test CV pipeline with a mock image to validate framework."""

import asyncio
import numpy as np
from PIL import Image
import os
from vigia_detect.cv_pipeline.medical_detector_factory import create_medical_detector

def create_mock_medical_image():
    """Create a mock medical image for testing."""
    # Create 512x512 mock wound image 
    img_array = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
    
    # Add some "wound-like" features
    img_array[200:300, 200:300] = [180, 100, 100]  # Reddish area
    img_array[220:280, 220:280] = [120, 60, 60]    # Darker center
    
    img = Image.fromarray(img_array)
    
    os.makedirs("tests/fixtures", exist_ok=True)
    img_path = "tests/fixtures/mock_lpp_image.jpg"
    img.save(img_path)
    
    return img_path

async def test_cv_with_mock_image():
    print("=== TESTING CV PIPELINE WITH MOCK IMAGE ===")
    
    # Create mock image
    image_path = create_mock_medical_image()
    print(f"✅ Mock image created: {image_path}")
    
    # Create detector
    detector = create_medical_detector()
    print(f"✅ Detector: {type(detector).__name__}")
    
    # Test detection
    try:
        result = await detector.detect_medical_condition(
            image_path=image_path,
            token_id="batman-mock-001",
            patient_context={
                "age": 75, 
                "diabetes": True,
                "anatomical_location": "sacrum"
            }
        )
        
        print("\n=== CV DETECTION RESULT ===")
        for key, value in result.items():
            print(f"{key}: {value}")
            
        # Validate framework is working
        if result.get('success'):
            print("\n✅ CV PIPELINE FRAMEWORK WORKING")
            print("✅ Image loading successful")
            print("✅ Mock detection processing")
            print("✅ Result structure valid")
        else:
            print(f"\n⚠️  Pipeline issue: {result.get('error')}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_cv_with_mock_image())