#!/usr/bin/env python3
"""
Script para debuggear el procesador de WhatsApp
"""
import sys
import os
sys.path.append('.')

try:
    from vigia_detect.messaging.whatsapp.processor import process_whatsapp_image
    print("✅ Procesador WhatsApp importado")
    
    # Test con imagen de httpbin
    result = process_whatsapp_image(
        'https://httpbin.org/image/jpeg',
        patient_code='CD-2025-001'
    )
    
    print(f"Success: {result.get('success')}")
    if result.get('success'):
        print(f"Detections: {len(result.get('detections', []))}")
        print(f"Message: {result.get('message', '')[:100]}...")
    else:
        print(f"Error: {result.get('error')}")
        print(f"Message: {result.get('message')}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()