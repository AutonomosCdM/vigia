"""
Fixtures compartidas para todos los tests del proyecto Vigía.
Centraliza la configuración de tests y elimina duplicación.
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import numpy as np
from PIL import Image
from datetime import datetime

# Agregar el proyecto al path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


# ==================== FIXTURES DE CONFIGURACIÓN ====================

@pytest.fixture(scope="session")
def test_env_vars():
    """Variables de entorno para tests"""
    return {
        'SUPABASE_URL': 'https://test.supabase.co',
        'SUPABASE_KEY': 'test-key-123',
        'TWILIO_ACCOUNT_SID': 'ACtest123',
        'TWILIO_AUTH_TOKEN': 'test-token-456',
        'TWILIO_WHATSAPP_FROM': 'whatsapp:+14155238886',
        'SLACK_BOT_TOKEN': 'xoxb-test-token',
        'SLACK_SIGNING_SECRET': 'test-signing-secret',
        'REDIS_HOST': 'localhost',
        'REDIS_PORT': '6379',
        'ENVIRONMENT': 'test'
    }


@pytest.fixture(autouse=True)
def setup_test_env(test_env_vars, monkeypatch):
    """Configura variables de entorno para todos los tests"""
    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def temp_dir():
    """Directorio temporal para tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ==================== CONSTANTES DE TESTS ====================

# Test data constants from shared_fixtures
SAMPLE_PATIENT_CODES = [
    "CD-2025-001",
    "AB-2024-999", 
    "XY-2025-123"
]

SAMPLE_IMAGE_METADATA = {
    "width": 1920,
    "height": 1080,
    "channels": 3,
    "format": "JPEG"
}

SAMPLE_DETECTION_RESULTS = {
    "detections": [
        {
            "bbox": [100, 100, 200, 200],
            "confidence": 0.85,
            "grade": 2,
            "location": "sacro"
        }
    ],
    "confidence_scores": [0.85],
    "processing_time": 1.23
}

# ==================== FIXTURES DE DATOS ====================

@pytest.fixture
def sample_patient_data():
    """Datos de paciente de ejemplo"""
    return {
        'patient_code': 'TC-2025-001',
        'name': 'Test Case',
        'age': 65,
        'service': 'Test Service',
        'bed': '101-A',
        'diagnoses': ['Test diagnosis 1', 'Test diagnosis 2'],
        'medications': ['Test med 1', 'Test med 2'],
        'risk_score': 15
    }


@pytest.fixture
def sample_detection_result():
    """Resultado de detección de ejemplo"""
    return {
        'detections': [
            {
                'class': 2,
                'confidence': 0.92,
                'bbox': [100, 100, 200, 200],
                'location': 'Sacro'
            }
        ],
        'inference_time': 0.123,
        'preprocessing_time': 0.045,
        'total_time': 0.168,
        'max_severity': 2
    }


@pytest.fixture
def sample_whatsapp_message():
    """Mensaje de WhatsApp de ejemplo"""
    return {
        'From': 'whatsapp:+56912345678',
        'To': 'whatsapp:+14155238886',
        'Body': 'Hola, envío foto del paciente César Durán',
        'MessageSid': 'SMtest123',
        'AccountSid': 'ACtest123',
        'NumMedia': '1',
        'MediaUrl0': 'https://api.twilio.com/test-image.jpg',
        'MediaContentType0': 'image/jpeg'
    }


@pytest.fixture
def sample_slack_event():
    """Evento de Slack de ejemplo"""
    return {
        'type': 'block_actions',
        'user': {'id': 'U123456', 'name': 'test_user'},
        'channel': {'id': 'C123456', 'name': 'test_channel'},
        'trigger_id': 'test_trigger_123',
        'actions': [{
            'action_id': 'ver_historial_medico',
            'block_id': 'block_123',
            'value': 'CD-2025-001',
            'type': 'button'
        }]
    }


@pytest.fixture
def sample_patient_code():
    """Provide a sample patient code"""
    return SAMPLE_PATIENT_CODES[0]


