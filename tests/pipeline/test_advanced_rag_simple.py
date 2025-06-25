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

# Agregar vigia_detect al path
sys.path.insert(0, str(Path(__file__).parent))


        
    except Exception as e:
        print(f"❌ Error en clustering básico: {e}")
        return False


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
        return True
        
    except Exception as e:
        print(f"❌ Error en explainability básico: {e}")
        return False


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
        return True
        
    except Exception as e:
        print(f"❌ Error en MedCLIP básico: {e}")
        return False


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
        return True
        
    except Exception as e:
        print(f"❌ Error en RAG integration básico: {e}")
        return False


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
        return True
        
    except Exception as e:
        print(f"❌ Error en funcionalidad asíncrona: {e}")
        return False


def run_basic_rag_tests():
    """Ejecutar todas las pruebas básicas de componentes RAG."""
    print("🧪 Iniciando pruebas básicas de componentes RAG avanzados...\n")
    
    results = []
    
    # Pruebas síncronas
    results.append(test_incremental_training_basic())
    results.append(test_clustering_basic())
    results.append(test_explainability_basic())
    results.append(test_medclip_basic())
    results.append(test_advanced_rag_integration_basic())
    
    return results


async def run_async_tests():
    """Ejecutar pruebas asíncronas."""
    print("\n⚡ Ejecutando pruebas asíncronas...")
    result = await test_async_functionality()
    return [result]


def main():
    """Función principal."""
    # Pruebas síncronas
    sync_results = run_basic_rag_tests()
    
    # Pruebas asíncronas
    async_results = asyncio.run(run_async_tests())
    
    # Combinar resultados
    all_results = sync_results + async_results
    
    # Resumen de resultados
    print("\n" + "="*60)
    print("📋 RESUMEN DE PRUEBAS RAG BÁSICAS")
    print("="*60)
    
    passed = sum(all_results)
    total = len(all_results)
    
    print(f"✅ Pruebas exitosas: {passed}/{total}")
    print(f"❌ Pruebas fallidas: {total - passed}/{total}")
    print(f"📊 Tasa de éxito: {(passed/total)*100:.1f}%")
    
    component_status = {
        "Incremental Training": sync_results[0],
        "Dynamic Clustering": sync_results[1], 
        "Medical Explainability": sync_results[2],
        "MedCLIP Multimodal": sync_results[3],
        "Advanced RAG Integration": sync_results[4],
        "Async Functionality": async_results[0]
    }
    
    print("\n📊 Estado por componente:")
    for component, status in component_status.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {component}")
    
    if passed == total:
        print("\n🎉 ¡Todas las pruebas básicas RAG pasaron exitosamente!")
        print("🚀 Componentes core implementados correctamente")
        print("💡 Sistema listo para pruebas de integración completa")
    else:
        print(f"\n⚠️ {total - passed} pruebas fallaron - revisar implementación")
        print("🔧 Algunos componentes necesitan ajustes")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)