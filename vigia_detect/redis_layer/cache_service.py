import redis
import time
from redisvl import RedisVL
from typing import Optional, Dict, Any
from .config import get_redis_config

class SemanticCache:
    """Semantic caching service for LLM responses."""
    
    def __init__(self):
        self.config = get_redis_config()
        self.client = redis.Redis(
            host=self.config.host,
            port=self.config.port,
            password=self.config.password,
            ssl=self.config.ssl
        )
        self.rvl = RedisVL(
            redis_url=f"redis://:{self.config.password}@{self.config.host}:{self.config.port}",
            index_name=self.config.cache_index
        )

    async def get_semantic_cache(self, query: str, threshold: float = 0.85) -> Optional[Dict[str, Any]]:
        """Get cached response for semantically similar query."""
        results = await self.rvl.search(
            vector=query,
            vector_field="embedding",
            return_fields=["response", "metadata"],
            limit=1,
            distance_threshold=threshold
        )
        return results[0] if results else None

    async def set_semantic_cache(self, query: str, response: Dict[str, Any]):
        """Cache LLM response with semantic key."""
        await self.rvl.set(
            key=query,
            vector=query,
            payload={
                "response": response,
                "metadata": {
                    "timestamp": int(time.time()),
                    "ttl": self.config.cache_ttl
                }
            }
        )
        self.client.expire(query, self.config.cache_ttl)

    def health_check(self) -> bool:
        """Check Redis connection health."""
        try:
            return self.client.ping()
        except redis.RedisError:
            return False
