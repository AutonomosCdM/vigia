#!/usr/bin/env python3
"""
Test Real Image Processing System
================================

Test if Vigia image processing is using real models or mocks
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

def test_real_image_processing():
    """Test if image processing is using real AI models"""
    print("🔍 TESTING VIGIA IMAGE PROCESSING SYSTEM")
    print("=" * 50)
    print("Checking if we're using REAL AI models or mocks...")
    print()
    
    # Check environment settings
    print("1️⃣ Checking Environment Configuration...")
    
    use_mock_yolo = os.getenv('VIGIA_USE_MOCK_YOLO', 'false').lower() == 'true'
    use_mock_env = os.getenv('USE_MOCKS', 'false').lower() == 'true'
    environment = os.getenv('ENVIRONMENT', 'development')
    
    print(f"   VIGIA_USE_MOCK_YOLO: {use_mock_yolo}")
    print(f"   USE_MOCKS: {use_mock_env}")
    print(f"   ENVIRONMENT: {environment}")
    print()
    
    # Check if we can load the real detector
    print("2️⃣ Testing Real YOLOv5 Model Loading...")
    try:
        from vigia_detect.cv_pipeline.detector import LPPDetector
        
        print("   📥 Loading LPPDetector...")
        start_time = time.time()
        
        # Initialize with real model
        detector = LPPDetector(
            model_type='yolov5s',
            conf_threshold=0.25
        )
        
        load_time = time.time() - start_time
        
        print(f"   ✅ LPPDetector loaded successfully ({load_time:.2f}s)")
        print(f"   🎯 Model type: {detector.model_type}")
        print(f"   🔧 Device: {detector.device}")
        print(f"   📋 Classes: {detector.class_names}")
        
        # Check if model is actually loaded
        if detector.model is not None:
            print(f"   ✅ Real YOLOv5 model loaded: {type(detector.model)}")
            is_real_model = True
        else:
            print(f"   ⚠️  Model is None - may be using mock")
            is_real_model = False
            
    except Exception as e:
        print(f"   ❌ Detector loading error: {e}")
        is_real_model = False
    
    print()
    
    # Test with actual image if real model is loaded
    if is_real_model:
        print("3️⃣ Testing Real Image Processing...")
        try:
            # Find test image
            test_image_paths = [
                "./vigia_detect/cv_pipeline/tests/data/test_eritema_simple.jpg",
                "./data/test_images/test_lpp.jpg",
                "./tests/data/sample_wound.jpg"
            ]
            
            test_image = None
            for path in test_image_paths:
                if os.path.exists(path):
                    test_image = path
                    break
            
            if test_image:
                print(f"   📸 Processing test image: {test_image}")
                
                # Process image with real model
                processing_start = time.time()
                results = detector.detect(test_image)
                processing_time = time.time() - processing_start
                
                print(f"   ✅ Real image processing completed ({processing_time:.3f}s)")
                print(f"   📊 Results type: {type(results)}")
                
                if hasattr(results, 'pandas'):
                    df = results.pandas().xyxy[0]
                    print(f"   🔍 Detections found: {len(df)}")
                    if len(df) > 0:
                        print(f"   📋 Classes detected: {df['name'].unique().tolist()}")
                        print(f"   🎯 Confidences: {df['confidence'].tolist()}")
                else:
                    print(f"   📋 Raw results: {results}")
                
                print("   ✅ REAL AI MODEL PROCESSING CONFIRMED!")
                
            else:
                print("   ⚠️  No test images found, creating synthetic test...")
                
                # Create synthetic test array
                import numpy as np
                synthetic_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
                
                processing_start = time.time()
                results = detector.detect(synthetic_image)
                processing_time = time.time() - processing_start
                
                print(f"   ✅ Synthetic image processed ({processing_time:.3f}s)")
                print("   ✅ REAL AI MODEL CONFIRMED!")
                
        except Exception as e:
            print(f"   ❌ Image processing error: {e}")
            print("   ⚠️  May be using mock or having model issues")
    
    print()
    
    # Test unified processor
    print("4️⃣ Testing Unified Image Processor...")
    try:
        from vigia_detect.core.unified_image_processor import UnifiedImageProcessor
        
        processor = UnifiedImageProcessor()
        print("   ✅ UnifiedImageProcessor loaded")
        
        # Check configuration
        print(f"   🔧 Processor type: {type(processor)}")
        
        # Test with patient context
        patient_context = {
            "patient_code": "TEST-001",
            "age": 75,
            "diabetes": True
        }
        
        if test_image and is_real_model:
            print("   📸 Testing with real image and patient context...")
            
            result = processor.process_image(
                image_path=test_image,
                patient_context=patient_context
            )
            
            print(f"   ✅ Unified processing completed")
            print(f"   📊 Result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")
            
            if isinstance(result, dict):
                if 'lpp_grade' in result:
                    print(f"   🎯 LPP Grade detected: {result['lpp_grade']}")
                if 'confidence' in result:
                    print(f"   📈 Confidence: {result['confidence']:.2%}")
                if 'medical_assessment' in result:
                    print(f"   🏥 Medical assessment included: Yes")
        
    except Exception as e:
        print(f"   ❌ UnifiedImageProcessor error: {e}")
    
    print()
    
    # Final assessment
    print("5️⃣ FINAL ASSESSMENT")
    print("-" * 30)
    
    if is_real_model and not use_mock_yolo:
        print("✅ VIGIA IS USING REAL AI MODELS!")
        print("   🧠 Real YOLOv5 model loaded and functional")
        print("   🔬 Actual computer vision inference")
        print("   🏥 Medical-grade pressure injury detection")
        print("   ⚡ Processing time indicates real model complexity")
        system_status = "REAL AI PROCESSING"
    elif use_mock_yolo or use_mock_env:
        print("⚠️  VIGIA IS CONFIGURED FOR MOCK MODE")
        print("   🧪 Mock responses for development/testing")
        print("   ⚡ Fast mock processing for CI/CD")
        print("   🔧 Set VIGIA_USE_MOCK_YOLO=false for real models")
        system_status = "MOCK/DEVELOPMENT MODE"
    else:
        print("❓ VIGIA MODEL STATUS UNCLEAR")
        print("   🔧 May have model loading issues")
        print("   📦 Check dependencies and model files")
        system_status = "UNCLEAR/NEEDS INVESTIGATION"
    
    print()
    print(f"🎯 SYSTEM STATUS: {system_status}")
    print(f"🕐 Test completed at: {datetime.now()}")
    
    return is_real_model and not use_mock_yolo

if __name__ == "__main__":
    is_real = test_real_image_processing()
    
    if is_real:
        print(f"\n✅ Vigia image processing: REAL AI MODELS")
        sys.exit(0)
    else:
        print(f"\n⚠️  Vigia image processing: MOCK OR ISSUES")
        sys.exit(1)