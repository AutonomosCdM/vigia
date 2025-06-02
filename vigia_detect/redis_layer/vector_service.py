from typing import List, Dict, Optional
from redisvl import RedisVL
from .config import get_redis_config

class VectorSearchService:
    """Vector search service for medical protocols."""
    
    def __init__(self):
        self.config = get_redis_config()
        self.rvl = RedisVL(
            redis_url=f"redis://:{self.config.password}@{self.config.host}:{self.config.port}",
            index_name=self.config.vector_index
        )

    async def index_protocol(self, protocol_id: str, text: str, embedding: List[float], metadata: Dict):
        """Index a medical protocol with its vector embedding."""
        await self.rvl.set(
            key=protocol_id,
            vector=embedding,
            payload={
                "text": text,
                "metadata": metadata
            }
        )

    async def search_protocols(self, query_embedding: List[float], top_k: int = 3) -> List[Dict]:
        """Search for similar medical protocols."""
        results = await self.rvl.search(
            vector=query_embedding,
            vector_field="embedding",
            return_fields=["text", "metadata"],
            limit=top_k
        )
        return results

    async def create_index(self, schema: Dict):
        """Create vector index with custom schema."""
        await self.rvl.create_index(schema)

    def health_check(self) -> bool:
        """Check Redis connection health."""
        try:
            return self.rvl.ping()
        except Exception:
            return False
