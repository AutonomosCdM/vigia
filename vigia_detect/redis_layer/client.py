from typing import Optional, Dict, List
from .cache_service import SemanticCache
from .vector_service import VectorSearchService
from .config import get_redis_config

class RedisClient:
    """Unified Redis client for LPP-Detect system."""
    
    def __init__(self):
        self.config = get_redis_config()
        self.cache = SemanticCache()
        self.vector = VectorSearchService()

    async def get_cached_response(self, query: str) -> Optional[Dict]:
        """Get cached LLM response if semantically similar query exists."""
        return await self.cache.get_semantic_cache(query)

    async def cache_response(self, query: str, response: Dict):
        """Cache LLM response with semantic key."""
        await self.cache.set_semantic_cache(query, response)

    async def search_protocols(self, embedding: List[float]) -> List[Dict]:
        """Search for relevant medical protocols."""
        return await self.vector.search_protocols(embedding)

    async def index_protocol(self, protocol_id: str, text: str, embedding: List[float], metadata: Dict):
        """Index a medical protocol with its embedding."""
        await self.vector.index_protocol(protocol_id, text, embedding, metadata)

    def health_check(self) -> bool:
        """Check health of all Redis services."""
        return self.cache.health_check() and self.vector.health_check()
