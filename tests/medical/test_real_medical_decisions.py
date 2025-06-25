#!/usr/bin/env python3
"""
REAL Medical Decision Engine Tests
===================================

Tests for ACTUAL medical functionality - not mocks.
Validates real NPUAP/EPUAP guidelines implementation.
"""

import pytest
from datetime import datetime

from vigia_detect.systems.medical_decision_engine import (
    MedicalDecisionEngine, 
    LPPGrade, 
    SeverityLevel,
    EvidenceLevel
)


class TestRealMedicalDecisions:
    """Test actual medical decision engine with real NPUAP guidelines."""
    
    def setup_method(self):
        """Setup real medical decision engine."""
        self.engine = MedicalDecisionEngine()
    
    def test_grade_4_emergency_escalation_real(self):
        """Test real Grade 4 LPP triggers emergency escalation per NPUAP."""
        # Real Grade 4 LPP case
        patient_context = {
            "age": 75,
            "diabetes": True,
            "mobility": "bedbound",
            "braden_score": 12
        }
        
        # Execute REAL medical decision
        decision = self.engine.make_clinical_decision(
            lpp_grade=4,
            confidence=0.95,
            anatomical_location="sacrum",
            patient_context=patient_context
        )
        
        # Validate real medical escalation
        assert decision['severity_assessment'] == SeverityLevel.EMERGENCY.value
        assert decision['evidence_documentation']['npuap_compliance'] is True
        
        # Validate real clinical recommendations exist
        recommendations = decision['clinical_recommendations']
        assert len(recommendations) > 0
        assert any("quirúrgica" in rec.lower() for rec in recommendations), f"No surgical recommendation: {recommendations}"
        
        # Validate diabetic patient gets glucose control
        assert any("glucémico" in rec.lower() for rec in recommendations), f"No diabetes management: {recommendations}"
        
        # Validate evidence documentation
        evidence = decision['evidence_documentation']
        assert evidence['npuap_compliance'] is True
        assert 'evidence_review_date' in evidence
        
        # Validate real NPUAP references
        evidence_recs = evidence['recommendations']
        npuap_refs = [rec for rec in evidence_recs if "NPUAP" in rec['reference']]
        assert len(npuap_refs) > 0, "No NPUAP references found"
        
        # Validate escalation requirements
        escalation = decision['escalation_requirements']
        assert escalation['requires_specialist_review'] is True
        assert escalation['urgency_level'] == "emergency"
        assert escalation['review_timeline'] == "15min"
    
    def test_real_npuap_prevention_guidelines(self):
        """Test real NPUAP prevention guidelines for Grade 0."""
        patient_context = {
            "age": 65,
            "risk_factors": {"diabetes": False, "mobility": "limited"}
        }
        
        # Execute prevention decision
        decision = self.engine.make_clinical_decision(
            lpp_grade=0,
            confidence=0.90,
            anatomical_location="heel",
            patient_context=patient_context
        )
        
        # Validate prevention recommendations
        assert decision['severity_assessment'] == SeverityLevel.PREVENTIVE.value
        recommendations = decision['clinical_recommendations']
        
        # Check for real NPUAP prevention measures
        prevention_terms = ["braden", "prevention", "assessment", "repositioning"]
        has_prevention = any(
            any(term in rec.lower() for term in prevention_terms) 
            for rec in recommendations
        )
        assert has_prevention, f"Prevention recommendations missing: {recommendations}"
    
    def test_low_confidence_safety_escalation_real(self):
        """Test real safety-first escalation for low confidence cases."""
        patient_context = {
            "age": 85,
            "multiple_comorbidities": True
        }
        
        # Low confidence Grade 3 - should escalate to emergency
        decision = self.engine.make_clinical_decision(
            lpp_grade=3,
            confidence=0.45,  # Below safety threshold
            anatomical_location="sacrum", 
            patient_context=patient_context
        )
        
        # Validate safety-first escalation
        assert decision['severity_assessment'] == SeverityLevel.EMERGENCY.value
        
        # Validate escalation requirements
        escalation = decision['escalation_requirements']
        assert escalation['required'] is True
        assert escalation['reason'] == "low_confidence_safety_escalation"
    
    def test_real_evidence_levels_documented(self):
        """Test that recommendations include real evidence levels."""
        decision = self.engine.make_clinical_decision(
            lpp_grade=2,
            confidence=0.88,
            anatomical_location="heel",
            patient_context={"age": 70}
        )
        
        # Validate evidence documentation
        evidence_docs = decision['evidence_documentation']['recommendations']
        
        # Check for real evidence levels (A, B, C)
        evidence_levels = [doc['evidence_level'] for doc in evidence_docs]
        valid_levels = [EvidenceLevel.LEVEL_A.value, EvidenceLevel.LEVEL_B.value, EvidenceLevel.LEVEL_C.value]
        
        assert all(level in valid_levels for level in evidence_levels)
        
        # Check for NPUAP references
        references = [doc['reference'] for doc in evidence_docs]
        assert any("NPUAP" in ref for ref in references)
    
    def test_real_quality_metrics_calculation(self):
        """Test real quality metrics calculation."""
        decision = self.engine.make_clinical_decision(
            lpp_grade=3,
            confidence=0.92,
            anatomical_location="sacrum",
            patient_context={"age": 70, "diabetes": True}
        )
        
        # Validate quality metrics
        metrics = decision['quality_metrics']
        
        assert 'decision_confidence' in metrics
        assert 'evidence_strength' in metrics  
        assert 'safety_score' in metrics
        
        # Confidence should be realistic
        assert 0 <= metrics['decision_confidence'] <= 1
        assert 0 <= metrics['safety_score'] <= 1
    
    def test_real_anatomical_location_specific_recommendations(self):
        """Test location-specific recommendations are generated."""
        # Sacral LPP - high risk location
        sacral_decision = self.engine.make_clinical_decision(
            lpp_grade=2,
            confidence=0.85,
            anatomical_location="sacrum",
            patient_context={"age": 75}
        )
        
        # Heel LPP - different risk profile
        heel_decision = self.engine.make_clinical_decision(
            lpp_grade=2,
            confidence=0.85, 
            anatomical_location="heel",
            patient_context={"age": 75}
        )
        
        # Should have different recommendations
        sacral_recs = sacral_decision['clinical_recommendations']
        heel_recs = heel_decision['clinical_recommendations']
        
        # At least some recommendations should differ by location
        assert sacral_recs != heel_recs, "Location-specific recommendations not implemented"


