#!/usr/bin/env python3
"""
Demonstration of Redis Phase 2 features for medical semantic caching.

This example shows:
1. Medical context-aware caching
2. Protocol search with vector similarity
3. Cache analytics
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import logging
from typing import Dict, Any

from vigia_detect.redis_layer import create_redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_medical_caching():
    """Demonstrate medical semantic caching with context."""
    client = create_redis_client()
    
    # Example 1: Medical query with patient context
    print("\n=== Example 1: Medical Query Caching ===")
    
    query = "¿Cuál es el tratamiento recomendado para una úlcera por presión en el sacro?"
    patient_context = {
        "patient_id": "PAT-001",
        "lpp_grade": 2,
        "location": "sacro",
        "patient_type": "elderly"
    }
    
    # First query - will miss cache
    print(f"\nQuery: {query}")
    cached_result = await client.get_cached_response(query, patient_context)
    
    if cached_result:
        print(f"✓ Cache HIT! Similarity: {cached_result['similarity']:.2f}")
        print(f"Response: {cached_result['response']}")
    else:
        print("✗ Cache MISS - Generating new response...")
        
        # In real scenario, this would come from LLM
        response = {
            "treatment": "Para LPP grado 2 en sacro: limpieza con suero fisiológico, "
                        "aplicación de apósito hidrocoloide, cambios posturales cada 2 horas",
            "protocols": ["MINSAL-2019", "EPUAP-2019"],
            "next_evaluation": "48-72 horas"
        }
        
        # Cache the response
        await client.cache_response(query, response, patient_context)
        print("Response cached for future queries")
        
    # Second query - similar but not identical
    similar_query = "¿Cómo tratar una lesión por presión sacra?"
    print(f"\n\nSimilar Query: {similar_query}")
    
    cached_result = await client.get_cached_response(similar_query, patient_context)
    if cached_result:
        print(f"✓ Cache HIT! Similarity: {cached_result['similarity']:.2f}")
        print(f"Original query was: {cached_result['cached_query']}")
    else:
        print("✗ Cache MISS")


async def demo_protocol_search():
    """Demonstrate medical protocol vector search."""
    client = create_redis_client()
    
    print("\n\n=== Example 2: Protocol Search ===")
    
    # Search for prevention protocols
    print("\nSearching for LPP prevention protocols...")
    prevention_protocols = await client.get_lpp_prevention_protocol()
    
    for i, protocol in enumerate(prevention_protocols[:2]):
        print(f"\nProtocol {i+1}:")
        print(f"  Title: {protocol['title']}")
        print(f"  Source: {protocol['source']}")
        print(f"  Relevance: {protocol['relevance_score']:.2f}")
        print(f"  Content: {protocol['content'][:150]}...")
        
    # Search for specific grade treatment
    print("\n\nSearching for Grade 3 LPP treatment...")
    grade3_treatment = await client.get_lpp_treatment_protocol(lpp_grade=3)
    
    if grade3_treatment:
        protocol = grade3_treatment[0]
        print(f"Found treatment protocol:")
        print(f"  Title: {protocol['title']}")
        print(f"  Tags: {', '.join(protocol['tags'])}")
        print(f"  Content preview: {protocol['content'][:200]}...")


async def demo_analytics():
    """Demonstrate cache analytics."""
    client = create_redis_client()
    
    print("\n\n=== Example 3: Cache Analytics ===")
    
    # Get cache statistics
    cache_stats = await client.get_cache_analytics()
    print("\nCache Statistics:")
    print(f"  Total entries: {cache_stats.get('total_entries', 0)}")
    print(f"  Total hits: {cache_stats.get('total_hits', 0)}")
    print(f"  Average hits per entry: {cache_stats.get('avg_hits_per_entry', 0):.2f}")
    print(f"  Cache effectiveness: {cache_stats.get('cache_effectiveness', 0):.2%}")
    
    # Get protocol index stats
    protocol_stats = client.get_protocol_index_stats()
    print("\nProtocol Index Statistics:")
    print(f"  Total documents: {protocol_stats.get('num_docs', 0)}")
    print(f"  Index name: {protocol_stats.get('index_name', 'N/A')}")


async def demo_contextual_differences():
    """Demonstrate how context affects caching."""
    client = create_redis_client()
    
    print("\n\n=== Example 4: Context-Aware Caching ===")
    
    query = "¿Cuál es el pronóstico de esta lesión?"
    
    # Same query, different patients
    patient1_context = {
        "patient_id": "PAT-001",
        "lpp_grade": 2,
        "location": "talón"
    }
    
    patient2_context = {
        "patient_id": "PAT-002", 
        "lpp_grade": 3,
        "location": "sacro"
    }
    
    # Cache response for patient 1
    response1 = {
        "prognosis": "LPP grado 2 en talón: recuperación esperada en 2-4 semanas con tratamiento adecuado",
        "risk_factors": ["diabetes", "movilidad reducida"]
    }
    await client.cache_response(query, response1, patient1_context)
    
    # Try to get cache for patient 2 (should miss due to different context)
    print(f"\nQuery: {query}")
    print(f"Patient 1 context: Grade {patient1_context['lpp_grade']}, {patient1_context['location']}")
    print(f"Patient 2 context: Grade {patient2_context['lpp_grade']}, {patient2_context['location']}")
    
    result = await client.get_cached_response(query, patient2_context)
    if result:
        print("✗ ERROR: Should not have found cache for different patient!")
    else:
        print("✓ Correct: Cache miss for different patient context")
        
    # Try with same patient
    result = await client.get_cached_response(query, patient1_context)
    if result:
        print("✓ Correct: Cache hit for same patient context")
    else:
        print("✗ ERROR: Should have found cache for same patient!")


async def main():
    """Run all demonstrations."""
    print("Redis Phase 2 Medical Caching Demo")
    print("==================================")
    
    try:
        # Check Redis health first
        client = create_redis_client()
        health = client.health_check()
        print(f"\nRedis Health Check: {health}")
        
        if not all(health.values()):
            print("\n⚠️  Warning: Redis services not fully healthy!")
            print("Make sure Redis is running and properly configured.")
            return
            
        # Run demos
        await demo_medical_caching()
        await demo_protocol_search()
        await demo_analytics()
        await demo_contextual_differences()
        
        print("\n\nDemo completed successfully! 🎉")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        print("\nMake sure:")
        print("1. Redis is running")
        print("2. Environment variables are set (REDIS_HOST, REDIS_PASSWORD)")
        print("3. Run the migration script: python scripts/migrate_redis_phase2.py")


if __name__ == "__main__":
    asyncio.run(main())