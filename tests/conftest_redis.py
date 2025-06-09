#!/usr/bin/env python3
"""
Configuración de pytest específica para pruebas Redis + MedGemma
Fixtures compartidas y configuración para testing del módulo integrado.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, Generator
import redis.asyncio as redis
import sys

# Agregar path del proyecto
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import settings


@pytest.fixture(scope="session")
def event_loop():
    """Fixture para event loop que persiste durante toda la sesión."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Fixture para configuración mock."""
    mock_config = MagicMock()
    mock_config.redis_host = "localhost"
    mock_config.redis_port = 6379
    mock_config.redis_password = None
    mock_config.redis_ssl = False
    mock_config.redis_db = 0
    mock_config.redis_cache_ttl = 3600
    mock_config.redis_vector_index = "test_lpp_protocols"
    mock_config.redis_cache_index = "test_lpp_cache"
    mock_config.redis_vector_dim = 768
    return mock_config


@pytest.fixture
def mock_redis_responses():
    """Fixture con respuestas mock estándar para Redis."""
    return {
        'info': {
            'redis_version': '7.0.0',
            'redis_mode': 'standalone',
            'uptime_in_seconds': 3600,
            'used_memory_human': '1.5M',
            'connected_clients': 5,
            'total_commands_processed': 1000
        },
        'protocols': {
            'lpp_prevention': {
                'title': 'Protocolo de Prevención de LPP',
                'content': 'Evaluación de riesgo cada 8 horas con escala de Braden. Cambios posturales cada 2 horas.',
                'category': 'prevention',
                'urgency': 'routine',
                'created_at': '2025-01-09'
            },
            'lpp_grade2_treatment': {
                'title': 'Tratamiento de LPP Grado 2',
                'content': 'Limpieza con suero fisiológico. Aplicación de apósito apropiado. Seguimiento cada 24 horas.',
                'category': 'treatment',
                'urgency': 'urgent',
                'created_at': '2025-01-09'
            },
            'lpp_emergency': {
                'title': 'Protocolo de Emergencia LPP',
                'content': 'Signos de alarma: celulitis, fiebre, dolor intenso. Evaluación médica urgente.',
                'category': 'emergency',
                'urgency': 'emergency',
                'created_at': '2025-01-09'
            }
        },
        'cache_stats': {
            'total_queries': '25',
            'cache_hits': '10',
            'cache_misses': '15',
            'last_reset': '2025-01-09'
        }
    }


@pytest.fixture
def mock_redis_client(mock_redis_responses):
    """Fixture principal para cliente Redis mock."""
    client = AsyncMock()
    
    # Configurar respuestas básicas
    client.ping.return_value = True
    client.info.return_value = mock_redis_responses['info']
    client.aclose.return_value = None
    
    # Configurar operaciones de protocolos
    client.exists.return_value = False  # Por defecto no existen
    client.hset.return_value = True
    client.sadd.return_value = 1
    client.expire.return_value = True
    client.hincrby.return_value = 1
    
    # Configurar búsquedas de protocolos
    def mock_smembers(key: str):
        if "category:prevention" in key:
            return {"lpp_prevention"}
        elif "category:treatment" in key:
            return {"lpp_grade2_treatment"}
        elif "category:emergency" in key:
            return {"lpp_emergency"}
        else:
            return set()
    
    client.smembers.side_effect = mock_smembers
    
    # Configurar recuperación de datos de protocolos
    def mock_hgetall(key: str):
        if "medical_protocol:lpp_prevention" in key:
            return mock_redis_responses['protocols']['lpp_prevention']
        elif "medical_protocol:lpp_grade2_treatment" in key:
            return mock_redis_responses['protocols']['lpp_grade2_treatment']
        elif "medical_protocol:lpp_emergency" in key:
            return mock_redis_responses['protocols']['lpp_emergency']
        elif "medical_cache:stats" in key:
            return mock_redis_responses['cache_stats']
        elif "medical_cache:query:" in key:
            return {}  # Cache miss por defecto
        else:
            return {}
    
    client.hgetall.side_effect = mock_hgetall
    
    # Configurar conteo de claves
    def mock_keys(pattern: str):
        if "medical_protocol:" in pattern:
            return ['medical_protocol:lpp_prevention', 'medical_protocol:lpp_grade2_treatment']
        elif "medical_cache:query:" in pattern:
            return ['medical_cache:query:12345', 'medical_cache:query:67890']
        else:
            return []
    
    client.keys.side_effect = mock_keys
    
    return client