@pytest.fixture
def invalid_patient_codes():
    """Provide invalid patient codes for testing"""
    return [
        "",
        "INVALID",
        "CD-25-001",  # Wrong year format
        "C-2025-001",  # Wrong prefix format
        "CD-2025-1",   # Wrong number format
        "CD-2025-ABCD"  # Non-numeric number
    ]


@pytest.fixture
def sample_detection_payload():
    """Sample detection payload for testing"""
    return {
        "patient_code": SAMPLE_PATIENT_CODES[0],
        "image_path": "/test/path/image.jpg",
        "detection_results": SAMPLE_DETECTION_RESULTS,
        "timestamp": datetime.now().isoformat(),
        "processing_id": "test-123"
    }


@pytest.fixture
def mock_detection_result():
    """Mock detection result for testing"""
    return {
        'success': True,
        'detection_result': {
            'detections': [
                {
                    'class': 'lpp_grade_2',
                    'confidence': 0.85,
                    'bbox': [100, 100, 200, 200],
                    'area': 10000
                }
            ],
            'processing_time': 0.5
        },
        'medical_assessment': {
            'lpp_grade': 2,
            'severity_level': 'IMPORTANTE',
            'recommendations': ['Curación según protocolo'],
            'confidence_score': 0.85
        },
        'patient_code': 'CD-2025-001'
    }


# ==================== FIXTURES DE IMÁGENES ====================

