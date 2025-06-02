"""Enhanced Redis client with medical semantic caching and protocol search."""
import logging
from typing import Optional, Dict, Any, List

from .cache_service_v2 import MedicalSemanticCache
from .protocol_indexer import MedicalProtocolIndexer
from .config import get_redis_config

logger = logging.getLogger(__name__)


class MedicalRedisClient:
    """
    Unified client for medical data caching and protocol search.
    
    This client provides:
    - Semantic caching with medical context awareness
    - Medical protocol vector search
    - Performance analytics
    """
    
    def __init__(self):
        """Initialize Redis client with medical-specific services."""
        self.config = get_redis_config()
        self.cache = MedicalSemanticCache()
        self.protocol_indexer = MedicalProtocolIndexer()
        logger.info("Initialized MedicalRedisClient")
        
    # === Semantic Cache Methods ===
    
    async def get_cached_response(
        self,
        query: str,
        patient_context: Optional[Dict[str, Any]] = None,
        similarity_threshold: float = 0.85
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response for a medical query.
        
        Args:
            query: The medical query
            patient_context: Context including patient_id, lpp_grade, location
            similarity_threshold: Minimum similarity for cache hit
            
        Returns:
            Cached response if found, None otherwise
        """
        return await self.cache.get_semantic_cache(
            query=query,
            context=patient_context,
            threshold=similarity_threshold
        )
        
    async def cache_response(
        self,
        query: str,
        response: Dict[str, Any],
        patient_context: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ):
        """
        Cache a medical response with semantic indexing.
        
        Args:
            query: The original query
            response: The response to cache
            patient_context: Medical context
            ttl: Time to live in seconds
        """
        await self.cache.set_semantic_cache(
            query=query,
            response=response,
            context=patient_context,
            ttl=ttl
        )
        
    # === Protocol Search Methods ===
    
    async def search_medical_protocols(
        self,
        query: str,
        lpp_grade: Optional[int] = None,
        context_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search medical protocols for relevant information.
        
        Args:
            query: Search query
            lpp_grade: Specific LPP grade (1-4)
            context_type: Type of information (treatment, prevention, assessment)
            limit: Maximum results
            
        Returns:
            List of relevant protocol sections
        """
        filters = {}
        if lpp_grade:
            filters["lpp_grade"] = f"grade_{lpp_grade}"
        if context_type:
            filters["tags"] = context_type
            
        return await self.protocol_indexer.search_protocols(
            query=query,
            filters=filters,
            limit=limit
        )
        
    async def get_lpp_treatment_protocol(self, lpp_grade: int) -> List[Dict[str, Any]]:
        """
        Get specific treatment protocols for an LPP grade.
        
        Args:
            lpp_grade: LPP grade (1-4)
            
        Returns:
            Treatment protocol sections
        """
        return await self.protocol_indexer.get_protocol_context(
            lpp_grade=lpp_grade,
            context_type="treatment"
        )
        
    async def get_lpp_prevention_protocol(self) -> List[Dict[str, Any]]:
        """Get prevention protocols for LPP."""
        return await self.protocol_indexer.search_protocols(
            query="prevención úlceras por presión",
            filters={"tags": "prevention"},
            limit=3
        )
        
    # === Analytics Methods ===
    
    async def get_cache_analytics(self) -> Dict[str, Any]:
        """Get analytics about cache performance."""
        stats = await self.cache.get_cache_stats()
        
        # Calculate additional metrics
        if stats.get("total_entries", 0) > 0:
            stats["cache_effectiveness"] = (
                stats["total_hits"] / stats["total_entries"] 
                if stats["total_entries"] > 0 else 0
            )
            
        return stats
        
    def get_protocol_index_stats(self) -> Dict[str, Any]:
        """Get statistics about indexed protocols."""
        return self.protocol_indexer.get_index_stats()
        
    # === Management Methods ===
    
    def index_protocols_from_docs(self, docs_directory: str = "docs/papers"):
        """
        Index medical protocols from documentation directory.
        
        Args:
            docs_directory: Path to directory with protocol PDFs
        """
        self.protocol_indexer.index_protocols_from_directory(docs_directory)
        
    def index_custom_protocol(self, protocol_data: Dict[str, Any]):
        """
        Index a custom protocol from structured data.
        
        Args:
            protocol_data: Protocol data with title, content, tags, etc.
        """
        self.protocol_indexer.index_protocol_json(protocol_data)
        
    async def invalidate_patient_cache(self, patient_id: str):
        """Invalidate all cache entries for a specific patient."""
        await self.cache.invalidate_cache(pattern=f"patient:{patient_id}")
        
    async def clear_all_cache(self):
        """Clear all cached data (use with caution)."""
        await self.cache.invalidate_cache()
        
    # === Health Check ===
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all Redis services."""
        return {
            "cache_service": self.cache.health_check(),
            "protocol_index": bool(self.protocol_indexer.get_index_stats())
        }
        
    # === Context Manager Support ===
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Cleanup if needed
        pass


# Example usage functions
async def example_medical_query():
    """Example of using the medical Redis client."""
    client = MedicalRedisClient()
    
    # Example 1: Check cache for a medical query
    query = "¿Cuál es el tratamiento para LPP grado 2?"
    patient_context = {
        "patient_id": "12345",
        "lpp_grade": 2,
        "location": "sacro"
    }
    
    # Try cache first
    cached = await client.get_cached_response(query, patient_context)
    if cached:
        print(f"Cache hit! Similarity: {cached['similarity']}")
        return cached['response']
        
    # If not cached, search protocols
    protocols = await client.search_medical_protocols(
        query=query,
        lpp_grade=2,
        context_type="treatment"
    )
    
    # Generate response from protocols (would use LLM in practice)
    response = {
        "treatment": "Based on protocols...",
        "protocols": protocols[:2]
    }
    
    # Cache the response
    await client.cache_response(query, response, patient_context)
    
    return response


async def example_protocol_search():
    """Example of searching medical protocols."""
    client = MedicalRedisClient()
    
    # Search for prevention protocols
    prevention = await client.get_lpp_prevention_protocol()
    
    # Get specific treatment protocol
    treatment = await client.get_lpp_treatment_protocol(lpp_grade=3)
    
    return {
        "prevention": prevention,
        "treatment": treatment
    }