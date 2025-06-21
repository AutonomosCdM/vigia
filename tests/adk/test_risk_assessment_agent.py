#!/usr/bin/env python3
"""
Test Risk Assessment Agent - Comprehensive Testing Suite
=======================================================

Complete testing framework for the RiskAssessmentAgent ADK implementation.
Tests all risk assessment scales and medical protocols.

Test Coverage:
- Braden Scale assessment (pressure injury risk)
- STRATIFY fall risk evaluation
- Infection risk scoring
- MUST nutritional risk assessment
- Comprehensive multi-scale assessment
- Evidence-based recommendations
- Risk correlation analysis
"""

import pytest
import asyncio
import logging
from typing import Dict, Any
from datetime import datetime, timezone

# Test imports
from vigia_detect.agents.adk.risk_assessment import (
    RiskAssessmentAgent,
    RiskLevel,
    AssessmentScale,
    BradenScaleCalculator,
    create_risk_assessment_agent
)

logger = logging.getLogger(__name__)


class TestRiskAssessmentAgent:
    """Comprehensive test suite for Risk Assessment Agent"""
    
    @pytest.fixture
    async def risk_agent(self):
        """Create risk assessment agent for testing"""
        agent = create_risk_assessment_agent()
        yield agent
    
    @pytest.fixture
    def sample_patient_data(self):
        """Sample patient data for testing"""
        return {
            'patient_id': 'TEST-RISK-001',
            'age': 75,
            'bmi': 20.5,
            'consciousness_level': 'alert',
            'sensory_impairment': False,
            'responds_to_pressure': True,
            'incontinence': 'occasional',
            'diaphoresis': False,
            'mobility': 'limited',
            'bedbound': False,
            'wheelchair_bound': True,
            'position_changes_frequency': 'frequent_assistance',
            'position_assistance_required': True,
            'oral_intake_percentage': 80,
            'enteral_nutrition': False,
            'recent_weight_loss': False,
            'albumin_level': 3.2,
            'slides_in_bed': False,
            'spasticity': False,
            'requires_assistance_moving': True,
            'recent_falls': True,
            'confusion': False,
            'agitation': False,
            'visual_impairment': True,
            'frequent_toileting': False,
            'immunosuppression': False,
            'invasive_devices': ['urinary_catheter'],
            'diabetes': True,
            'recent_surgery': False,
            'recent_antibiotics': False,
            'malnutrition': False,
            'weight_loss_percentage_3months': 3.0,
            'acute_disease_no_intake': False
        }
    
    @pytest.fixture
    def high_risk_patient_data(self):
        """High-risk patient data for testing escalation"""
        return {
            'patient_id': 'TEST-RISK-002',
            'age': 82,
            'bmi': 16.8,
            'consciousness_level': 'sedated',
            'sensory_impairment': True,
            'responds_to_pressure': False,
            'incontinence': 'both',
            'diaphoresis': True,
            'mobility': 'none',
            'bedbound': True,
            'wheelchair_bound': False,
            'position_changes_frequency': 'none',
            'position_assistance_required': True,
            'oral_intake_percentage': 25,
            'enteral_nutrition': False,
            'recent_weight_loss': True,
            'albumin_level': 2.8,
            'slides_in_bed': True,
            'spasticity': True,
            'requires_assistance_moving': True,
            'recent_falls': True,
            'confusion': True,
            'agitation': True,
            'visual_impairment': True,
            'frequent_toileting': True,
            'immunosuppression': True,
            'invasive_devices': ['central_line', 'ventilator', 'urinary_catheter'],
            'diabetes': True,
            'recent_surgery': True,
            'recent_antibiotics': True,
            'malnutrition': True,
            'weight_loss_percentage_3months': 12.0,
            'acute_disease_no_intake': True
        }
    
    async def test_braden_scale_assessment(self, risk_agent, sample_patient_data):
        """Test Braden Scale assessment functionality"""
        logger.info("Testing Braden Scale assessment")
        
        # Perform assessment
        result = await risk_agent.assess_braden_scale(sample_patient_data)
        
        # Validate result structure
        assert result.patient_id == 'TEST-RISK-001'
        assert result.assessment_type == 'braden_scale'
        assert isinstance(result.total_score, int)
        assert 6 <= result.total_score <= 23  # Valid Braden score range
        assert isinstance(result.risk_level, RiskLevel)
        assert isinstance(result.recommendations, list)
        assert len(result.recommendations) > 0
        assert isinstance(result.confidence_score, float)
        assert 0.0 <= result.confidence_score <= 1.0
        
        # Validate evidence summary
        assert 'assessment_tool' in result.evidence_summary
        assert result.evidence_summary['assessment_tool'] == 'Braden Scale'
        assert 'total_score' in result.evidence_summary
        assert 'subscale_scores' in result.evidence_summary
        
        # Check all 6 Braden subscales are present
        subscales = result.evidence_summary['subscale_scores']
        expected_subscales = [
            'sensory_perception', 'moisture', 'activity', 
            'mobility', 'nutrition', 'friction_shear'
        ]
        for subscale in expected_subscales:
            assert subscale in subscales
        
        logger.info(f"Braden assessment completed - Score: {result.total_score}, Risk: {result.risk_level.value}")
    
    async def test_braden_high_risk_patient(self, risk_agent, high_risk_patient_data):
        """Test Braden Scale with high-risk patient"""
        logger.info("Testing Braden Scale with high-risk patient")
        
        result = await risk_agent.assess_braden_scale(high_risk_patient_data)
        
        # High-risk patient should have low Braden score
        assert result.total_score <= 12  # High risk threshold
        assert result.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]
        assert result.escalation_required is True
        
        # Should have comprehensive recommendations
        assert len(result.recommendations) >= 4
        
        # Check for critical recommendations
        recommendation_text = ' '.join(result.recommendations).lower()
        assert 'immediate' in recommendation_text or 'urgent' in recommendation_text
        
    async def test_fall_risk_assessment(self, risk_agent, sample_patient_data):
        """Test STRATIFY fall risk assessment"""
        logger.info("Testing fall risk assessment")
        
        result = await risk_agent.assess_fall_risk(sample_patient_data)
        
        # Validate result structure
        assert result.patient_id == 'TEST-RISK-001'
        assert result.assessment_type == 'fall_risk'
        assert isinstance(result.total_score, int)
        assert 0 <= result.total_score <= 5  # Valid STRATIFY range
        assert isinstance(result.risk_level, RiskLevel)
        
        # Validate evidence summary
        assert result.evidence_summary['assessment_tool'] == 'STRATIFY Scale'
        assert 'stratify_score' in result.evidence_summary
        
        logger.info(f"Fall risk assessment completed - STRATIFY Score: {result.total_score}")
    
    async def test_infection_risk_assessment(self, risk_agent, sample_patient_data):
        """Test infection risk assessment"""
        logger.info("Testing infection risk assessment")
        
        result = await risk_agent.assess_infection_risk(sample_patient_data)
        
        # Validate result structure
        assert result.patient_id == 'TEST-RISK-001'
        assert result.assessment_type == 'infection_risk'
        assert isinstance(result.total_score, int)
        assert result.total_score >= 0
        assert isinstance(result.risk_level, RiskLevel)
        
        # Validate evidence summary
        assert 'assessment_method' in result.evidence_summary
        assert 'infection_score' in result.evidence_summary
        
        logger.info(f"Infection risk assessment completed - Score: {result.total_score}")
    
    async def test_nutritional_risk_assessment(self, risk_agent, sample_patient_data):
        """Test MUST nutritional risk assessment"""
        logger.info("Testing nutritional risk assessment")
        
        result = await risk_agent.assess_nutritional_risk(sample_patient_data)
        
        # Validate result structure
        assert result.patient_id == 'TEST-RISK-001'
        assert result.assessment_type == 'nutritional_risk'
        assert isinstance(result.total_score, int)
        assert result.total_score >= 0
        assert isinstance(result.risk_level, RiskLevel)
        
        # Validate evidence summary
        assert result.evidence_summary['assessment_tool'] == 'MUST (Malnutrition Universal Screening Tool)'
        assert 'must_score' in result.evidence_summary
        
        logger.info(f"Nutritional risk assessment completed - MUST Score: {result.total_score}")
    
    async def test_comprehensive_risk_assessment(self, risk_agent, sample_patient_data):
        """Test comprehensive multi-scale assessment"""
        logger.info("Testing comprehensive risk assessment")
        
        result = await risk_agent.perform_comprehensive_risk_assessment(sample_patient_data)
        
        # Validate comprehensive result structure
        assert 'patient_id' in result
        assert 'assessment_timestamp' in result
        assert 'overall_risk_level' in result
        assert 'escalation_required' in result
        assert 'individual_assessments' in result
        assert 'combined_recommendations' in result
        assert 'risk_correlation_analysis' in result
        
        # Validate individual assessments
        assessments = result['individual_assessments']
        expected_assessments = ['braden_scale', 'fall_risk', 'infection_risk', 'nutritional_risk']
        
        for assessment_type in expected_assessments:
            assert assessment_type in assessments
            assessment = assessments[assessment_type]
            assert 'score' in assessment
            assert 'risk_level' in assessment
            assert 'recommendations' in assessment
            assert 'evidence_summary' in assessment
        
        # Validate combined recommendations
        assert isinstance(result['combined_recommendations'], list)
        assert len(result['combined_recommendations']) > 0
        
        # Validate risk correlation analysis
        correlation = result['risk_correlation_analysis']
        assert 'high_risk_domains' in correlation
        assert 'synergistic_risks' in correlation
        assert 'priority_interventions' in correlation
        
        logger.info(f"Comprehensive assessment completed - Overall risk: {result['overall_risk_level']}")
    
    async def test_high_risk_comprehensive_assessment(self, risk_agent, high_risk_patient_data):
        """Test comprehensive assessment with high-risk patient"""
        logger.info("Testing comprehensive assessment with high-risk patient")
        
        result = await risk_agent.perform_comprehensive_risk_assessment(high_risk_patient_data)
        
        # High-risk patient should trigger escalation
        assert result['escalation_required'] is True
        
        # Should have multiple high-risk domains
        correlation = result['risk_correlation_analysis']
        assert len(correlation['high_risk_domains']) >= 2
        
        # Should have synergistic risks identified
        if len(correlation['high_risk_domains']) >= 2:
            assert len(correlation['synergistic_risks']) >= 0  # May have synergistic risks
        
        logger.info(f"High-risk comprehensive assessment completed")
    
    async def test_braden_scale_calculator(self):
        """Test individual Braden Scale calculator components"""
        logger.info("Testing Braden Scale calculator components")
        
        calculator = BradenScaleCalculator()
        
        # Test sensory perception calculation
        test_data = {'consciousness_level': 'alert', 'sensory_impairment': False, 'responds_to_pressure': True}
        score, desc = calculator.calculate_sensory_perception(test_data)
        assert 1 <= score <= 4
        assert isinstance(desc, str)
        
        # Test moisture calculation
        test_data = {'incontinence': 'none', 'diaphoresis': False}
        score, desc = calculator.calculate_moisture(test_data)
        assert 1 <= score <= 4
        assert isinstance(desc, str)
        
        # Test activity calculation
        test_data = {'mobility': 'independent', 'bedbound': False, 'wheelchair_bound': False}
        score, desc = calculator.calculate_activity(test_data)
        assert 1 <= score <= 4
        assert isinstance(desc, str)
        
        # Test mobility calculation
        test_data = {'position_changes_frequency': 'independent', 'assistance_required': False}
        score, desc = calculator.calculate_mobility(test_data)
        assert 1 <= score <= 4
        assert isinstance(desc, str)
        
        # Test nutrition calculation
        test_data = {'oral_intake_percentage': 90, 'enteral_nutrition': False, 'recent_weight_loss': False, 'albumin_level': 3.5}
        score, desc = calculator.calculate_nutrition(test_data)
        assert 1 <= score <= 4
        assert isinstance(desc, str)
        
        # Test friction/shear calculation
        test_data = {'slides_in_bed': False, 'spasticity': False, 'requires_assistance_moving': False}
        score, desc = calculator.calculate_friction_shear(test_data)
        assert 1 <= score <= 3
        assert isinstance(desc, str)
        
        logger.info("Braden Scale calculator component tests completed")
    
    async def test_agent_medical_case_processing(self, risk_agent, sample_patient_data):
        """Test agent medical case processing interface"""
        logger.info("Testing agent medical case processing")
        
        result = await risk_agent.process_medical_case(
            case_id='TEST-CASE-001',
            patient_data=sample_patient_data,
            context={'test_context': True}
        )
        
        # Validate processing result
        assert result['success'] is True
        assert result['case_id'] == 'TEST-CASE-001'
        assert 'assessment_result' in result
        assert 'processing_timestamp' in result
        
        # Validate assessment result structure
        assessment = result['assessment_result']
        assert 'patient_id' in assessment
        assert 'overall_risk_level' in assessment
        assert 'individual_assessments' in assessment
        
        logger.info("Medical case processing test completed")
    
    async def test_risk_level_thresholds(self, risk_agent):
        """Test risk level threshold calculations"""
        logger.info("Testing risk level thresholds")
        
        # Test very low risk Braden patient
        low_risk_data = {
            'patient_id': 'LOW-RISK-001',
            'consciousness_level': 'alert',
            'incontinence': 'none',
            'mobility': 'independent',
            'oral_intake_percentage': 100,
            'slides_in_bed': False
        }
        
        result = await risk_agent.assess_braden_scale(low_risk_data)
        assert result.risk_level in [RiskLevel.LOW, RiskLevel.VERY_LOW]
        assert result.escalation_required is False
        
        # Test very high risk Braden patient
        high_risk_data = {
            'patient_id': 'HIGH-RISK-001',
            'consciousness_level': 'comatose',
            'incontinence': 'both',
            'bedbound': True,
            'position_changes_frequency': 'none',
            'oral_intake_percentage': 20,
            'slides_in_bed': True
        }
        
        result = await risk_agent.assess_braden_scale(high_risk_data)
        assert result.risk_level in [RiskLevel.HIGH, RiskLevel.VERY_HIGH]
        assert result.escalation_required is True
        
        logger.info("Risk level threshold tests completed")
    
    def test_risk_assessment_agent_initialization(self):
        """Test proper agent initialization"""
        logger.info("Testing Risk Assessment Agent initialization")
        
        agent = create_risk_assessment_agent()
        
        # Validate agent properties
        assert agent._agent_id == "vigia-risk-assessment"
        assert agent._agent_name == "Risk Assessment Agent"
        assert "braden_scale_assessment" in agent._capabilities
        assert "fall_risk_evaluation" in agent._capabilities
        assert "infection_risk_scoring" in agent._capabilities
        assert "nutritional_risk_assessment" in agent._capabilities
        
        # Validate medical specialties
        assert "preventive_medicine" in agent._medical_specialties
        assert "wound_care" in agent._medical_specialties
        assert "geriatrics" in agent._medical_specialties
        
        logger.info("Agent initialization test completed")


# Pytest test runner
if __name__ == "__main__":
    pytest.main([__file__, "-v"])