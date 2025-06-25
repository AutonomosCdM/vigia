#!/usr/bin/env python3
"""Test real PHI tokenization functionality."""

import asyncio
from vigia_detect.core.phi_tokenization_client import PHITokenizationClient

async def test_phi_tokenization_real():
    print("=== TESTING REAL PHI TOKENIZATION ===")
    
    # Create real client
    client = PHITokenizationClient()
    print(f"✅ PHI Client created")
    print(f"Service URL: {client.config.tokenization_service_url}")
    print(f"Staff ID: {client.config.staff_id}")
    
    # Test tokenization (even if service not running)
    test_cases = [
        {
            "hospital_mrn": "MRN-2025-001-BW",
            "patient_data": {
                "age": 75,
                "diabetes": True,
                "admission_date": "2025-06-23"
            }
        },
        {
            "hospital_mrn": "MRN-2025-002-JD", 
            "patient_data": {
                "age": 42,
                "hypertension": True
            }
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Hospital MRN: {case['hospital_mrn']}")
        
        try:
            # Test tokenization
            result = await client.tokenize_patient(
                hospital_mrn=case["hospital_mrn"],
                request_purpose="lpp_medical_assessment"
            )
            
            print(f"✅ Tokenization successful:")
            print(f"  Token ID: {result.token_id}")
            print(f"  Patient Alias: {result.patient_alias}")
            print(f"  Created: {result.created_at}")
            
            # Test cache functionality
            cached_result = client.cache.get(case["hospital_mrn"])
            if cached_result:
                print(f"✅ Cache working: {cached_result.token_id}")
            else:
                print("⚠️  No cache entry (expected if service not running)")
                
        except Exception as e:
            print(f"⚠️  Tokenization error: {str(e)}")
            print("Expected if PHI service not running at localhost:8080")
    
    # Test client configuration
    print(f"\n=== CLIENT CONFIGURATION ===")
    print(f"Cache TTL: {client.config.token_cache_ttl_minutes} minutes")
    print(f"Max Cache Size: {client.config.max_cache_size}")
    print(f"Request Timeout: {client.config.request_timeout_seconds}s")
    print(f"Max Retries: {client.config.max_retries}")

if __name__ == "__main__":
    asyncio.run(test_phi_tokenization_real())