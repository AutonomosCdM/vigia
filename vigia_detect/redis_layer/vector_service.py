from typing import List, Dict, Optional
try:
    from redisvl.index import Index
    from redisvl.query import Query
    REDISVL_AVAILABLE = True
except ImportError:
    REDISVL_AVAILABLE = False
    Index = None
    Query = None

from .config import get_redis_config

class VectorSearchService:
    """Vector search service for medical protocols."""
    
    def __init__(self):
        self.config = get_redis_config()
        if not REDISVL_AVAILABLE:
            raise ImportError("redisvl is not available. Install with: pip install redisvl")
        
        redis_url = f"redis://:{self.config.password}@{self.config.host}:{self.config.port}"
        # Initialize with basic configuration - create index if needed
        self.index = None  # Will be initialized when needed

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


# Alias for backward compatibility
VectorService = VectorSearchService
