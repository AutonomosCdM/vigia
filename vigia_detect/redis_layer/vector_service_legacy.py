from typing import List, Dict, Optional
try:
    from redisvl.index import SearchIndex
    from redisvl.query import VectorQuery
    from redisvl.schema import IndexSchema
    REDISVL_AVAILABLE = True
except ImportError:
    REDISVL_AVAILABLE = False
    SearchIndex = None
    VectorQuery = None
    IndexSchema = None

from .config import get_redis_config

class VectorSearchService:
    """Vector search service for medical protocols."""
    
    def __init__(self):
        if not REDISVL_AVAILABLE:
            raise ImportError("RedisVL is not available. Install with: pip install redisvl")
        
        self.config = get_redis_config()
        
        # Create index schema for medical protocols
        schema = IndexSchema.from_dict({
            "index": {
                "name": self.config.vector_index,
                "prefix": "protocol:",
                "storage_type": "hash"
            },
            "fields": [
                {
                    "name": "text",
                    "type": "text"
                },
                {
                    "name": "embedding",
                    "type": "vector",
                    "attrs": {
                        "dims": 384,  # sentence-transformers default
                        "distance_metric": "COSINE",
                        "algorithm": "HNSW"
                    }
                }
            ]
        })
        
        # Initialize search index
        self.index = SearchIndex(schema)
        
        # Connect to Redis
        redis_url = f"redis://:{self.config.password}@{self.config.host}:{self.config.port}"
        try:
            self.index.connect(redis_url)
        except Exception:
            # Fallback to default Redis connection
            import redis
            self.redis_client = redis.from_url(redis_url)
            self._fallback_mode = True

    def index_protocol(self, protocol_id: str, text: str, embedding: List[float], metadata: Dict):
        """Index a medical protocol with its vector embedding."""
        if hasattr(self, '_fallback_mode'):
            # Simple Redis fallback - store as hash
            key = f"protocol:{protocol_id}"
            data = {
                "text": text,
                "metadata": str(metadata),
                "embedding": str(embedding)  # Convert to string for simple storage
            }
            self.redis_client.hset(key, mapping=data)
        else:
            # Use RedisVL
            key = f"protocol:{protocol_id}"
            self.index.load([{
                "text": text,
                "embedding": embedding,
                **metadata
            }], keys=[key])

    def search_protocols(self, query_embedding: List[float], top_k: int = 3) -> List[Dict]:
        """Search for similar medical protocols."""
        if hasattr(self, '_fallback_mode'):
            # Simple fallback - return empty results
            return []
        
        # Create vector query
        query = VectorQuery(
            vector=query_embedding,
            vector_field_name="embedding",
            return_fields=["text", "metadata"],
            limit=top_k
        )
        
        # Execute search
        results = self.index.query(query)
        return [result.dict() for result in results]

    def create_index(self, schema: Dict = None):
        """Create vector index with custom schema."""
        if hasattr(self, '_fallback_mode'):
            return  # No index creation needed for fallback
        
        try:
            self.index.create()
        except Exception as e:
            # Index might already exist
            pass

    def health_check(self) -> bool:
        """Check Redis connection health."""
        try:
            if hasattr(self, '_fallback_mode'):
                return self.redis_client.ping()
            else:
                return self.index.exists()
        except Exception:
            return False


# Legacy alias
VectorService = VectorSearchService