@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing (from shared_fixtures)"""
    import shutil
    temp_dir = tempfile.mkdtemp()
    try:
        yield Path(temp_dir)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def sample_image(temp_dir):
    """Crea una imagen de prueba"""
    # Crear imagen RGB de 640x480
    img = Image.new('RGB', (640, 480), color='white')
    
    # Agregar un rectángulo rojo (simulando lesión)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([200, 150, 400, 300], fill='red')
    
    # Guardar imagen
    image_path = temp_dir / 'test_image.jpg'
    img.save(image_path)
    
    return str(image_path)


@pytest.fixture
def sample_image_path(temp_directory):
    """Create a sample image file for testing (from shared_fixtures)"""
    image_path = temp_directory / "sample_image.jpg"
    # Create a minimal valid image file (1x1 pixel)
    image_data = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
    
    with open(image_path, 'wb') as f:
        f.write(image_data)
    
    return image_path


@pytest.fixture
def sample_image_array():
    """Array numpy de imagen de prueba"""
    # Imagen RGB 640x480
    img = np.ones((480, 640, 3), dtype=np.uint8) * 255
    
    # Agregar región roja (simulando lesión)
    img[150:300, 200:400] = [255, 0, 0]
    
    return img


@pytest.fixture
def batch_images(temp_dir):
    """Crea múltiples imágenes de prueba"""
    images = []
    for i in range(5):
        img = Image.new('RGB', (640, 480), color='white')
        draw = ImageDraw.Draw(img)
        # Diferentes posiciones para cada imagen
        x = 100 + i * 50
        y = 100 + i * 30
        draw.rectangle([x, y, x+100, y+100], fill='red')
        
        image_path = temp_dir / f'test_image_{i}.jpg'
        img.save(image_path)
        images.append(str(image_path))
    
    return images


# ==================== MOCKS DE SERVICIOS ====================

@pytest.fixture
def mock_supabase_client():
    """Mock del cliente Supabase (enhanced version)"""
    client = MagicMock()
    
    # Mock de métodos comunes (enhanced from shared_fixtures)
    client.table.return_value.select.return_value.execute.return_value.data = [
        {"id": 1, "patient_code": "CD-2025-001"}
    ]
    client.table.return_value.insert.return_value.execute.return_value.data = [
        {'id': 'test-id-123', 'created_at': '2025-01-01T00:00:00'}
    ]
    
    return client


@pytest.fixture
def mock_twilio_client():
    """Mock del cliente Twilio"""
    client = MagicMock()
    
    # Mock de envío de mensaje
    message = MagicMock()
    message.sid = 'SMtest123'
    message.status = 'sent'
    client.messages.create.return_value = message
    
    return client


@pytest.fixture
def mock_slack_client():
    """Mock del cliente Slack (enhanced version)"""
    client = MagicMock()
    
    # Mock de métodos comunes (enhanced from shared_fixtures)
    client.chat_postMessage.return_value = {'ok': True, 'ts': '123.456'}
    client.views_open.return_value = {'ok': True}
    client.auth_test.return_value = {"ok": True, "user": "test_bot"}
    
    return client


@pytest.fixture
def mock_redis_client():
    """Mock del cliente Redis (enhanced version)"""
    client = MagicMock()
    
    # Mock de métodos comunes (enhanced from shared_fixtures)
    client.get.return_value = None
    client.set.return_value = True
    client.exists.return_value = False
    client.ping.return_value = True
    client.health_check.return_value = {
        "redis": True,
        "cache": True,
        "vector_search": True
    }
    
    return client


# ==================== FIXTURES DE MODELOS ====================

@pytest.fixture
def mock_yolo_model():
    """Mock del modelo YOLO"""
    model = MagicMock()
    
    # Mock de predicción
    result = MagicMock()
    result.xyxy = [torch.tensor([[100, 100, 200, 200, 0.92, 2]])]
    result.pandas.return_value.xyxy = [
        MagicMock(values=np.array([[100, 100, 200, 200, 0.92, 2]]))
    ]
    
    model.return_value = [result]
    
    return model


@pytest.fixture
def mock_detector():
    """Mock LPP detector for testing (from shared_fixtures)"""
    mock_detector = MagicMock()
    mock_detector.detect.return_value = SAMPLE_DETECTION_RESULTS
    mock_detector.confidence_threshold = 0.25
    return mock_detector


@pytest.fixture
def mock_preprocessor():
    """Mock image preprocessor for testing (from shared_fixtures)"""
    mock_preprocessor = MagicMock()
    mock_preprocessor.preprocess.return_value = "processed_image_data"
    mock_preprocessor.get_original_size.return_value = (1920, 1080)
    mock_preprocessor.get_applied_steps.return_value = ["resize", "normalize"]
    return mock_preprocessor


@pytest.fixture
def mock_webhook_client():
    """Mock webhook client for testing (from shared_fixtures)"""
    mock_client = MagicMock()
    mock_client.send_async.return_value = {
        "success": True,
        "webhook_id": "test-webhook-123",
        "status_code": 200
    }
    return mock_client


# ==================== FIXTURES DE CONTEXTO ====================

@pytest.fixture
def vigia_context(mock_supabase_client, mock_twilio_client, 
                  mock_slack_client, mock_redis_client):
    """Contexto completo para tests de integración"""
    return {
        'supabase': mock_supabase_client,
        'twilio': mock_twilio_client,
        'slack': mock_slack_client,
        'redis': mock_redis_client,
        'config': {
            'model_type': 'yolov5s',
            'confidence_threshold': 0.25,
            'environment': 'test'
        }
    }


# ==================== UTILIDADES ====================

@pytest.fixture
def capture_logs():
    """Captura logs durante tests"""
    import logging
    from io import StringIO
    
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    
    # Agregar handler a todos los loggers de vigia
    loggers = [
        logging.getLogger('vigia'),
        logging.getLogger('vigia-detect'),
        logging.getLogger('vigia.supabase'),
        logging.getLogger('vigia.twilio'),
        logging.getLogger('vigia.slack')
    ]
    
    for logger in loggers:
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    
    yield log_capture
    
    # Limpiar handlers
    for logger in loggers:
        logger.removeHandler(handler)


@pytest.fixture
def assert_detection_valid():
    """Helper para validar detecciones"""
    def _assert(detection):
        assert 'class' in detection
        assert 'confidence' in detection
        assert 'bbox' in detection
        assert len(detection['bbox']) == 4
        assert 0 <= detection['class'] <= 4
        assert 0 <= detection['confidence'] <= 1
    
    return _assert


@pytest.fixture
def sample_settings():
    """Sample settings for testing (from shared_fixtures)"""
    return {
        "environment": "test",
        "debug": True,
        "log_level": "DEBUG",
        "supabase_url": "https://test.supabase.co",
        "supabase_key": "test_key",
        "twilio_account_sid": "test_sid",
        "twilio_auth_token": "test_token",
        "slack_bot_token": "xoxb-test-token",
        "model_confidence": 0.25,
        "use_mock_yolo": True
    }


@pytest.fixture
def test_config_file(temp_directory):
    """Create a test configuration file (from shared_fixtures)"""
    import json
    config_data = {
        "test_setting": "test_value",
        "database": {
            "url": "test://localhost",
            "timeout": 30
        }
    }
    
    config_path = temp_directory / "test_config.json"
    with open(config_path, 'w') as f:
        json.dump(config_data, f)
    
    return config_path


@pytest.fixture
def mock_health_checker():
    """Mock health checker for testing (from shared_fixtures)"""
    mock_checker = MagicMock()
    mock_checker.check_services.return_value = {
        "database": {"status": "healthy", "response_time": 0.1},
        "redis": {"status": "healthy", "response_time": 0.05},
        "external_apis": {"status": "healthy", "response_time": 0.3}
    }
    return mock_checker


# ==================== CONFIGURACIÓN DE PYTEST ====================

def pytest_configure(config):
    """Configuración global de pytest"""
    # Agregar markers personalizados
    config.addinivalue_line(
        "markers", "integration: marca tests de integración"
    )
    config.addinivalue_line(
        "markers", "slow: marca tests lentos"
    )
    config.addinivalue_line(
        "markers", "requires_gpu: marca tests que requieren GPU"
    )


# ==================== DATA FACTORY ====================

class TestDataFactory:
    """Factory for creating test data objects (from shared_fixtures)"""
    
    @staticmethod
    def create_detection_result(grade: int = 2, confidence: float = 0.85):
        """Create a test detection result"""
        return {
            "bbox": [100, 100, 200, 200],
            "confidence": confidence,
            "grade": grade,
            "location": "sacro",
            "severity": "medium" if grade >= 2 else "low"
        }
    
    @staticmethod
    def create_patient_data(patient_code: str = None):
        """Create test patient data"""
        return {
            "patient_code": patient_code or SAMPLE_PATIENT_CODES[0],
            "age": 65,
            "gender": "M",
            "admission_date": "2025-01-01",
            "room_number": "101"
        }
    
    @staticmethod
    def create_processing_result(success: bool = True, **kwargs):
        """Create test processing result"""
        base_result = {
            "success": success,
            "processing_id": "test-123",
            "timestamp": datetime.now().isoformat(),
            "processor_version": "test_v1.0"
        }
        
        if success:
            base_result.update({
                "results": SAMPLE_DETECTION_RESULTS,
                "processing_time_seconds": 1.23
            })
        else:
            base_result.update({
                "error": kwargs.get("error", "Test error"),
                "error_code": kwargs.get("error_code", "TEST_ERROR")
            })
        
        base_result.update(kwargs)
        return base_result


@pytest.fixture
def test_data_factory():
    """Provide test data factory"""
    return TestDataFactory


# ==================== REDIS-SPECIFIC FIXTURES ====================

@pytest.fixture(scope="session")
def event_loop():
    """Fixture para event loop que persiste durante toda la sesión (for Redis tests)"""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Fixture para configuración mock (Redis specific)"""
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
    """Fixture con respuestas mock estándar para Redis"""
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
def mock_redis_client_enhanced(mock_redis_responses):
    """Fixture principal para cliente Redis mock con funcionalidad completa"""
    from unittest.mock import AsyncMock
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
def sample_medical_queries():
    """Fixture con consultas médicas de prueba para Redis tests"""
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
def redis_integration_config():
    """Fixture con configuración específica para pruebas de integración Redis"""
    return {
        'cache_ttl': 1800,  # 30 minutos para pruebas
        'similarity_threshold': 0.85,
        'max_protocols': 3,
        'max_recommendations': 5,
        'timeout_seconds': 30
    }


