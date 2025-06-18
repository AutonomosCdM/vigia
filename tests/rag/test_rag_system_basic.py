#!/usr/bin/env python3
"""
Pruebas Simplificadas para Componentes RAG Avanzados
===================================================

Suite de pruebas básicas para validar la funcionalidad core de los componentes RAG
sin dependencias externas complejas.
"""

import asyncio
import numpy as np
from datetime import datetime
import sys
import os
from pathlib import Path
import pytest

# Agregar vigia_detect al path
sys.path.insert(0, str(Path(__file__).parent))


def test_incremental_training_basic():
    """Test básico del pipeline de entrenamiento incremental."""
    try:
        print("🎯 Probando Incremental Training Pipeline (básico)...")
        
        # Importar y crear instancia básica
        from vigia_detect.rag.incremental_training_pipeline import (
            IncrementalTrainingPipeline, TrainingDataType, ValidationStatus, MedicalTrainingData
        )
        
        # Test creación de instancia
        pipeline = IncrementalTrainingPipeline(min_batch_size=2)
        assert pipeline.min_batch_size == 2
        assert pipeline.validation_threshold == 0.8
        
        # Test creación de datos de entrenamiento
        training_data = MedicalTrainingData(
            data_id="test_001",
            data_type=TrainingDataType.QUERY_RESPONSE_PAIR,
            query_text="Paciente con LPP grado 2",
            target_text="Protocolo de cuidados estándar",
            similarity_score=None,
            medical_classification=None,
            patient_outcome=None,
            validation_status=ValidationStatus.PENDING,
            medical_context={'lpp_grade': 2},
            created_at=datetime.now(),
            validated_at=None,
            validator_id=None
        )
        
        assert training_data.data_id == "test_001"
        assert training_data.data_type == TrainingDataType.QUERY_RESPONSE_PAIR
        
        print("✅ Incremental Training Pipeline básico funcionando")
        
    except Exception as e:
        print(f"❌ Error en incremental training básico: {e}")
        pytest.fail(f"Incremental training basic test failed: {e}")


def test_clustering_basic():
    """Test básico del servicio de clustering dinámico."""
    try:
        print("🔍 Probando Dynamic Clustering Service (básico)...")
        
        # Importar clases básicas
        from vigia_detect.rag.dynamic_clustering_service import (
            DynamicMedicalClusteringService, ClusterType, MedicalQuery
        )
        
        # Test creación de instancia (modo básico)
        service = DynamicMedicalClusteringService(min_cluster_size=2)
        assert service.min_cluster_size == 2
        assert service.similarity_threshold == 0.8
        
        # Test creación de consulta médica
        medical_query = MedicalQuery(
            query_id="query_001",
            query_text="Úlcera por presión en talón",
            lpp_grade=2,
            anatomical_location="talon",
            patient_context={'age': 70},
            timestamp=datetime.now(),
            jurisdiction="chile",
            embedding=np.random.rand(768),
            cluster_id=None
        )
        
        assert medical_query.query_id == "query_001"
        assert medical_query.lpp_grade == 2
        
        # Test tipos de cluster
        assert ClusterType.SIMILAR_SYMPTOMS.value == "similar_symptoms"
        assert ClusterType.TREATMENT_PATTERNS.value == "treatment_patterns"
        
        print("✅ Dynamic Clustering Service básico funcionando")
        
    except Exception as e:
        print(f"❌ Error en clustering básico: {e}")
        pytest.fail(f"Dynamic clustering basic test failed: {e}")


def test_explainability_basic():
    """Test básico del servicio de explicabilidad médica."""
    try:
        print("💡 Probando Medical Explainability Service (básico)...")
        
        # Importar clases básicas
        from vigia_detect.rag.medical_explainability_service import (
            MedicalExplainabilityService, ExplanationType, EvidenceLevel, EvidenceSource
        )
        
        # Test creación de fuente de evidencia
        evidence_source = EvidenceSource(
            source_id="source_001",
            source_type="clinical_guideline",
            title="Guía NPUAP 2019",
            content="Protocolo para LPP grado 2",
            evidence_level=EvidenceLevel.LEVEL_A,
            confidence_score=0.9,
            relevance_score=0.85,
            publication_date=datetime.now(),
            medical_specialty="wound_care",
            jurisdiction="international",
            keywords=["LPP", "pressure", "injury"]
        )
        
        assert evidence_source.source_id == "source_001"
        assert evidence_source.evidence_level == EvidenceLevel.LEVEL_A
        
        # Test tipos de explicación
        assert ExplanationType.SOURCE_ATTRIBUTION.value == "source_attribution"
        assert ExplanationType.SIMILARITY_ANALYSIS.value == "similarity_analysis"
        
        print("✅ Medical Explainability Service básico funcionando")
        
    except Exception as e:
        print(f"❌ Error en explainability básico: {e}")
        pytest.fail(f"Medical explainability basic test failed: {e}")


