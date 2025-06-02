#!/usr/bin/env python3
"""Migration script for Redis Phase 2 implementation."""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set PYTHONPATH if not set
if 'PYTHONPATH' not in os.environ:
    os.environ['PYTHONPATH'] = str(project_root)

from vigia_detect.redis_layer import create_redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_to_phase2():
    """Migrate Redis implementation to Phase 2."""
    logger.info("Starting Redis Phase 2 migration...")
    
    try:
        # Initialize new client
        client = create_redis_client()
        
        # Check health
        health = client.health_check()
        logger.info(f"Health check: {health}")
        
        # Index medical protocols
        docs_dir = project_root / "docs" / "papers"
        if docs_dir.exists():
            logger.info(f"Indexing protocols from {docs_dir}")
            client.index_protocols_from_docs(str(docs_dir))
        else:
            logger.warning(f"Docs directory not found: {docs_dir}")
            
        # Add some example protocols
        example_protocols = [
            {
                "id": "lpp_prevention_001",
                "title": "Protocolo de Prevención de LPP",
                "content": """
                Las lesiones por presión (LPP) son áreas de daño localizado en la piel y tejidos subyacentes,
                generalmente sobre una prominencia ósea. La prevención incluye:
                1. Cambios posturales cada 2 horas
                2. Uso de superficies especiales de apoyo
                3. Evaluación regular del riesgo con escala de Braden
                4. Mantener la piel limpia y seca
                5. Nutrición e hidratación adecuadas
                """,
                "tags": ["prevention", "care", "assessment"],
                "lpp_grades": ["grade_0", "grade_1"],
                "source": "MINSAL Chile"
            },
            {
                "id": "lpp_treatment_grade2",
                "title": "Tratamiento LPP Grado 2",
                "content": """
                El tratamiento de LPP grado 2 (pérdida parcial del espesor de la piel) incluye:
                1. Limpieza con suero fisiológico
                2. Aplicación de apósito hidrocoloide o espuma
                3. Protección de la zona afectada
                4. Cambios de apósito según fabricante (3-7 días)
                5. Monitoreo de signos de infección
                6. Continuación de medidas preventivas
                """,
                "tags": ["treatment", "care"],
                "lpp_grades": ["grade_2"],
                "source": "Protocolo EPUAP/NPUAP"
            },
            {
                "id": "lpp_treatment_grade3",
                "title": "Tratamiento LPP Grado 3",
                "content": """
                El tratamiento de LPP grado 3 (pérdida total del espesor de la piel) requiere:
                1. Evaluación por equipo multidisciplinario
                2. Desbridamiento del tejido necrótico si es necesario
                3. Control de la carga bacteriana
                4. Uso de apósitos avanzados (alginatos, hidrogeles)
                5. Consideración de terapia de presión negativa
                6. Optimización nutricional con suplementos proteicos
                """,
                "tags": ["treatment", "care"],
                "lpp_grades": ["grade_3"],
                "source": "Guía Clínica MINSAL"
            }
        ]
        
        logger.info("Indexing example protocols...")
        for protocol in example_protocols:
            client.index_custom_protocol(protocol)
            
        # Get stats
        stats = client.get_protocol_index_stats()
        logger.info(f"Protocol index stats: {stats}")
        
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    migrate_to_phase2()