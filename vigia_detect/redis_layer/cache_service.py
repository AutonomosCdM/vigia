"""Enhanced semantic caching service for medical data with embeddings."""
import json
import time
import hashlib
import logging
from typing import Optional, Dict, Any, List, Tuple
import redis
from redis.commands.search.field import TextField, NumericField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
import numpy as np

from .config import get_redis_config
from .embeddings import MedicalEmbeddingService

logger = logging.getLogger(__name__)


class MedicalSemanticCache:
    """Enhanced semantic caching for medical queries and responses."""
    
    def __init__(self):
        self.config = get_redis_config()
        self.embedding_service = MedicalEmbeddingService()
        self.embedding_dim = self.embedding_service.embedding_dim
        
        # Initialize Redis client
        self.client = redis.Redis(
            host=self.config.host,
            port=self.config.port,
            password=self.config.password,
            ssl=self.config.ssl,
            decode_responses=True
        )
        
        # Index configuration
        self.index_name = "idx:medical_cache"
        self.key_prefix = "cache:medical:"
        
        # Create index if not exists
        self._create_index()
        
    def _create_index(self):
        """Create Redis search index for semantic cache."""
        try:
            # Check if index already exists
            self.client.ft(self.index_name).info()
            logger.info(f"Index {self.index_name} already exists")
        except redis.ResponseError:
            # Create new index
            logger.info(f"Creating index {self.index_name}")
            
            schema = (
                TextField("query", no_stem=True),
                TextField("response"),
                TextField("medical_context", no_stem=True),
                NumericField("timestamp"),
                NumericField("ttl"),
                NumericField("hit_count"),
                VectorField(
                    "embedding",
                    "FLAT",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": self.embedding_dim,
                        "DISTANCE_METRIC": "COSINE"
                    }
                )
            )
            
            definition = IndexDefinition(
                prefix=[self.key_prefix],
                index_type=IndexType.HASH
            )
            
            self.client.ft(self.index_name).create_index(
                fields=schema,
                definition=definition
            )
            
    def _generate_cache_key(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate unique cache key based on query and context."""
        key_parts = [query]
        
        if context:
            # Add relevant context to make key unique
            if "patient_id" in context:
                key_parts.append(f"patient:{context['patient_id']}")
            if "lpp_grade" in context:
                key_parts.append(f"grade:{context['lpp_grade']}")
            if "location" in context:
                key_parts.append(f"loc:{context['location']}")
                
        key_string = "|".join(key_parts)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        
        return f"{self.key_prefix}{key_hash}"
        
    async def get_semantic_cache(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        threshold: float = 0.85,
        max_results: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response for semantically similar query.
        
        Args:
            query: The query to search for
            context: Medical context (patient_id, lpp_grade, location)
            threshold: Similarity threshold (0-1)
            max_results: Maximum number of similar results to consider
            
        Returns:
            Cached response if found, None otherwise
        """
        try:
            # Generate embedding for query
            query_embedding = self.embedding_service.generate_medical_embedding(query, context)
            
            # Build search query
            search_query = (
                Query(f"*=>[KNN {max_results} @embedding $vector AS score]")
                .return_fields("query", "response", "medical_context", "score", "timestamp")
                .sort_by("score")
                .dialect(2)
            )
            
            # Execute search
            results = self.client.ft(self.index_name).search(
                search_query,
                query_params={
                    "vector": query_embedding.astype(np.float32).tobytes()
                }
            )
            
            # Filter by threshold and context
            for doc in results.docs:
                similarity = 1 - float(doc.score)  # Convert distance to similarity
                
                if similarity >= threshold:
                    # Check context match if provided
                    if context and doc.medical_context:
                        cached_context = json.loads(doc.medical_context)
                        if not self._context_matches(context, cached_context):
                            continue
                            
                    # Update hit count
                    self._increment_hit_count(doc.id)
                    
                    return {
                        "response": json.loads(doc.response),
                        "similarity": similarity,
                        "cached_query": doc.query,
                        "timestamp": int(doc.timestamp)
                    }
                    
            return None
            
        except Exception as e:
            logger.error(f"Error in semantic cache lookup: {e}")
            return None
            
    async def set_semantic_cache(
        self,
        query: str,
        response: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ):
        """
        Cache response with semantic indexing.
        
        Args:
            query: The original query
            response: The response to cache
            context: Medical context
            ttl: Time to live in seconds (defaults to config)
        """
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(query, context)
            
            # Generate embedding
            embedding = self.embedding_service.generate_medical_embedding(query, context)
            
            # Prepare cache data
            cache_data = {
                "query": query,
                "response": json.dumps(response),
                "medical_context": json.dumps(context) if context else "",
                "embedding": embedding.astype(np.float32).tobytes(),
                "timestamp": int(time.time()),
                "ttl": ttl or self.config.cache_ttl,
                "hit_count": 0
            }
            
            # Store in Redis
            self.client.hset(cache_key, mapping=cache_data)
            
            # Set expiration
            if ttl or self.config.cache_ttl:
                self.client.expire(cache_key, ttl or self.config.cache_ttl)
                
            logger.info(f"Cached response for query: {query[:50]}...")
            
        except Exception as e:
            logger.error(f"Error setting semantic cache: {e}")
            
    def _context_matches(self, query_context: Dict, cached_context: Dict) -> bool:
        """Check if medical contexts match for cache validity."""
        # Critical fields that must match
        critical_fields = ["patient_id", "lpp_grade"]
        
        for field in critical_fields:
            if field in query_context and field in cached_context:
                if query_context[field] != cached_context[field]:
                    return False
                    
        return True
        
    def _increment_hit_count(self, cache_key: str):
        """Increment hit count for cache analytics."""
        try:
            self.client.hincrby(cache_key, "hit_count", 1)
        except Exception as e:
            logger.warning(f"Failed to increment hit count: {e}")
            
    async def invalidate_cache(self, pattern: Optional[str] = None):
        """
        Invalidate cache entries.
        
        Args:
            pattern: Optional pattern to match specific entries
        """
        try:
            if pattern:
                # Delete specific pattern
                cursor = 0
                while True:
                    cursor, keys = self.client.scan(
                        cursor, 
                        match=f"{self.key_prefix}*{pattern}*",
                        count=100
                    )
                    if keys:
                        self.client.delete(*keys)
                    if cursor == 0:
                        break
            else:
                # Clear all cache
                self.client.flushdb()
                
            logger.info(f"Cache invalidated: {pattern or 'all'}")
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            # Get all cache keys
            keys = []
            cursor = 0
            while True:
                cursor, batch = self.client.scan(
                    cursor,
                    match=f"{self.key_prefix}*",
                    count=100
                )
                keys.extend(batch)
                if cursor == 0:
                    break
                    
            # Calculate stats
            total_hits = 0
            for key in keys:
                hit_count = self.client.hget(key, "hit_count")
                if hit_count:
                    total_hits += int(hit_count)
                    
            return {
                "total_entries": len(keys),
                "total_hits": total_hits,
                "avg_hits_per_entry": total_hits / len(keys) if keys else 0,
                "index_info": self.client.ft(self.index_name).info()
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
            
    def health_check(self) -> bool:
        """Check Redis connection and index health."""
        try:
            # Check connection
            if not self.client.ping():
                return False
                
            # Check index
            self.client.ft(self.index_name).info()
            return True
            
        except Exception:
            return False