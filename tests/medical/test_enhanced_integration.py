"""
Tests para integración completa MINSAL en arquitectura Vigia
"""

import pytest
from vigia_detect.agents.enhanced_medical_agent_wrapper import EnhancedLPPMedicalAgent, create_medical_agent
from vigia_detect.core.enhanced_medical_dispatcher import EnhancedMedicalDispatcher, create_enhanced_dispatcher
from vigia_detect.rag.minsal_rag_enhancer import MINSALRAGEnhancer, enhance_minsal_decision_with_rag


class TestEnhancedMINSALIntegration:
    """Test suite para validar integración completa MINSAL en arquitectura"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.enhanced_agent = create_medical_agent(jurisdiction="chile", use_minsal=True)
        self.international_agent = create_medical_agent(jurisdiction="international", use_minsal=False)
        self.enhanced_dispatcher = create_enhanced_dispatcher(default_jurisdiction="chile")
        self.rag_enhancer = MINSALRAGEnhancer()
    
    def test_enhanced_agent_jurisdiction_selection(self):
        """Test selección automática de motor según jurisdicción"""
        # Agente chileno debe usar MINSAL
        chile_agent = create_medical_agent(jurisdiction="chile", use_minsal=True)
        assert chile_agent.jurisdiction == "chile"
        assert chile_agent.use_minsal is True
        assert chile_agent.decision_engine == "minsal"
        
        # Agente internacional debe usar motor base
        intl_agent = create_medical_agent(jurisdiction="international", use_minsal=False)
        assert intl_agent.jurisdiction == "international"
        assert intl_agent.use_minsal is False
        assert intl_agent.decision_engine == "international"
    
    def test_enhanced_agent_decision_routing(self):
        """Test enrutamiento de decisiones según agente"""
        # Simulación detección LPP Grado 2
        mock_detection = {
            'detections': [{
                'class': 'lpp_grade_2',
                'confidence': 0.8,
                'anatomical_location': 'sacrum'
            }]
        }
        
        patient_context = {
            'age': 75,
            'diabetes': True,
            'public_healthcare': True
        }
        
        # Test agente MINSAL
        minsal_result = self.enhanced_agent.analyze_lpp_image(
            image_path="test.jpg",
            patient_code="CH-2025-001",
            detection_result=mock_detection,
            patient_context=patient_context
        )
        
        assert minsal_result['success'] is True
        analysis = minsal_result['analysis']
        
        assert analysis['decision_engine'] == 'MINSAL_Enhanced'
        assert 'chilean_terminology' in analysis
        assert 'regulatory_compliance' in analysis
        assert analysis['jurisdiction'] == 'chile'
        
        # Verificar terminología chilena
        terminology = analysis['chilean_terminology']
        assert 'Lesiones Por Presión' in terminology.get('condition_name', '')
    
    def test_international_agent_fallback(self):
        """Test fallback a motor internacional"""
        mock_detection = {
            'detections': [{
                'class': 'lpp_grade_2',
                'confidence': 0.8,
                'anatomical_location': 'sacrum'
            }]
        }
        
        # Test agente internacional
        intl_result = self.international_agent.analyze_lpp_image(
            image_path="test.jpg",
            patient_code="US-2025-001",
            detection_result=mock_detection
        )
        
        assert intl_result['success'] is True
        analysis = intl_result['analysis']
        
        assert analysis['decision_engine'] == 'International_NPUAP_EPUAP'
        assert 'chilean_terminology' not in analysis
        assert analysis['jurisdiction'] == 'international'
    
    @pytest.mark.asyncio
    async def test_enhanced_dispatcher_jurisdiction_detection(self):
        """Test detección automática de jurisdicción"""
        # Mock input con indicadores chilenos
        class MockStandardizedInput:
            def __init__(self):
                self.patient_context = {
                    'healthcare_system': 'fonasa',
                    'institution': 'hospital_publico'
                }
                self.metadata = {
                    'language': 'spanish',
                    'country': 'chile'
                }
                self.medical_content = {
                    'description': 'Evaluación lesiones por presión paciente'
                }
        
        chile_input = MockStandardizedInput()
        detected_jurisdiction = self.enhanced_dispatcher._detect_jurisdiction(chile_input)
        
        assert detected_jurisdiction == "chile"
        
        # Mock input internacional
        class MockInternationalInput:
            def __init__(self):
                self.patient_context = {}
                self.metadata = {
                    'language': 'english',
                    'country': 'usa'
                }
                self.medical_content = {
                    'description': 'Pressure injury assessment patient'
                }
        
        intl_input = MockInternationalInput()
        detected_jurisdiction = self.enhanced_dispatcher._detect_jurisdiction(intl_input)
        
        assert detected_jurisdiction == "international"
    
    def test_rag_enhancer_minsal_protocols(self):
        """Test RAG enhancer para protocolos MINSAL"""
        patient_context = {
            'age': 80,
            'diabetes': True,
            'public_healthcare': True
        }
        
        enhanced_knowledge = self.rag_enhancer.enhance_clinical_decision(
            lpp_grade=2,
            patient_context=patient_context,
            clinical_query="tratamiento LPP grado 2 sacro"
        )
        
        assert 'minsal_protocols' in enhanced_knowledge
        assert 'contextual_recommendations' in enhanced_knowledge
        assert 'healthcare_adaptations' in enhanced_knowledge
        
        # Verificar adaptaciones específicas Chile
        adaptations = enhanced_knowledge['healthcare_adaptations']
        assert adaptations['system_type'] == 'mixed_public_private'
        assert len(adaptations['available_resources']) > 0
    
    def test_rag_contextual_recommendations(self):
        """Test recomendaciones contextuales población chilena"""
        elderly_diabetic_context = {
            'age': 85,
            'diabetes': True,
            'malnutrition': True,
            'public_healthcare': True
        }
        
        contextual_recs = self.rag_enhancer._get_contextual_recommendations(
            lpp_grade=3, patient_context=elderly_diabetic_context
        )
        
        assert len(contextual_recs) > 0
        
        # Verificar recomendaciones específicas detectadas
        contexts = [rec['context'] for rec in contextual_recs]
        assert 'elderly_chilean_population' in contexts
        assert 'diabetes_chilean_prevalence' in contexts
        assert 'public_healthcare_resources' in contexts
        
        # Verificar prioridades altas para factores críticos
        high_priority_recs = [rec for rec in contextual_recs if rec['priority'] == 'high']
        assert len(high_priority_recs) >= 2  # Edad + diabetes deben ser alta prioridad
    
    def test_healthcare_system_adaptations(self):
        """Test adaptaciones específicas sistema salud chileno"""
        public_patient_context = {
            'public_healthcare': True,
            'insurance': 'fonasa',
            'urban_access': False  # Paciente rural
        }
        
        adaptations = self.rag_enhancer._get_healthcare_system_adaptations(public_patient_context)
        
        assert adaptations['system_type'] == 'mixed_public_private'
        assert len(adaptations['available_resources']) > 0
        assert len(adaptations['referral_pathways']) > 0
        
        # Verificar recursos específicos sistema público
        resources = ' '.join(adaptations['available_resources']).lower()
        assert 'colchones' in resources or 'apósitos' in resources
        
        referrals = ' '.join(adaptations['referral_pathways']).lower()
        assert 'derivación' in referrals or 'interconsulta' in referrals
    
    @pytest.mark.asyncio
    async def test_enhanced_rag_integration(self):
        """Test integración completa RAG con decisión MINSAL"""
        patient_context = {
            'age': 70,
            'diabetes': True,
            'public_healthcare': True,
            'jurisdiction': 'chile'
        }
        
        enhanced_knowledge = await enhance_minsal_decision_with_rag(
            lpp_grade=2,
            confidence=0.75,
            anatomical_location="sacrum",
            patient_context=patient_context
        )
        
        assert 'error' not in enhanced_knowledge
        assert enhanced_knowledge['retrieval_confidence'] > 0.0
        
        # Verificar fuentes de evidencia
        evidence_sources = enhanced_knowledge.get('evidence_sources', [])
        minsal_sources = [src for src in evidence_sources if src['source'] == 'MINSAL']
        assert len(minsal_sources) >= 2  # Al menos 2 documentos MINSAL
    
    def test_bilingual_terminology_handling(self):
        """Test manejo terminología bilingüe"""
        # Contexto chileno - debe usar español
        chile_terminology = self.enhanced_dispatcher._get_terminology_preference("chile")
        
        assert chile_terminology['condition_name'] == 'lesiones_por_presion'
        assert 'ulceras_por_presion' in chile_terminology['alternative_names']
        assert chile_terminology['classification_system'] == 'categorias_minsal'
        
        # Contexto internacional - debe usar inglés
        intl_terminology = self.enhanced_dispatcher._get_terminology_preference("international")
        
        assert intl_terminology['condition_name'] == 'pressure_injury'
        assert 'pressure_ulcer' in intl_terminology['alternative_names']
        assert intl_terminology['classification_system'] == 'npuap_stages'
    
    def test_regulatory_compliance_routing(self):
        """Test enrutamiento según compliance regulatorio"""
        # Requerimientos Chile
        chile_reqs = self.enhanced_dispatcher._get_regulatory_requirements("chile")
        
        assert 'MINSAL_2018' in chile_reqs['primary_standards']
        assert 'NPUAP_EPUAP_2019' in chile_reqs['primary_standards']
        assert 'minsal_compliance' in chile_reqs['audit_requirements']
        assert chile_reqs['documentation_language'] == 'spanish'
        
        # Requerimientos internacionales
        intl_reqs = self.enhanced_dispatcher._get_regulatory_requirements("international")
        
        assert 'NPUAP_EPUAP_2019' in intl_reqs['primary_standards']
        assert 'MINSAL_2018' not in intl_reqs['primary_standards']
        assert intl_reqs['documentation_language'] == 'english'


@pytest.mark.integration
class TestMINSALArchitectureIntegration:
    """Tests de integración arquitectural completa"""
    
    @pytest.mark.asyncio
    async def test_complete_minsal_workflow(self):
        """Test workflow completo desde input hasta decisión MINSAL"""
        # 1. Setup componentes
        dispatcher = create_enhanced_dispatcher("chile")
        
        # 2. Mock input chileno
        class MockChileanInput:
            def __init__(self):
                self.patient_context = {
                    'age': 78,
                    'diabetes': True,
                    'public_healthcare': True,
                    'jurisdiction': 'chile'
                }
                self.metadata = {
                    'institution': 'Hospital Público Santiago',
                    'language': 'spanish'
                }
                self.medical_content = {
                    'description': 'Evaluación lesiones por presión en paciente geriátrico',
                    'image_path': 'test_sacrum_lpp.jpg'
                }
        
        chile_input = MockChileanInput()
        
        # 3. Test detección jurisdicción
        jurisdiction = dispatcher._detect_jurisdiction(chile_input)
        assert jurisdiction == "chile"
        
        # 4. Test creación agente apropiado
        agent = create_medical_agent(jurisdiction=jurisdiction, use_minsal=True)
        assert agent.decision_engine == "minsal"
        
        # 5. Test análisis con motor MINSAL
        mock_detection = {
            'detections': [{
                'class': 'lpp_grade_2',
                'confidence': 0.85,
                'anatomical_location': 'sacrum'
            }]
        }
        
        result = agent.analyze_lpp_image(
            image_path="test_sacrum_lpp.jpg",
            patient_code="CH-2025-078",
            detection_result=mock_detection,
            patient_context=chile_input.patient_context
        )
        
        # 6. Verificar resultado integrado
        assert result['success'] is True
        assert result['jurisdiction'] == 'chile'
        
        analysis = result['analysis']
        assert analysis['decision_engine'] == 'MINSAL_Enhanced'
        assert 'regulatory_compliance' in analysis
        assert analysis['regulatory_compliance']['minsal_compliant'] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])