@pytest.fixture
def mock_ollama_success():
    """Fixture para Ollama funcionando correctamente."""
    def _mock_run(cmd, **kwargs):
        if cmd[0] == "ollama" and cmd[1] == "list":
            return MagicMock(
                stdout="alibayram/medgemma:latest\nother-model:latest",
                stderr="",
                returncode=0
            )
        elif cmd[0] == "ollama" and cmd[1] == "run":
            # Simular respuesta médica de MedGemma
            return MagicMock(
                stdout="""
                Análisis médico del caso:
                
                Basándome en los protocolos médicos consultados, esta presentación sugiere una lesión por presión grado 1-2.
                
                Recomendaciones específicas:
                1. Evaluación inmediata con escala de Braden
                2. Implementar cambios posturales cada 2 horas
                3. Aplicar superficie de redistribución de presión
                4. Documentar evolución cada 8 horas
                5. Considerar interconsulta si no mejora en 72 horas
                
                Nivel de urgencia: Moderado
                Seguimiento requerido: 24 horas
                """,
                stderr="",
                returncode=0
            )
        else:
            return MagicMock(stdout="", stderr="Command not found", returncode=1)
    
    with patch('subprocess.run', side_effect=_mock_run) as mock:
        yield mock


@pytest.fixture
def mock_ollama_unavailable():
    """Fixture para Ollama no disponible."""
    with patch('subprocess.run', side_effect=FileNotFoundError("ollama command not found")):
        yield


@pytest.fixture
def mock_ollama_model_not_found():
    """Fixture para modelo MedGemma no encontrado."""
    def _mock_run(cmd, **kwargs):
        if cmd[0] == "ollama" and cmd[1] == "list":
            return MagicMock(
                stdout="other-model:latest\nanother-model:latest",
                stderr="",
                returncode=0
            )
        else:
            return MagicMock(stdout="", stderr="Model not found", returncode=1)
    
    with patch('subprocess.run', side_effect=_mock_run) as mock:
        yield mock


@pytest.fixture
def temp_directory():
    """Fixture para directorio temporal."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_medical_queries():
    """Fixture con consultas médicas de prueba."""
    return [
        {
            'query': '¿Cómo prevenir lesiones por presión en paciente encamado?',
            'expected_category': 'prevention',
            'expected_urgency': 'routine'
        },
        {
            'query': 'Paciente de 75 años con eritema no blanqueable en sacro de 3x2 cm',
            'expected_category': 'treatment',
            'expected_urgency': 'urgent'
        },
        {
            'query': 'LPP con exudado purulento y fiebre, signos de celulitis perilesional',
            'expected_category': 'emergency',
            'expected_urgency': 'emergency'
        },
        {
            'query': '¿Qué nutrientes son importantes para la cicatrización de heridas?',
            'expected_category': 'nutrition',
            'expected_urgency': 'routine'
        }
    ]


@pytest.fixture
def sample_protocol_responses():
    """Fixture con respuestas esperadas de protocolos."""
    return {
        'prevention': {
            'protocols_found': 1,
            'urgency': 'routine',
            'recommendations_min': 3
        },
        'treatment': {
            'protocols_found': 1,
            'urgency': 'urgent',
            'recommendations_min': 4
        },
        'emergency': {
            'protocols_found': 1,
            'urgency': 'emergency',
            'recommendations_min': 3
        }
    }


@pytest.fixture
def redis_integration_config():
    """Fixture con configuración específica para pruebas de integración."""
    return {
        'cache_ttl': 1800,  # 30 minutos para pruebas
        'similarity_threshold': 0.85,
        'max_protocols': 3,
        'max_recommendations': 5,
        'timeout_seconds': 30
    }


class RedisTestHelper:
    """Helper class para operaciones de testing Redis."""
    
    @staticmethod
    def create_cache_key(query: str) -> str:
        """Crear clave de cache consistente."""
        return f"medical_cache:query:{hash(query) % 100000}"
    
    @staticmethod
    def mock_cached_response(query: str, analysis: str, recommendations: list) -> dict:
        """Crear respuesta mock para cache."""
        return {
            "query": query,
            "response": {
                "analysis": analysis,
                "recommendations": recommendations,
                "urgency": "moderate",
                "confidence": 0.9,
                "source": "cached"
            },
            "created_at": "2025-01-09"
        }
    
    @staticmethod
    def validate_medical_response(response: dict) -> bool:
        """Validar estructura de respuesta médica."""
        required_fields = ["analysis", "recommendations", "urgency", "confidence", "source"]
        return all(field in response for field in required_fields)
    
    @staticmethod
    def extract_urgency_level(text: str) -> str:
        """Extraer nivel de urgencia del texto."""
        text_lower = text.lower()
        if any(word in text_lower for word in ["urgente", "emergencia", "inmediato"]):
            return "urgent"
        elif any(word in text_lower for word in ["moderado", "pronto"]):
            return "moderate"
        else:
            return "routine"


@pytest.fixture
def redis_test_helper():
    """Fixture para helper de testing Redis."""
    return RedisTestHelper


# Marks para categorizar pruebas
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.redis = pytest.mark.redis
pytest.mark.medgemma = pytest.mark.medgemma
pytest.mark.slow = pytest.mark.slow