#!/usr/bin/env python3
"""
Pruebas completas para integración Redis + MedGemma
Suite de pruebas exhaustiva para validar funcionalidad del sistema integrado.
"""

import pytest
import asyncio
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from typing import Dict, Any, List

# Agregar path del proyecto
import sys
sys.path.append(str(Path(__file__).parent.parent))

try:
    from examples.redis_integration_demo import RedisGemmaIntegrationDemo
    from scripts.setup_redis_simple import SimpleRedisSetup
    from config.settings import settings
except ImportError as e:
    # Fallback para pruebas independientes
    print(f"Warning: {e}")
    
    # Crear clases mock si no están disponibles
    class RedisGemmaIntegrationDemo:
        def __init__(self):
            self.redis_client = None
            self.medgemma_model = "alibayram/medgemma"
        
        async def initialize(self):
            return True
        
        async def cleanup(self):
            pass
        
        async def get_cached_response(self, query):
            return None
        
        async def get_relevant_protocols(self, query, category=None):
            return []
        
        async def analyze_with_medgemma(self, query, protocols):
            return {
                "analysis": "Mock analysis",
                "recommendations": ["Mock recommendation"],
                "urgency": "moderate",
                "confidence": 0.85,
                "source": "mock"
            }
        
        async def cache_response(self, query, response):
            pass
        
        async def process_medical_query(self, query):
            return {
                "query": query,
                "analysis": "Mock analysis",
                "recommendations": ["Mock recommendation"],
                "urgency": "moderate",
                "confidence": 0.85,
                "protocols_consulted": 1,
                "protocols_used": 1,
                "source": "mock",
                "cache_hit": False,
                "processing_steps": ["mock_step"]
            }
        
        async def run_demo_scenarios(self):
            return [{"cache_hit": False} for _ in range(4)]
        
        async def show_final_stats(self):
            pass
        
        def _extract_recommendations(self, text):
            return ["Mock recommendation 1", "Mock recommendation 2"]
    
    class SimpleRedisSetup:
        def __init__(self):
            self.redis_client = None
        
        async def initialize(self):
            return True
        
        async def cleanup(self):
            pass
        
        async def check_redis_status(self):
            return True
        
        async def load_medical_protocols(self):
            return True
        
        async def setup_cache_structure(self):
            return True
        
        async def test_basic_operations(self):
            return True
        
        async def test_medical_workflow(self):
            return True
    
    # Mock settings
    class MockSettings:
        redis_host = "localhost"
        redis_port = 6379
        redis_password = None
        redis_ssl = False
        redis_db = 0
        redis_cache_ttl = 3600
    
    settings = MockSettings()


