"""Tests for medical semantic cache implementation."""
import pytest
import asyncio
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import json

from vigia_detect.redis_layer.cache_service_v2 import MedicalSemanticCache
from vigia_detect.redis_layer.embeddings import MedicalEmbeddingService


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    client = Mock()
    client.ping.return_value = True
    client.ft.return_value.info.return_value = {"num_docs": 10}
    return client


@pytest.fixture
def mock_embedding_service():
    """Create a mock embedding service."""
    service = Mock(spec=MedicalEmbeddingService)
    service.embedding_dim = 384
    service.generate_medical_embedding.return_value = np.random.rand(384)
    return service


@pytest.fixture
def medical_cache(mock_redis_client, mock_embedding_service):
    """Create a medical cache instance with mocks."""
    with patch('vigia_detect.redis_layer.cache_service_v2.redis.Redis', return_value=mock_redis_client):
        with patch('vigia_detect.redis_layer.cache_service_v2.MedicalEmbeddingService', return_value=mock_embedding_service):
            cache = MedicalSemanticCache()
            cache.client = mock_redis_client
            cache.embedding_service = mock_embedding_service
            return cache


class TestMedicalSemanticCache:
    """Test medical semantic cache functionality."""
    
    @pytest.mark.asyncio
    async def test_get_semantic_cache_hit(self, medical_cache, mock_redis_client):
        """Test cache hit scenario."""
        # Setup mock search results
        mock_doc = Mock()
        mock_doc.score = "0.1"  # Distance (1 - 0.1 = 0.9 similarity)
        mock_doc.query = "test query"
        mock_doc.response = json.dumps({"result": "test response"})
        mock_doc.medical_context = json.dumps({"patient_id": "123"})
        mock_doc.timestamp = "1234567890"
        mock_doc.id = "cache:medical:abc123"
        
        mock_results = Mock()
        mock_results.docs = [mock_doc]
        
        mock_redis_client.ft.return_value.search.return_value = mock_results
        
        # Test cache lookup
        result = await medical_cache.get_semantic_cache(
            query="test medical query",
            context={"patient_id": "123"},
            threshold=0.85
        )
        
        assert result is not None
        assert result["similarity"] == 0.9
        assert result["response"]["result"] == "test response"
        assert result["cached_query"] == "test query"
        
    @pytest.mark.asyncio
    async def test_get_semantic_cache_miss(self, medical_cache, mock_redis_client):
        """Test cache miss scenario."""
        # Setup empty search results
        mock_results = Mock()
        mock_results.docs = []
        
        mock_redis_client.ft.return_value.search.return_value = mock_results
        
        result = await medical_cache.get_semantic_cache(
            query="new medical query",
            threshold=0.85
        )
        
        assert result is None
        
    @pytest.mark.asyncio
    async def test_get_semantic_cache_below_threshold(self, medical_cache, mock_redis_client):
        """Test cache result below similarity threshold."""
        # Setup mock search results with low similarity
        mock_doc = Mock()
        mock_doc.score = "0.3"  # Distance (1 - 0.3 = 0.7 similarity, below 0.85 threshold)
        
        mock_results = Mock()
        mock_results.docs = [mock_doc]
        
        mock_redis_client.ft.return_value.search.return_value = mock_results
        
        result = await medical_cache.get_semantic_cache(
            query="test query",
            threshold=0.85
        )
        
        assert result is None
        
    @pytest.mark.asyncio
    async def test_set_semantic_cache(self, medical_cache, mock_redis_client, mock_embedding_service):
        """Test setting cache entry."""
        query = "What is the treatment for grade 2 LPP?"
        response = {"treatment": "Apply hydrocolloid dressing"}
        context = {"patient_id": "123", "lpp_grade": 2}
        
        await medical_cache.set_semantic_cache(
            query=query,
            response=response,
            context=context,
            ttl=3600
        )
        
        # Verify Redis operations
        mock_redis_client.hset.assert_called_once()
        mock_redis_client.expire.assert_called_once()
        
        # Verify embedding was generated
        mock_embedding_service.generate_medical_embedding.assert_called_once_with(query, context)
        
    @pytest.mark.asyncio
    async def test_context_matching(self, medical_cache):
        """Test medical context matching logic."""
        query_context = {"patient_id": "123", "lpp_grade": 2}
        
        # Matching context
        cached_context = {"patient_id": "123", "lpp_grade": 2}
        assert medical_cache._context_matches(query_context, cached_context) is True
        
        # Different patient
        cached_context = {"patient_id": "456", "lpp_grade": 2}
        assert medical_cache._context_matches(query_context, cached_context) is False
        
        # Different grade
        cached_context = {"patient_id": "123", "lpp_grade": 3}
        assert medical_cache._context_matches(query_context, cached_context) is False
        
    @pytest.mark.asyncio
    async def test_invalidate_cache_pattern(self, medical_cache, mock_redis_client):
        """Test cache invalidation with pattern."""
        mock_redis_client.scan.return_value = (0, ["cache:medical:123", "cache:medical:456"])
        
        await medical_cache.invalidate_cache(pattern="patient:123")
        
        mock_redis_client.scan.assert_called()
        mock_redis_client.delete.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_get_cache_stats(self, medical_cache, mock_redis_client):
        """Test cache statistics retrieval."""
        # Setup mock data
        mock_redis_client.scan.return_value = (0, ["cache:medical:1", "cache:medical:2"])
        mock_redis_client.hget.side_effect = ["5", "10"]  # Hit counts
        
        stats = await medical_cache.get_cache_stats()
        
        assert stats["total_entries"] == 2
        assert stats["total_hits"] == 15
        assert stats["avg_hits_per_entry"] == 7.5
        
    def test_health_check(self, medical_cache, mock_redis_client):
        """Test health check functionality."""
        # Healthy scenario
        mock_redis_client.ping.return_value = True
        assert medical_cache.health_check() is True
        
        # Unhealthy scenario
        mock_redis_client.ping.return_value = False
        assert medical_cache.health_check() is False


class TestMedicalEmbeddingService:
    """Test medical embedding service."""
    
    def test_enhance_with_context(self):
        """Test text enhancement with medical context."""
        service = MedicalEmbeddingService()
        
        text = "Treatment recommendation"
        context = {
            "lpp_grade": 2,
            "location": "sacrum",
            "patient_type": "elderly"
        }
        
        enhanced = service._enhance_with_context(text, context)
        
        assert "LPP Grade 2" in enhanced
        assert "Location: sacrum" in enhanced
        assert "Patient: elderly" in enhanced
        assert text in enhanced
        
    def test_preprocess_medical_text(self):
        """Test medical text preprocessing."""
        service = MedicalEmbeddingService()
        
        text = "Patient has LPP grade 2, following EPUAP guidelines"
        processed = service.preprocess_medical_text(text)
        
        assert "lesión por presión" in processed
        assert "European Pressure Ulcer Advisory Panel" in processed