class TestRealMedicalWarnings:
    """Test real medical warning generation."""
    
    def setup_method(self):
        self.engine = MedicalDecisionEngine()
    
    def test_diabetes_specific_warnings_real(self):
        """Test real diabetes-specific medical warnings."""
        diabetic_context = {
            "age": 68,
            "diabetes": True,
            "hba1c": 8.5,  # Poor control
            "medications": ["metformin", "insulin"]
        }
        
        decision = self.engine.make_clinical_decision(
            lpp_grade=2,
            confidence=0.89,
            anatomical_location="heel",
            patient_context=diabetic_context
        )
        
        # Check for diabetes-specific warnings
        warnings = decision['medical_warnings']
        diabetes_warnings = [w for w in warnings if "diabet" in w.lower() or "glucose" in w.lower()]
        
        assert len(diabetes_warnings) > 0, f"Diabetes warnings missing: {warnings}"
    
    def test_anticoagulation_bleeding_warnings_real(self):
        """Test real anticoagulation bleeding risk warnings."""
        anticoag_context = {
            "age": 72,
            "medications": ["warfarin", "aspirin"],
            "bleeding_risk": "high"
        }
        
        decision = self.engine.make_clinical_decision(
            lpp_grade=3,
            confidence=0.91,
            anatomical_location="sacrum",
            patient_context=anticoag_context
        )
        
        # Check for bleeding risk warnings
        warnings = decision['medical_warnings']
        bleeding_warnings = [w for w in warnings if "bleeding" in w.lower() or "anticoag" in w.lower()]
        
        assert len(bleeding_warnings) > 0, f"Anticoagulation warnings missing: {warnings}"


@pytest.mark.integration
class TestRealMedicalEngineIntegration:
    """Integration tests with real medical engine."""
    
    def test_complete_medical_workflow_real(self):
        """Test complete medical decision workflow with real engine."""
        engine = MedicalDecisionEngine()
        
        # Simulate real clinical case
        real_case = {
            "patient_id": "real-test-001",
            "lpp_grade": 3,
            "confidence": 0.87,
            "location": "sacrum",
            "context": {
                "age": 78,
                "diabetes": True,
                "braden_score": 14,
                "mobility": "chair-bound",
                "nutritional_status": "malnourished"
            }
        }
        
        # Execute complete workflow
        start_time = datetime.now()
        
        decision = engine.make_clinical_decision(
            lpp_grade=real_case["lpp_grade"],
            confidence=real_case["confidence"],
            anatomical_location=real_case["location"],
            patient_context=real_case["context"]
        )
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Validate complete decision structure
        required_fields = [
            'lpp_grade', 'severity_assessment', 'confidence_score',
            'clinical_recommendations', 'medical_warnings',
            'escalation_requirements', 'evidence_documentation',
            'quality_metrics'
        ]
        
        for field in required_fields:
            assert field in decision, f"Missing required field: {field}"
        
        # Validate reasonable processing time (< 1 second)
        assert processing_time < 1.0, f"Medical decision too slow: {processing_time}s"
        
        # Validate medical content quality
        assert len(decision['clinical_recommendations']) >= 2
        assert decision['evidence_documentation']['npuap_compliance'] is True
        assert decision['quality_metrics']['decision_confidence'] > 0