class RedisTestHelper:
    """Helper class para operaciones de testing Redis"""
    
    @staticmethod
    def create_cache_key(query: str) -> str:
        """Crear clave de cache consistente"""
        return f"medical_cache:query:{hash(query) % 100000}"
    
    @staticmethod
    def mock_cached_response(query: str, analysis: str, recommendations: list) -> dict:
        """Crear respuesta mock para cache"""
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
        """Validar estructura de respuesta médica"""
        required_fields = ["analysis", "recommendations", "urgency", "confidence", "source"]
        return all(field in response for field in required_fields)
    
    @staticmethod
    def extract_urgency_level(text: str) -> str:
        """Extraer nivel de urgencia del texto"""
        text_lower = text.lower()
        if any(word in text_lower for word in ["urgente", "emergencia", "inmediato"]):
            return "urgent"
        elif any(word in text_lower for word in ["moderado", "pronto"]):
            return "moderate"
        else:
            return "routine"


@pytest.fixture
def redis_test_helper():
    """Fixture para helper de testing Redis"""
    return RedisTestHelper


# ==================== VALIDATION UTILITIES ====================

def assert_valid_patient_code(patient_code: str) -> None:
    """Assert that a patient code is valid (from shared_fixtures)"""
    parts = patient_code.split('-')
    assert len(parts) == 3, f"Invalid patient code format: {patient_code}"
    assert len(parts[0]) == 2 and parts[0].isalpha(), "Invalid prefix"
    assert len(parts[1]) == 4 and parts[1].isdigit(), "Invalid year"
    assert len(parts[2]) == 3 and parts[2].isdigit(), "Invalid number"