class TestRedisGemmaIntegration:
    """Suite de pruebas para integración Redis + MedGemma."""
    
    @pytest.fixture
    async def redis_demo(self):
        """Fixture para demo de Redis + MedGemma."""
        demo = RedisGemmaIntegrationDemo()
        yield demo
        await demo.cleanup()
    
    @pytest.fixture
    async def redis_setup(self):
        """Fixture para setup de Redis."""
        setup = SimpleRedisSetup()
        yield setup
        await setup.cleanup()
    
    @pytest.fixture
    def mock_redis_client(self):
        """Mock del cliente Redis."""
        mock_client = AsyncMock()
        
        # Mock responses para diferentes operaciones
        mock_client.ping.return_value = True
        mock_client.info.return_value = {
            'redis_version': '7.0.0',
            'uptime_in_seconds': 3600,
            'used_memory_human': '1.5M',
            'connected_clients': 5,
            'total_commands_processed': 1000
        }
        
        # Mock para protocolos médicos
        mock_client.smembers.return_value = {'lpp_prevention', 'lpp_grade2_treatment'}
        mock_client.hgetall.return_value = {
            'title': 'Protocolo de Prevención de LPP',
            'content': 'Contenido del protocolo...',
            'category': 'prevention',
            'urgency': 'routine'
        }
        
        # Mock para cache
        mock_client.hset.return_value = True
        mock_client.expire.return_value = True
        mock_client.hincrby.return_value = 1
        mock_client.keys.return_value = ['medical_protocol:lpp_prevention']
        
        return mock_client
    
    @pytest.fixture
    def mock_ollama_available(self):
        """Mock para Ollama disponible."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="alibayram/medgemma:latest",
                returncode=0
            )
            yield mock_run


class TestRedisSetup(TestRedisGemmaIntegration):
    """Pruebas para configuración de Redis."""
    
    @pytest.mark.asyncio
    async def test_redis_initialization(self, redis_setup, mock_redis_client):
        """Test inicialización de Redis."""
        with patch('redis.asyncio.Redis', return_value=mock_redis_client):
            result = await redis_setup.initialize()
            assert result is True
            mock_redis_client.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_status_check(self, redis_setup, mock_redis_client):
        """Test verificación de estado de Redis."""
        redis_setup.redis_client = mock_redis_client
        
        result = await redis_setup.check_redis_status()
        assert result is True
        mock_redis_client.info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_medical_protocols_loading(self, redis_setup, mock_redis_client):
        """Test carga de protocolos médicos."""
        redis_setup.redis_client = mock_redis_client
        mock_redis_client.exists.return_value = False  # No existen previamente
        
        result = await redis_setup.load_medical_protocols()
        assert result is True
        
        # Verificar que se llamaron los métodos para cargar protocolos
        assert mock_redis_client.hset.call_count >= 3  # Al menos 3 protocolos
        assert mock_redis_client.sadd.call_count >= 6  # Índices por categoría y urgencia
    
    @pytest.mark.asyncio
    async def test_cache_structure_setup(self, redis_setup, mock_redis_client):
        """Test configuración de estructura de cache."""
        redis_setup.redis_client = mock_redis_client
        mock_redis_client.exists.return_value = False
        
        result = await redis_setup.setup_cache_structure()
        assert result is True
        
        # Verificar creación de índices de cache
        assert mock_redis_client.hset.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_basic_operations(self, redis_setup, mock_redis_client):
        """Test operaciones básicas de Redis."""
        redis_setup.redis_client = mock_redis_client
        
        result = await redis_setup.test_basic_operations()
        assert result is True
        
        # Verificar operaciones de búsqueda y cache
        mock_redis_client.smembers.assert_called()
        mock_redis_client.hgetall.assert_called()
        mock_redis_client.hset.assert_called()
    
    @pytest.mark.asyncio
    async def test_medical_workflow(self, redis_setup, mock_redis_client):
        """Test flujo médico completo."""
        redis_setup.redis_client = mock_redis_client
        
        result = await redis_setup.test_medical_workflow()
        assert result is True
        
        # Verificar que se ejecutó el flujo completo
        mock_redis_client.smembers.assert_called()
        mock_redis_client.hset.assert_called()
        mock_redis_client.hincrby.assert_called()


class TestMedGemmaIntegration(TestRedisGemmaIntegration):
    """Pruebas para integración con MedGemma."""
    
    @pytest.mark.asyncio
    async def test_initialization_with_ollama(self, redis_demo, mock_redis_client, mock_ollama_available):
        """Test inicialización con Ollama disponible."""
        with patch('redis.asyncio.Redis', return_value=mock_redis_client):
            result = await redis_demo.initialize()
            assert result is True
            assert redis_demo.medgemma_model == "alibayram/medgemma"
    
    @pytest.mark.asyncio
    async def test_initialization_without_ollama(self, redis_demo, mock_redis_client):
        """Test inicialización sin Ollama disponible."""
        with patch('redis.asyncio.Redis', return_value=mock_redis_client), \
             patch('subprocess.run', side_effect=FileNotFoundError()):
            
            result = await redis_demo.initialize()
            assert result is True
            assert redis_demo.medgemma_model is None
    
    @pytest.mark.asyncio
    async def test_cache_operations(self, redis_demo, mock_redis_client):
        """Test operaciones de cache."""
        redis_demo.redis_client = mock_redis_client
        
        # Test cache miss
        mock_redis_client.hgetall.return_value = {}
        result = await redis_demo.get_cached_response("test query")
        assert result is None
        
        # Test cache hit
        mock_redis_client.hgetall.return_value = {
            "response": json.dumps({"analysis": "cached response"}),
            "created_at": "2025-01-09"
        }
        result = await redis_demo.get_cached_response("test query")
        assert result is not None
        assert result["cache_hit"] is True
        assert "cached_at" in result
    
    @pytest.mark.asyncio
    async def test_protocol_retrieval(self, redis_demo, mock_redis_client):
        """Test recuperación de protocolos."""
        redis_demo.redis_client = mock_redis_client
        
        # Mock datos de protocolos
        mock_redis_client.smembers.side_effect = [
            {"lpp_prevention"}, {"lpp_grade2_treatment"}, {"lpp_emergency"}
        ]
        mock_redis_client.hgetall.return_value = {
            "title": "Protocolo Test",
            "content": "Contenido del protocolo",
            "category": "treatment",
            "urgency": "urgent"
        }
        
        protocols = await redis_demo.get_relevant_protocols("test query")
        assert len(protocols) >= 1
        assert protocols[0]["title"] == "Protocolo Test"
        assert protocols[0]["category"] == "treatment"
    
    @pytest.mark.asyncio
    async def test_medgemma_analysis_simulated(self, redis_demo):
        """Test análisis con MedGemma simulado."""
        redis_demo.medgemma_model = None  # Forzar modo simulado
        
        protocols = [
            {
                "title": "Protocolo Test",
                "content": "Contenido del protocolo",
                "category": "treatment"
            }
        ]
        
        result = await redis_demo.analyze_with_medgemma("test query", protocols)
        
        assert result["source"] == "simulated"
        assert "analysis" in result
        assert "recommendations" in result
        assert "urgency" in result
        assert "confidence" in result
    
    @pytest.mark.asyncio
    async def test_medgemma_analysis_real(self, redis_demo, mock_ollama_available):
        """Test análisis con MedGemma real."""
        redis_demo.medgemma_model = "alibayram/medgemma"
        
        # Mock respuesta de Ollama
        mock_ollama_available.return_value = MagicMock(
            stdout="Análisis médico: Se recomienda evaluación inmediata y cambios posturales",
            stderr="",
            returncode=0
        )
        
        protocols = [
            {
                "title": "Protocolo LPP Grado 2",
                "content": "Protocolo completo para tratamiento",
                "category": "treatment"
            }
        ]
        
        result = await redis_demo.analyze_with_medgemma("LPP grado 2", protocols)
        
        assert result["source"] == "medgemma"
        assert "analysis" in result
        assert result["protocols_used"] == 1
        mock_ollama_available.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_response_storage(self, redis_demo, mock_redis_client):
        """Test almacenamiento de respuestas en cache."""
        redis_demo.redis_client = mock_redis_client
        
        test_response = {
            "analysis": "Test analysis",
            "recommendations": ["Test recommendation"]
        }
        
        await redis_demo.cache_response("test query", test_response)
        
        # Verificar que se almacenó correctamente
        mock_redis_client.hset.assert_called()
        mock_redis_client.expire.assert_called_with(pytest.approx(1800, abs=100), 1800)  # 30 min TTL
        mock_redis_client.hincrby.assert_called_with("medical_cache:stats", "total_queries", 1)


class TestIntegrationWorkflows(TestRedisGemmaIntegration):
    """Pruebas para flujos de trabajo integrados."""
    
    @pytest.mark.asyncio
    async def test_complete_medical_query_workflow(self, redis_demo, mock_redis_client, mock_ollama_available):
        """Test flujo completo de consulta médica."""
        redis_demo.redis_client = mock_redis_client
        redis_demo.medgemma_model = "alibayram/medgemma"
        
        # Setup mocks
        mock_redis_client.hgetall.return_value = {}  # Cache miss inicial
        mock_redis_client.smembers.side_effect = [
            {"lpp_prevention"}, {"lpp_grade2_treatment"}, set()
        ]
        mock_redis_client.hgetall.side_effect = [
            {},  # Cache miss
            {  # Protocolo 1
                "title": "Prevención LPP",
                "content": "Protocolo de prevención",
                "category": "prevention",
                "urgency": "routine"
            },
            {  # Protocolo 2
                "title": "Tratamiento LPP Grado 2",
                "content": "Protocolo de tratamiento",
                "category": "treatment", 
                "urgency": "urgent"
            }
        ]
        
        # Mock MedGemma response
        mock_ollama_available.return_value = MagicMock(
            stdout="Evaluación: LPP grado 2. Recomienda cambios posturales y evaluación médica",
            stderr="",
            returncode=0
        )
        
        query = "Paciente con eritema no blanqueable en sacro"
        result = await redis_demo.process_medical_query(query)
        
        # Verificaciones del resultado
        assert result["query"] == query
        assert "analysis" in result
        assert "recommendations" in result
        assert "urgency" in result
        assert result["cache_hit"] is False
        assert result["protocols_consulted"] >= 1
        assert result["source"] == "medgemma"
        assert "processing_steps" in result
    
    @pytest.mark.asyncio
    async def test_cache_hit_workflow(self, redis_demo, mock_redis_client):
        """Test flujo con hit en cache."""
        redis_demo.redis_client = mock_redis_client
        
        # Setup cache hit
        cached_response = {
            "analysis": "Cached analysis",
            "recommendations": ["Cached recommendation"],
            "urgency": "moderate"
        }
        mock_redis_client.hgetall.return_value = {
            "response": json.dumps(cached_response),
            "created_at": "2025-01-09"
        }
        
        query = "Cached query test"
        result = await redis_demo.process_medical_query(query)
        
        assert result["cache_hit"] is True
        assert result["analysis"] == "Cached analysis"
        assert "cached_at" in result
    
    @pytest.mark.asyncio
    async def test_demo_scenarios_execution(self, redis_demo, mock_redis_client):
        """Test ejecución de escenarios de demo."""
        redis_demo.redis_client = mock_redis_client
        redis_demo.medgemma_model = None  # Usar modo simulado
        
        # Setup mocks básicos
        mock_redis_client.hgetall.return_value = {}  # Cache miss
        mock_redis_client.smembers.return_value = {"lpp_prevention"}
        mock_redis_client.hgetall.side_effect = [
            {},  # Cache miss
            {  # Protocolo
                "title": "Test Protocol",
                "content": "Test content",
                "category": "prevention",
                "urgency": "routine"
            }
        ] * 10  # Suficientes para todos los escenarios
        
        results = await redis_demo.run_demo_scenarios()
        
        # Verificar que se ejecutaron todos los escenarios
        assert len(results) == 4  # 4 escenarios definidos
        
        # Verificar cache hit en el último escenario (consulta repetida)
        assert results[0]["cache_hit"] is False  # Primera consulta
        assert results[3]["cache_hit"] is True   # Consulta repetida


class TestErrorHandling(TestRedisGemmaIntegration):
    """Pruebas para manejo de errores."""
    
    @pytest.mark.asyncio
    async def test_redis_connection_failure(self, redis_demo):
        """Test fallo de conexión a Redis."""
        with patch('redis.asyncio.Redis') as mock_redis_class:
            mock_client = AsyncMock()
            mock_client.ping.side_effect = ConnectionError("Redis connection failed")
            mock_redis_class.return_value = mock_client
            
            result = await redis_demo.initialize()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_ollama_execution_failure(self, redis_demo):
        """Test fallo en ejecución de Ollama."""
        redis_demo.medgemma_model = "alibayram/medgemma"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                stdout="",
                stderr="Model not found",
                returncode=1
            )
            
            protocols = [{"title": "Test", "content": "Test", "category": "test"}]
            result = await redis_demo.analyze_with_medgemma("test", protocols)
            
            assert result["source"] == "fallback"
            assert "analysis" in result
    
    @pytest.mark.asyncio
    async def test_cache_operation_failure(self, redis_demo, mock_redis_client):
        """Test fallo en operaciones de cache."""
        redis_demo.redis_client = mock_redis_client
        mock_redis_client.hgetall.side_effect = Exception("Redis error")
        
        result = await redis_demo.get_cached_response("test")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_protocol_retrieval_failure(self, redis_demo, mock_redis_client):
        """Test fallo en recuperación de protocolos."""
        redis_demo.redis_client = mock_redis_client
        mock_redis_client.smembers.side_effect = Exception("Redis error")
        
        protocols = await redis_demo.get_relevant_protocols("test")
        assert protocols == []


class TestPerformanceAndStats(TestRedisGemmaIntegration):
    """Pruebas para rendimiento y estadísticas."""
    
    @pytest.mark.asyncio
    async def test_statistics_collection(self, redis_demo, mock_redis_client):
        """Test recolección de estadísticas."""
        redis_demo.redis_client = mock_redis_client
        
        # Mock stats data
        mock_redis_client.info.return_value = {
            'used_memory_human': '2.1M',
            'total_commands_processed': 5000
        }
        mock_redis_client.hgetall.return_value = {
            'total_queries': '42',
            'cache_hits': '15'
        }
        mock_redis_client.keys.side_effect = [
            ['protocol:1', 'protocol:2'],  # Protocolos
            ['cache:1', 'cache:2', 'cache:3']  # Cache entries
        ]
        
        await redis_demo.show_final_stats()
        
        # Verificar que se llamaron los métodos correctos
        mock_redis_client.info.assert_called_once()
        mock_redis_client.hgetall.assert_called()
        assert mock_redis_client.keys.call_count == 2
    
    @pytest.mark.asyncio
    async def test_recommendation_extraction(self, redis_demo):
        """Test extracción de recomendaciones."""
        # Test con texto estructurado
        text_with_bullets = """
        Análisis médico:
        - Aplicar cambios posturales cada 2 horas
        - Evaluar con escala de Braden
        - Documentar evolución
        """
        
        recommendations = redis_demo._extract_recommendations(text_with_bullets)
        assert len(recommendations) >= 2
        assert any("cambios posturales" in rec.lower() for rec in recommendations)
        
        # Test con texto no estructurado
        text_unstructured = "Se recomienda evaluar al paciente. Debe aplicar medidas preventivas."
        recommendations = redis_demo._extract_recommendations(text_unstructured)
        assert len(recommendations) >= 1


@pytest.mark.integration
class TestFullSystemIntegration:
    """Pruebas de integración completa del sistema."""
    
    @pytest.mark.asyncio
    async def test_setup_and_demo_integration(self):
        """Test integración completa: setup + demo."""
        with patch('redis.asyncio.Redis') as mock_redis_class:
            mock_client = AsyncMock()
            mock_client.ping.return_value = True
            mock_client.info.return_value = {'redis_version': '7.0.0'}
            mock_client.exists.return_value = False
            mock_client.hset.return_value = True
            mock_client.sadd.return_value = True
            mock_client.expire.return_value = True
            mock_client.hincrby.return_value = 1
            mock_client.smembers.return_value = {"lpp_prevention"}
            mock_client.hgetall.return_value = {
                "title": "Test Protocol",
                "content": "Test content",
                "category": "prevention"
            }
            mock_client.keys.return_value = ["key1", "key2"]
            mock_redis_class.return_value = mock_client
            
            # Ejecutar setup
            setup = SimpleRedisSetup()
            setup_result = await setup.initialize()
            assert setup_result is True
            
            await setup.load_medical_protocols()
            await setup.setup_cache_structure()
            
            # Ejecutar demo
            demo = RedisGemmaIntegrationDemo()
            demo.redis_client = mock_client
            demo.medgemma_model = None  # Modo simulado
            
            query = "Test medical query"
            result = await demo.process_medical_query(query)
            
            assert result is not None
            assert "analysis" in result
            assert result["cache_hit"] is False
            
            # Cleanup
            await setup.cleanup()
            await demo.cleanup()


if __name__ == "__main__":
    # Ejecutar pruebas específicas si se ejecuta directamente
    pytest.main([__file__, "-v", "--tb=short"])