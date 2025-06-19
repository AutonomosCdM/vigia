"""Redis integration layer for LPP-Detect system.

This package provides:
- Semantic caching for LLM responses with medical context awareness
- Vector search capabilities for medical protocols
- Medical embedding generation
- Session management for medical agent conversations

Phase 2 Implementation:
- MedicalRedisClient: Unified interface for all Redis operations
- MedicalSemanticCache: Context-aware caching for medical queries
- MedicalProtocolIndexer: Vector search for medical protocols
- MedicalEmbeddingService: Specialized embeddings for medical text
"""

from .client import MedicalRedisClient
from .cache_service import MedicalSemanticCache
from .protocol_indexer import EnhancedProtocolIndexer as MedicalProtocolIndexer
from .embeddings import MedicalEmbeddingService, EmbeddingService
from .mock_client import MockRedisClient, create_redis_client

__all__ = [
    "MedicalRedisClient",
    "MedicalSemanticCache", 
    "MedicalProtocolIndexer",
    "MedicalEmbeddingService",
    "EmbeddingService",
    "MockRedisClient",
    "create_redis_client"
]