def assert_detection_result_structure(result) -> None:
    """Assert that a detection result has the expected structure (from shared_fixtures)"""
    required_fields = ["bbox", "confidence", "grade"]
    for field in required_fields:
        assert field in result, f"Missing required field: {field}"
    
    assert isinstance(result["bbox"], list), "bbox must be a list"
    assert len(result["bbox"]) == 4, "bbox must have 4 coordinates"
    assert 0 <= result["confidence"] <= 1, "confidence must be between 0 and 1"
    assert isinstance(result["grade"], int), "grade must be an integer"
    assert 0 <= result["grade"] <= 4, "grade must be between 0 and 4"


# Importar torch solo si está disponible (para el mock de YOLO)
try:
    import torch
except ImportError:
    torch = None


# ==================== EJEMPLOS DE USO ====================
"""
Ejemplos de cómo usar estas fixtures en tests:

def test_process_image(sample_image, mock_yolo_model):
    # Test con imagen y modelo mockeado
    processor = ImageProcessor()
    result = processor.process_image(sample_image)
    assert result['success'] is True

def test_save_detection(sample_detection_result, mock_supabase_client):
    # Test guardando en BD mockeada
    client = SupabaseClient()
    client.client = mock_supabase_client
    result = client.save_detection('patient-123', sample_detection_result)
    assert result is not None

def test_integration(vigia_context, sample_image):
    # Test de integración con contexto completo
    # Todos los servicios externos están mockeados
    pass

# Fixture usage from consolidated shared_fixtures:
def test_patient_code_validation(sample_patient_code, invalid_patient_codes):
    # Valid code should pass
    assert_valid_patient_code(sample_patient_code)
    
    # Invalid codes should fail
    for invalid_code in invalid_patient_codes:
        with pytest.raises(AssertionError):
            assert_valid_patient_code(invalid_code)

def test_detection_structure(test_data_factory):
    # Create test detection
    detection = test_data_factory.create_detection_result(grade=3, confidence=0.9)
    assert_detection_result_structure(detection)
"""