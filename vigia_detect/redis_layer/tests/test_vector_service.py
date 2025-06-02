import pytest
from unittest.mock import Mock, patch
from vigia_detect.redis_layer.vector_service import VectorService

class TestVectorService:
    @pytest.fixture
    def mock_redis(self):
        return Mock()

    def test_create_index(self, mock_redis):
        """Test HNSW index creation"""
        service = VectorService(mock_redis)
        service.create_index("protocols", dims=768, distance_metric="COSINE")
        
        mock_redis.create_index.assert_called_once_with(
            "protocols",
            dims=768,
            distance_metric="COSINE",
            index_type="HNSW"
        )

    def test_search_vectors(self, mock_redis):
        """Test vector similarity search"""
        service = VectorService(mock_redis)
        mock_redis.search.return_value = [{"content": "result"}]
        
        results = service.search("protocols", [0.1]*768, k=3)
        assert len(results) == 1
        mock_redis.search.assert_called_once()

    def test_add_documents(self, mock_redis):
        """Test adding documents to vector store"""
        service = VectorService(mock_redis)
        docs = [{"content": "doc1", "embedding": [0.1]*768}]
        
        service.add_documents("protocols", docs)
        mock_redis.add_documents.assert_called_once_with("protocols", docs)
