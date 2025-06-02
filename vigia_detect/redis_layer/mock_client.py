"""Mock Redis client for development and testing without Redis."""
import logging
from typing import Optional, Dict, Any, List
import json
import time
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


class MockRedisClient:
    """Mock Redis client that simulates Redis behavior in memory."""
    
    def __init__(self):
        """Initialize mock Redis with in-memory storage."""
        self.cache_store = {}
        self.protocol_store = {}
        self.embeddings_cache = {}
        logger.info("Initialized MockRedisClient (in-memory mode)")
        
    async def get_cached_response(
        self,
        query: str,
        patient_context: Optional[Dict[str, Any]] = None,
        similarity_threshold: float = 0.85
    ) -> Optional[Dict[str, Any]]:
        """Mock cache lookup - returns None to simulate cache miss."""
        cache_key = f"{query}:{json.dumps(patient_context or {})}"
        
        if cache_key in self.cache_store:
            logger.info(f"Mock cache HIT for query: {query[:50]}...")
            return self.cache_store[cache_key]
        
        logger.info(f"Mock cache MISS for query: {query[:50]}...")
        return None
        
    async def cache_response(
        self,
        query: str,
        response: Dict[str, Any],
        patient_context: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ):
        """Mock cache storage."""
        cache_key = f"{query}:{json.dumps(patient_context or {})}"
        
        self.cache_store[cache_key] = {
            "response": response,
            "similarity": 1.0,
            "cached_query": query,
            "timestamp": int(time.time())
        }
        
        logger.info(f"Mock cached response for query: {query[:50]}...")
        
    async def search_medical_protocols(
        self,
        query: str,
        lpp_grade: Optional[int] = None,
        context_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Mock protocol search."""
        # Return mock protocols
        mock_protocols = []
        
        if context_type == "prevention":
            mock_protocols.append({
                "title": "Protocolo de Prevención de LPP - MINSAL",
                "content": "Las medidas de prevención incluyen cambios posturales cada 2 horas, "
                          "uso de superficies especiales, evaluación de riesgo con escala de Braden...",
                "source": "MINSAL Chile 2019",
                "page": 15,
                "tags": ["prevention", "care"],
                "lpp_grades": ["grade_0", "grade_1"],
                "relevance_score": 0.92
            })
            
        if lpp_grade:
            mock_protocols.append({
                "title": f"Tratamiento LPP Grado {lpp_grade} - Guía EPUAP",
                "content": f"El tratamiento para LPP grado {lpp_grade} incluye limpieza con suero "
                          f"fisiológico, aplicación de apósitos específicos según el grado...",
                "source": "EPUAP/NPUAP Guidelines",
                "page": 45,
                "tags": ["treatment", "care"],
                "lpp_grades": [f"grade_{lpp_grade}"],
                "relevance_score": 0.88
            })
            
        return mock_protocols[:limit]
        
    async def get_lpp_treatment_protocol(self, lpp_grade: int) -> List[Dict[str, Any]]:
        """Mock treatment protocol retrieval."""
        return await self.search_medical_protocols(
            query=f"tratamiento LPP grado {lpp_grade}",
            lpp_grade=lpp_grade,
            context_type="treatment",
            limit=3
        )
        
    async def get_lpp_prevention_protocol(self) -> List[Dict[str, Any]]:
        """Mock prevention protocol retrieval."""
        return await self.search_medical_protocols(
            query="prevención úlceras por presión",
            context_type="prevention",
            limit=3
        )
        
    async def get_cache_analytics(self) -> Dict[str, Any]:
        """Mock cache analytics."""
        total_entries = len(self.cache_store)
        
        return {
            "total_entries": total_entries,
            "total_hits": total_entries * 3,  # Simulate some hits
            "avg_hits_per_entry": 3.0,
            "cache_effectiveness": 0.75
        }
        
    def get_protocol_index_stats(self) -> Dict[str, Any]:
        """Mock protocol index stats."""
        return {
            "num_docs": len(self.protocol_store) + 10,  # Simulate some indexed docs
            "index_name": "mock_medical_protocols",
            "index_options": {"mock": True},
            "fields": ["title", "content", "embedding"]
        }
        
    def index_protocols_from_docs(self, docs_directory: str = "docs/papers"):
        """Mock protocol indexing."""
        logger.info(f"Mock indexing protocols from {docs_directory}")
        # Simulate adding some protocols
        self.protocol_store["prevention_001"] = {
            "title": "Prevention Guidelines",
            "content": "Mock prevention content"
        }
        
    def index_custom_protocol(self, protocol_data: Dict[str, Any]):
        """Mock custom protocol indexing."""
        protocol_id = protocol_data.get("id", f"custom_{len(self.protocol_store)}")
        self.protocol_store[protocol_id] = protocol_data
        logger.info(f"Mock indexed protocol: {protocol_data.get('title', 'Unknown')}")
        
    async def invalidate_patient_cache(self, patient_id: str):
        """Mock cache invalidation."""
        # Remove entries containing the patient_id
        keys_to_remove = [
            key for key in self.cache_store
            if f'"patient_id": "{patient_id}"' in key
        ]
        for key in keys_to_remove:
            del self.cache_store[key]
        logger.info(f"Mock invalidated cache for patient: {patient_id}")
        
    async def clear_all_cache(self):
        """Mock clear all cache."""
        self.cache_store.clear()
        logger.info("Mock cleared all cache")
        
    def health_check(self) -> Dict[str, bool]:
        """Mock health check - always healthy."""
        return {
            "cache_service": True,
            "protocol_index": True
        }
        
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass


# Create a factory function that returns mock client when Redis is not available
def create_redis_client():
    """Create Redis client - returns mock if Redis not available."""
    try:
        # Try to import the real client
        from .client_v2 import MedicalRedisClient
        
        # Try to create real client
        client = MedicalRedisClient()
        
        # Test connection
        if client.health_check()["cache_service"]:
            logger.info("Using real Redis client")
            return client
            
    except Exception as e:
        logger.warning(f"Redis not available: {e}")
        
    logger.info("Using mock Redis client (in-memory mode)")
    return MockRedisClient()