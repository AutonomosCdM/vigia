import pytest
from unittest.mock import Mock, patch
from vigia_detect.redis_layer.cache_service import SemanticCache

class TestSemanticCache:
    @pytest.fixture
    def mock_redis(self):
        return Mock()

    def test_cache_hit(self, mock_redis):
        """Test semantic cache hit with similar query"""
        cache = SemanticCache(mock_redis)
        mock_redis.similarity_search.return_value = [{"content": "cached response"}]
        
        result = cache.get("new query", threshold=0.7)
        assert result == "cached response"
        mock_redis.similarity_search.assert_called_once()

    def test_cache_miss(self, mock_redis):
        """Test cache miss when no similar results"""
        cache = SemanticCache(mock_redis)
        mock_redis.similarity_search.return_value = []
        
        result = cache.get("new query", threshold=0.7)
        assert result is None

    def test_cache_store(self, mock_redis):
        """Test storing new cache entry"""
        cache = SemanticCache(mock_redis)
        cache.store("query", "response")
        
        mock_redis.store.assert_called_once_with("query", "response")
