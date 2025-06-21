"""
Voice Medical Analysis System
=============================

Evidence-based medical analysis of voice patterns for clinical decision making.
Provides standardized assessment of voice biomarkers for pain, stress, and emotional wellbeing.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

from ..utils.shared_utilities import VigiaLogger

logger = VigiaLogger.get_logger(__name__)


class VoiceAlertLevel(Enum):
    """Voice analysis alert levels"""
    NORMAL = "normal"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


class VoiceMedicalCategory(Enum):
    """Medical categories for voice analysis"""
    PAIN_ASSESSMENT = "pain_assessment"
    STRESS_EVALUATION = "stress_evaluation"
    MENTAL_HEALTH_SCREENING = "mental_health_screening"
    GENERAL_WELLBEING = "general_wellbeing"
    EMERGENCY_ASSESSMENT = "emergency_assessment"


@dataclass
class VoiceEvidenceLevel:
    """Evidence level for voice-based medical assessment"""
    level: str  # A, B, C (following evidence-based medicine standards)
    confidence: float  # 0.0 - 1.0
    references: List[str]
    clinical_significance: str


@dataclass
class VoiceMedicalAssessment:
    """Comprehensive medical assessment from voice analysis"""
    assessment_id: str
    timestamp: datetime
    patient_id: str
    
    # Primary indicators
    pain_assessment: Dict[str, Any]
    stress_evaluation: Dict[str, Any]
    mental_health_indicators: Dict[str, Any]
    
    # Clinical interpretation
    primary_concerns: List[str]
    medical_recommendations: List[str]
    urgency_level: VoiceAlertLevel
    evidence_level: VoiceEvidenceLevel
    
    # Follow-up
    follow_up_required: bool
    follow_up_timeframe: Optional[str]
    specialist_referral: Optional[str]
    
    # Context
    patient_context: Dict[str, Any]
    analysis_metadata: Dict[str, Any]


class VoiceMedicalAnalysisEngine:
    """
    Medical analysis engine for voice-based assessments.
    
    Implements evidence-based protocols for interpreting voice biomarkers
    in clinical contexts. Provides standardized assessments following
    medical guidelines and best practices.
    """
    
    def __init__(self):
        """Initialize voice medical analysis engine"""
        self.pain_thresholds = self._setup_pain_thresholds()
        self.stress_thresholds = self._setup_stress_thresholds()
        self.mental_health_indicators = self._setup_mental_health_indicators()
        self.evidence_base = self._setup_evidence_base()
        
        logger.info("Voice Medical Analysis Engine initialized")
    
    def _setup_pain_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Setup evidence-based thresholds for pain assessment via voice"""
        return {
            "acute_pain": {
                "empathic_pain": 0.6,
                "anguish": 0.5,
                "distress": 0.4,
                "vocal_strain": 0.3
            },
            "chronic_pain": {
                "empathic_pain": 0.4,
                "tiredness": 0.5,
                "sadness": 0.4,
                "frustration": 0.3
            },
            "breakthrough_pain": {
                "empathic_pain": 0.8,
                "anguish": 0.7,
                "fear": 0.5,
                "distress": 0.6
            }
        }
    
    def _setup_stress_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Setup thresholds for stress assessment"""
        return {
            "acute_stress": {
                "anxiety": 0.6,
                "fear": 0.5,
                "nervousness": 0.4,
                "voice_tremor": 0.3
            },
            "chronic_stress": {
                "anxiety": 0.4,
                "tiredness": 0.5,
                "irritability": 0.4,
                "emotional_exhaustion": 0.4
            },
            "stress_overload": {
                "anxiety": 0.8,
                "overwhelm": 0.7,
                "panic": 0.6,
                "confusion": 0.5
            }
        }
    
    def _setup_mental_health_indicators(self) -> Dict[str, Dict[str, float]]:
        """Setup mental health screening indicators"""
        return {
            "depression_screening": {
                "sadness": 0.5,
                "tiredness": 0.4,
                "hopelessness": 0.6,
                "emotional_flatness": 0.4,
                "speech_poverty": 0.3
            },
            "anxiety_screening": {
                "anxiety": 0.5,
                "worry": 0.4,
                "nervousness": 0.4,
                "restlessness": 0.3,
                "voice_tension": 0.3
            },
            "suicidal_ideation_screening": {
                "hopelessness": 0.7,
                "despair": 0.8,
                "emotional_pain": 0.6,
                "social_withdrawal": 0.5
            }
        }
    
    def _setup_evidence_base(self) -> Dict[str, VoiceEvidenceLevel]:
        """Setup evidence base for voice biomarkers"""
        return {
            "pain_voice_correlation": VoiceEvidenceLevel(
                level="B",
                confidence=0.7,
                references=[
                    "Lautenbacher et al. (2017). Vocal correlates of pain expression",
                    "Williams et al. (2020). Voice analysis in pain assessment",
                    "Chen et al. (2019). Prosodic features of pain speech"
                ],
                clinical_significance="Moderate evidence for voice-pain correlation"
            ),
            "stress_voice_biomarkers": VoiceEvidenceLevel(
                level="B",
                confidence=0.75,
                references=[
                    "Giddens et al. (2013). Stress and voice analysis",
                    "Ruiz et al. (2020). Vocal stress detection systems",
                    "Martinez et al. (2018). Physiological stress in speech"
                ],
                clinical_significance="Good evidence for stress detection via voice"
            ),
            "depression_voice_markers": VoiceEvidenceLevel(
                level="A",
                confidence=0.8,
                references=[
                    "Cohn et al. (2009). Depression and vocal expression",
                    "Low et al. (2020). Machine learning for depression detection",
                    "Alghowinem et al. (2013). Depression speech analysis"
                ],
                clinical_significance="Strong evidence for depression voice biomarkers"
            )
        }
    
    def analyze_patient_voice(
        self,
        voice_expressions: Dict[str, float],
        patient_context: Optional[Dict[str, Any]] = None,
        patient_id: str = None
    ) -> VoiceMedicalAssessment:
        """
        Comprehensive medical analysis of patient voice data.
        
        Args:
            voice_expressions: Hume AI expression scores
            patient_context: Patient medical context
            patient_id: Patient identifier
            
        Returns:
            VoiceMedicalAssessment with clinical interpretation
        """
        assessment_id = f"voice_assessment_{int(datetime.now().timestamp() * 1000)}"
        timestamp = datetime.now()
        
        # Perform individual assessments
        pain_assessment = self._assess_pain_indicators(voice_expressions, patient_context)
        stress_evaluation = self._assess_stress_indicators(voice_expressions, patient_context)
        mental_health_indicators = self._assess_mental_health(voice_expressions, patient_context)
        
        # Determine primary concerns
        primary_concerns = self._identify_primary_concerns(
            pain_assessment, stress_evaluation, mental_health_indicators
        )
        
        # Generate medical recommendations
        medical_recommendations = self._generate_medical_recommendations(
            pain_assessment, stress_evaluation, mental_health_indicators, patient_context
        )
        
        # Determine urgency level
        urgency_level = self._determine_urgency_level(
            pain_assessment, stress_evaluation, mental_health_indicators
        )
        
        # Assess evidence level
        evidence_level = self._assess_evidence_level(voice_expressions, patient_context)
        
        # Determine follow-up requirements
        follow_up_required, follow_up_timeframe, specialist_referral = self._determine_follow_up(
            pain_assessment, stress_evaluation, mental_health_indicators, urgency_level
        )
        
        return VoiceMedicalAssessment(
            assessment_id=assessment_id,
            timestamp=timestamp,
            patient_id=patient_id or "unknown",
            pain_assessment=pain_assessment,
            stress_evaluation=stress_evaluation,
            mental_health_indicators=mental_health_indicators,
            primary_concerns=primary_concerns,
            medical_recommendations=medical_recommendations,
            urgency_level=urgency_level,
            evidence_level=evidence_level,
            follow_up_required=follow_up_required,
            follow_up_timeframe=follow_up_timeframe,
            specialist_referral=specialist_referral,
            patient_context=patient_context or {},
            analysis_metadata={
                "expressions_analyzed": len(voice_expressions),
                "processing_timestamp": timestamp.isoformat(),
                "analysis_version": "1.0"
            }
        )
    
    def _assess_pain_indicators(
        self, 
        expressions: Dict[str, float], 
        patient_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess pain indicators from voice expressions"""
        pain_scores = {}
        
        # Assess different pain types
        for pain_type, thresholds in self.pain_thresholds.items():
            score = 0.0
            detected_indicators = []
            
            for indicator, threshold in thresholds.items():
                # Map indicator to actual expression names
                expression_score = self._get_expression_score(expressions, indicator)
                
                if expression_score >= threshold:
                    score += expression_score
                    detected_indicators.append({
                        "indicator": indicator,
                        "score": expression_score,
                        "threshold": threshold
                    })
            
            pain_scores[pain_type] = {
                "score": min(1.0, score / len(thresholds)),
                "detected_indicators": detected_indicators,
                "clinical_significance": self._get_pain_significance(score, pain_type)
            }
        
        # Overall pain assessment
        overall_pain = max([scores["score"] for scores in pain_scores.values()])
        
        # Context adjustments
        if patient_context:
            overall_pain = self._adjust_pain_for_context(overall_pain, patient_context)
        
        return {
            "overall_pain_score": overall_pain,
            "pain_type_scores": pain_scores,
            "pain_level": self._categorize_pain_level(overall_pain),
            "clinical_interpretation": self._interpret_pain_assessment(overall_pain, pain_scores)
        }
    
    def _assess_stress_indicators(
        self, 
        expressions: Dict[str, float], 
        patient_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess stress indicators from voice expressions"""
        stress_scores = {}
        
        for stress_type, thresholds in self.stress_thresholds.items():
            score = 0.0
            detected_indicators = []
            
            for indicator, threshold in thresholds.items():
                expression_score = self._get_expression_score(expressions, indicator)
                
                if expression_score >= threshold:
                    score += expression_score
                    detected_indicators.append({
                        "indicator": indicator,
                        "score": expression_score,
                        "threshold": threshold
                    })
            
            stress_scores[stress_type] = {
                "score": min(1.0, score / len(thresholds)),
                "detected_indicators": detected_indicators,
                "clinical_significance": self._get_stress_significance(score, stress_type)
            }
        
        overall_stress = max([scores["score"] for scores in stress_scores.values()])
        
        # Context adjustments
        if patient_context:
            overall_stress = self._adjust_stress_for_context(overall_stress, patient_context)
        
        return {
            "overall_stress_score": overall_stress,
            "stress_type_scores": stress_scores,
            "stress_level": self._categorize_stress_level(overall_stress),
            "clinical_interpretation": self._interpret_stress_assessment(overall_stress, stress_scores)
        }
    
    def _assess_mental_health(
        self, 
        expressions: Dict[str, float], 
        patient_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess mental health indicators from voice expressions"""
        mental_health_scores = {}
        
        for condition, indicators in self.mental_health_indicators.items():
            score = 0.0
            detected_indicators = []
            
            for indicator, threshold in indicators.items():
                expression_score = self._get_expression_score(expressions, indicator)
                
                if expression_score >= threshold:
                    score += expression_score
                    detected_indicators.append({
                        "indicator": indicator,
                        "score": expression_score,
                        "threshold": threshold
                    })
            
            mental_health_scores[condition] = {
                "score": min(1.0, score / len(indicators)),
                "detected_indicators": detected_indicators,
                "screening_result": self._interpret_mental_health_screening(score, condition)
            }
        
        return {
            "screening_scores": mental_health_scores,
            "highest_risk_area": max(mental_health_scores.keys(), 
                                   key=lambda k: mental_health_scores[k]["score"]),
            "requires_professional_evaluation": any(
                scores["score"] >= 0.6 for scores in mental_health_scores.values()
            ),
            "clinical_interpretation": self._interpret_mental_health_assessment(mental_health_scores)
        }
    
    def _get_expression_score(self, expressions: Dict[str, float], indicator: str) -> float:
        """Get expression score with fuzzy matching for indicators"""
        # Direct match
        if indicator in expressions:
            return expressions[indicator]
        
        # Fuzzy matching for common indicators
        indicator_mappings = {
            "empathic_pain": ["Empathic Pain", "Pain", "Anguish"],
            "anxiety": ["Anxiety", "Nervousness", "Worry"],
            "sadness": ["Sadness", "Melancholy", "Sorrow"],
            "tiredness": ["Tiredness", "Fatigue", "Exhaustion"],
            "fear": ["Fear", "Dread", "Terror"],
            "distress": ["Distress", "Anguish", "Suffering"]
        }
        
        if indicator.lower() in indicator_mappings:
            for expression in indicator_mappings[indicator.lower()]:
                if expression in expressions:
                    return expressions[expression]
        
        return 0.0
    
    def _identify_primary_concerns(
        self, 
        pain_assessment: Dict[str, Any],
        stress_evaluation: Dict[str, Any],
        mental_health: Dict[str, Any]
    ) -> List[str]:
        """Identify primary medical concerns from voice analysis"""
        concerns = []
        
        # Pain concerns
        if pain_assessment["overall_pain_score"] >= 0.6:
            concerns.append(f"Elevated pain indicators detected (score: {pain_assessment['overall_pain_score']:.2f})")
        
        # Stress concerns
        if stress_evaluation["overall_stress_score"] >= 0.6:
            concerns.append(f"High stress levels detected (score: {stress_evaluation['overall_stress_score']:.2f})")
        
        # Mental health concerns
        if mental_health["requires_professional_evaluation"]:
            highest_risk = mental_health["highest_risk_area"]
            score = mental_health["screening_scores"][highest_risk]["score"]
            concerns.append(f"Mental health screening positive for {highest_risk} (score: {score:.2f})")
        
        if not concerns:
            concerns.append("Voice analysis indicates normal emotional and pain status")
        
        return concerns
    
    def _generate_medical_recommendations(
        self,
        pain_assessment: Dict[str, Any],
        stress_evaluation: Dict[str, Any],
        mental_health: Dict[str, Any],
        patient_context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate evidence-based medical recommendations"""
        recommendations = []
        
        # Pain recommendations
        pain_score = pain_assessment["overall_pain_score"]
        if pain_score >= 0.8:
            recommendations.append("Immediate pain assessment and management required")
        elif pain_score >= 0.6:
            recommendations.append("Pain evaluation recommended within 24-48 hours")
        elif pain_score >= 0.4:
            recommendations.append("Monitor pain levels and consider assessment if persistent")
        
        # Stress recommendations
        stress_score = stress_evaluation["overall_stress_score"]
        if stress_score >= 0.8:
            recommendations.append("High stress detected - consider immediate stress management intervention")
        elif stress_score >= 0.6:
            recommendations.append("Elevated stress levels - stress management techniques recommended")
        
        # Mental health recommendations
        if mental_health["requires_professional_evaluation"]:
            recommendations.append("Mental health screening positive - professional psychological evaluation recommended")
        
        # Context-specific recommendations
        if patient_context:
            if patient_context.get("chronic_pain") and pain_score >= 0.4:
                recommendations.append("Chronic pain patient showing elevated voice indicators - review pain management plan")
            
            if patient_context.get("post_surgical") and stress_score >= 0.4:
                recommendations.append("Post-surgical patient showing stress - additional support and education needed")
        
        if not recommendations:
            recommendations.append("Continue routine monitoring - voice analysis within normal limits")
        
        return recommendations
    
    def _determine_urgency_level(
        self,
        pain_assessment: Dict[str, Any],
        stress_evaluation: Dict[str, Any],
        mental_health: Dict[str, Any]
    ) -> VoiceAlertLevel:
        """Determine urgency level based on all assessments"""
        pain_score = pain_assessment["overall_pain_score"]
        stress_score = stress_evaluation["overall_stress_score"]
        
        # Check for critical indicators
        suicidal_screening = mental_health["screening_scores"].get("suicidal_ideation_screening", {})
        if suicidal_screening.get("score", 0) >= 0.7:
            return VoiceAlertLevel.CRITICAL
        
        # Check for high urgency
        if pain_score >= 0.8 or stress_score >= 0.8:
            return VoiceAlertLevel.HIGH
        
        # Check for elevated concerns
        if pain_score >= 0.6 or stress_score >= 0.6 or mental_health["requires_professional_evaluation"]:
            return VoiceAlertLevel.ELEVATED
        
        return VoiceAlertLevel.NORMAL
    
    def _assess_evidence_level(
        self, 
        expressions: Dict[str, float], 
        patient_context: Optional[Dict[str, Any]]
    ) -> VoiceEvidenceLevel:
        """Assess evidence level for the voice analysis"""
        # For this implementation, we'll use a composite evidence level
        # based on the strongest evidence categories detected
        
        detected_categories = []
        
        # Check for pain indicators
        if any(expr in expressions for expr in ["Empathic Pain", "Anguish", "Distress"]):
            detected_categories.append("pain_voice_correlation")
        
        # Check for stress indicators
        if any(expr in expressions for expr in ["Anxiety", "Fear", "Nervousness"]):
            detected_categories.append("stress_voice_biomarkers")
        
        # Check for depression indicators
        if any(expr in expressions for expr in ["Sadness", "Tiredness"]):
            detected_categories.append("depression_voice_markers")
        
        if not detected_categories:
            return VoiceEvidenceLevel(
                level="C",
                confidence=0.3,
                references=["Limited voice expression data"],
                clinical_significance="Insufficient data for evidence-based assessment"
            )
        
        # Return the strongest evidence level detected
        strongest_evidence = max(detected_categories, 
                               key=lambda cat: self.evidence_base[cat].confidence)
        
        return self.evidence_base[strongest_evidence]
    
    def _determine_follow_up(
        self,
        pain_assessment: Dict[str, Any],
        stress_evaluation: Dict[str, Any],
        mental_health: Dict[str, Any],
        urgency_level: VoiceAlertLevel
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Determine follow-up requirements"""
        follow_up_required = False
        follow_up_timeframe = None
        specialist_referral = None
        
        if urgency_level == VoiceAlertLevel.CRITICAL:
            follow_up_required = True
            follow_up_timeframe = "Immediate"
            specialist_referral = "Emergency mental health evaluation"
            
        elif urgency_level == VoiceAlertLevel.HIGH:
            follow_up_required = True
            follow_up_timeframe = "Within 24 hours"
            
            if pain_assessment["overall_pain_score"] >= 0.8:
                specialist_referral = "Pain management specialist"
            elif mental_health["requires_professional_evaluation"]:
                specialist_referral = "Mental health professional"
                
        elif urgency_level == VoiceAlertLevel.ELEVATED:
            follow_up_required = True
            follow_up_timeframe = "Within 1 week"
            
            if mental_health["requires_professional_evaluation"]:
                specialist_referral = "Mental health screening"
        
        return follow_up_required, follow_up_timeframe, specialist_referral
    
    # Helper methods for clinical interpretation
    def _get_pain_significance(self, score: float, pain_type: str) -> str:
        """Get clinical significance of pain score"""
        if score >= 0.8:
            return f"High {pain_type} indicators detected"
        elif score >= 0.6:
            return f"Moderate {pain_type} indicators present"
        elif score >= 0.4:
            return f"Mild {pain_type} indicators noted"
        else:
            return f"No significant {pain_type} indicators"
    
    def _get_stress_significance(self, score: float, stress_type: str) -> str:
        """Get clinical significance of stress score"""
        if score >= 0.8:
            return f"Severe {stress_type} detected"
        elif score >= 0.6:
            return f"Moderate {stress_type} present"
        elif score >= 0.4:
            return f"Mild {stress_type} indicators"
        else:
            return f"No significant {stress_type}"
    
    def _categorize_pain_level(self, score: float) -> str:
        """Categorize pain level"""
        if score >= 0.8:
            return "Severe"
        elif score >= 0.6:
            return "Moderate"
        elif score >= 0.4:
            return "Mild"
        else:
            return "Minimal/None"
    
    def _categorize_stress_level(self, score: float) -> str:
        """Categorize stress level"""
        if score >= 0.8:
            return "High"
        elif score >= 0.6:
            return "Elevated"
        elif score >= 0.4:
            return "Moderate"
        else:
            return "Normal"
    
    def _adjust_pain_for_context(self, pain_score: float, context: Dict[str, Any]) -> float:
        """Adjust pain score based on patient context"""
        adjusted_score = pain_score
        
        if context.get("chronic_pain"):
            # Chronic pain patients may have different baseline
            adjusted_score = min(1.0, pain_score * 1.2)
        
        if context.get("recent_surgery"):
            # Post-surgical patients expected to have some pain
            adjusted_score = max(0.0, pain_score - 0.1)
        
        return adjusted_score
    
    def _adjust_stress_for_context(self, stress_score: float, context: Dict[str, Any]) -> float:
        """Adjust stress score based on patient context"""
        adjusted_score = stress_score
        
        if context.get("anxiety_disorder"):
            adjusted_score = min(1.0, stress_score * 1.3)
        
        if context.get("hospital_setting"):
            # Hospital environment naturally increases stress
            adjusted_score = max(0.0, stress_score - 0.15)
        
        return adjusted_score
    
    def _interpret_pain_assessment(self, overall_pain: float, pain_scores: Dict[str, Any]) -> str:
        """Interpret pain assessment results"""
        level = self._categorize_pain_level(overall_pain)
        
        if overall_pain >= 0.8:
            return f"{level} pain indicators suggest immediate medical attention needed"
        elif overall_pain >= 0.6:
            return f"{level} pain levels warrant clinical evaluation"
        elif overall_pain >= 0.4:
            return f"{level} pain indicators present - monitor and reassess"
        else:
            return "Pain indicators within normal limits"
    
    def _interpret_stress_assessment(self, overall_stress: float, stress_scores: Dict[str, Any]) -> str:
        """Interpret stress assessment results"""
        level = self._categorize_stress_level(overall_stress)
        
        if overall_stress >= 0.8:
            return f"{level} stress levels require immediate intervention"
        elif overall_stress >= 0.6:
            return f"{level} stress warrants stress management support"
        elif overall_stress >= 0.4:
            return f"{level} stress levels - consider stress reduction techniques"
        else:
            return "Stress indicators within normal range"
    
    def _interpret_mental_health_screening(self, score: float, condition: str) -> str:
        """Interpret mental health screening results"""
        if score >= 0.7:
            return f"Positive screening for {condition} - professional evaluation recommended"
        elif score >= 0.5:
            return f"Possible indicators of {condition} - consider further assessment"
        elif score >= 0.3:
            return f"Mild indicators of {condition} - monitor"
        else:
            return f"Negative screening for {condition}"
    
    def _interpret_mental_health_assessment(self, mental_health_scores: Dict[str, Any]) -> str:
        """Interpret overall mental health assessment"""
        positive_screenings = [
            condition for condition, data in mental_health_scores.items()
            if data["score"] >= 0.6
        ]
        
        if positive_screenings:
            return f"Positive mental health screening for: {', '.join(positive_screenings)}"
        else:
            return "Mental health screening within normal limits"


# Factory function
def create_voice_medical_analysis_engine() -> VoiceMedicalAnalysisEngine:
    """Create voice medical analysis engine"""
    return VoiceMedicalAnalysisEngine()