def test_medclip_basic():
    """Test básico del servicio multimodal MedCLIP."""
    try:
        print("📊 Probando MedCLIP Multimodal Service (básico)...")
        
        # Importar clase básica
        from vigia_detect.rag.multimodal_medclip_service import MedCLIPMultimodalService
        
        # Test creación de instancia
        service = MedCLIPMultimodalService()
        assert service.embedding_dimension == 768
        assert service.device is not None
        
        # Test conceptos médicos
        medical_concepts = service._load_medical_concepts()
        assert 'lpp' in medical_concepts
        assert 'wound' in medical_concepts
        
        # Test enhancement de texto médico
        enhanced_text = service._enhance_medical_text(
            "Paciente con úlcera",
            {'lpp_grade': 2, 'anatomical_location': 'sacro'}
        )
        assert "Grado 2" in enhanced_text
        assert "sacro" in enhanced_text
        
        print("✅ MedCLIP Multimodal Service básico funcionando")
        
    except Exception as e:
        print(f"❌ Error en MedCLIP básico: {e}")
        pytest.fail(f"MedCLIP basic test failed: {e}")


def test_advanced_rag_integration_basic():
    """Test básico de la integración RAG avanzada."""
    try:
        print("🚀 Probando Advanced RAG Integration (básico)...")
        
        # Importar clase básica
        from vigia_detect.rag.advanced_rag_integration import AdvancedRAGOrchestrator
        
        # Test creación de instancia
        orchestrator = AdvancedRAGOrchestrator()
        assert not orchestrator.is_initialized
        assert len(orchestrator.capabilities) == 4
        
        # Test capacidades esperadas
        expected_capabilities = [
            'multimodal_search',
            'dynamic_clustering', 
            'incremental_learning',
            'explainable_recommendations'
        ]
        
        for capability in expected_capabilities:
            assert capability in orchestrator.capabilities
        
        # Test métricas iniciales
        assert orchestrator.metrics['total_queries_processed'] == 0
        assert orchestrator.metrics['multimodal_queries'] == 0
        
        print("✅ Advanced RAG Integration básico funcionando")
        
    except Exception as e:
        print(f"❌ Error en RAG integration básico: {e}")
        pytest.fail(f"RAG integration basic test failed: {e}")


async def test_async_functionality():
    """Test funcionalidad asíncrona básica."""
    try:
        print("⚡ Probando funcionalidad asíncrona...")
        
        # Test función factory asíncrona
        from vigia_detect.rag.advanced_rag_integration import create_advanced_rag_orchestrator, AdvancedRAGOrchestrator
        
        # Crear orquestador (sin inicialización completa)
        orchestrator = AdvancedRAGOrchestrator()
        
        # Test método asíncrono básico
        status = await orchestrator.get_orchestrator_status()
        assert isinstance(status, dict)
        assert 'is_initialized' in status
        
        print("✅ Funcionalidad asíncrona básica funcionando")
        
    except Exception as e:
        print(f"❌ Error en funcionalidad asíncrona: {e}")
        pytest.fail(f"Async functionality test failed: {e}")


def run_basic_rag_tests():
    """Ejecutar todas las pruebas básicas de componentes RAG."""
    print("🧪 Iniciando pruebas básicas de componentes RAG avanzados...\n")
    
    # Pruebas síncronas - now they use assertions instead of returning values
    test_incremental_training_basic()
    test_clustering_basic()
    test_explainability_basic()
    test_medclip_basic()
    test_advanced_rag_integration_basic()
    
    print("All basic RAG tests completed successfully")


async def run_async_tests():
    """Ejecutar pruebas asíncronas."""
    print("\n⚡ Ejecutando pruebas asíncronas...")
    await test_async_functionality()
    print("Async tests completed successfully")


def main():
    """Función principal."""
    try:
        # Pruebas síncronas
        run_basic_rag_tests()
        
        # Pruebas asíncronas
        asyncio.run(run_async_tests())
        
        # Resumen de resultados
        print("\n" + "="*60)
        print("📋 RESUMEN DE PRUEBAS RAG BÁSICAS")
        print("="*60)
        print("✅ Todas las pruebas RAG básicas pasaron exitosamente!")
        print("🚀 Componentes core implementados correctamente")
        print("💡 Sistema listo para pruebas de integración completa")
        return True
        
    except Exception as e:
        print(f"\n⚠️ Error en pruebas RAG: {e}")
        print("🔧 Algunos componentes necesitan ajustes")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)