"""
Clinical Assessment Agent - Native ADK Implementation
===================================================

LLM-powered agent for evidence-based clinical decision making.
Inherits from LLMAgent for medical reasoning and decision support.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from google.adk.agents import LLMAgent, AgentContext
from google.adk.core.types import AgentCapability
from google.adk.tools import Tool
from google.adk.models import ModelConfig

from .base import VigiaBaseAgent

logger = logging.getLogger(__name__)


class ClinicalAssessmentAgent(VigiaBaseAgent, LLMAgent):
    """
    Evidence-based clinical assessment agent using LLM reasoning.
    
    Capabilities:
    - NPUAP/EPUAP clinical decision making
    - Evidence-based medical recommendations
    - Risk factor assessment and stratification
    - Integration with medical protocols and guidelines
    """
    
    def __init__(self, config=None):
        """Initialize Clinical Assessment Agent with LLM capabilities."""
        
        capabilities = [
            AgentCapability.MEDICAL_DIAGNOSIS,
            AgentCapability.CLINICAL_REASONING,
            AgentCapability.EVIDENCE_BASED_MEDICINE,
            AgentCapability.RISK_ASSESSMENT
        ]
        
        # Initialize both base classes
        VigiaBaseAgent.__init__(
            self,
            agent_id="vigia-clinical-assessment",
            agent_name="Vigia Clinical Assessment Agent", 
            capabilities=capabilities,
            medical_specialties=["wound_care", "clinical_assessment", "evidence_based_medicine"],
            config=config
        )
        
        # Configure LLM for medical reasoning
        model_config = ModelConfig(
            model_name="gemini-2.0-flash",  # Use Gemini for medical reasoning
            temperature=0.1,  # Low temperature for consistent medical decisions
            max_tokens=2048,
            system_prompt=self._get_medical_system_prompt()
        )
        
        LLMAgent.__init__(self, model_config=model_config)
        
        # Medical knowledge base
        self.npuap_guidelines = self._load_npuap_guidelines()
        self.risk_factors = self._load_risk_factors()
        self.evidence_levels = {
            "A": "High quality evidence",
            "B": "Moderate quality evidence", 
            "C": "Low quality evidence",
            "Expert": "Expert opinion"
        }
        
        logger.info("Clinical Assessment Agent initialized with medical LLM")
    
    def _get_medical_system_prompt(self) -> str:
        """Get system prompt for medical reasoning."""
        return """
You are a clinical assessment agent specialized in pressure injury (pressure ulcer) evaluation and evidence-based medical decision making.

Your role:
- Provide evidence-based clinical assessments following NPUAP/EPUAP guidelines
- Make recommendations based on scientific evidence levels (A, B, C)
- Consider patient risk factors and medical history
- Ensure all decisions are clinically sound and properly justified
- Maintain medical accuracy and safety at all times

Guidelines:
- Always cite evidence levels for recommendations
- Consider contraindications and patient-specific factors
- Escalate complex cases to appropriate specialists
- Document reasoning clearly for medical record
- Follow medical ethics and patient safety principles

Response format should include:
- Clinical assessment summary
- Evidence-based recommendations with citations
- Risk stratification
- Follow-up plan
- Escalation criteria if applicable
"""
    
    def _load_npuap_guidelines(self) -> Dict[str, Any]:
        """Load NPUAP/EPUAP clinical guidelines."""
        return {
            "grade_1": {
                "definition": "Non-blanchable erythema of intact skin",
                "characteristics": [
                    "Intact skin with non-blanchable redness",
                    "May be painful, firm, soft, warmer or cooler",
                    "May be difficult to detect in darkly pigmented skin"
                ],
                "interventions": [
                    "Pressure redistribution",
                    "Skin assessment every shift", 
                    "Nutritional assessment",
                    "Pain management"
                ],
                "evidence_level": "A"
            },
            "grade_2": {
                "definition": "Partial-thickness loss of skin with exposed dermis",
                "characteristics": [
                    "Partial-thickness loss of skin with exposed dermis",
                    "Wound bed is viable, pink or red, moist",
                    "May present as intact or open/ruptured serum-filled blister"
                ],
                "interventions": [
                    "Moist wound healing environment",
                    "Pressure redistribution",
                    "Appropriate dressing selection",
                    "Pain assessment and management"
                ],
                "evidence_level": "A"
            },
            "grade_3": {
                "definition": "Full-thickness loss of skin",
                "characteristics": [
                    "Full-thickness loss of skin",
                    "Adipose (fat) is visible",
                    "Granulation tissue and epibole often present",
                    "May include undermining and tunneling"
                ],
                "interventions": [
                    "Wound care specialist consultation",
                    "Advanced wound care products",
                    "Nutritional optimization",
                    "Surgical evaluation if indicated"
                ],
                "evidence_level": "A"
            },
            "grade_4": {
                "definition": "Full-thickness skin and tissue loss",
                "characteristics": [
                    "Full-thickness skin and tissue loss",
                    "Exposed or directly palpable fascia, muscle, tendon, ligament, cartilage or bone",
                    "Often includes undermining and tunneling"
                ],
                "interventions": [
                    "Immediate specialist consultation",
                    "Surgical evaluation",
                    "Advanced wound care management",
                    "Multidisciplinary team approach"
                ],
                "evidence_level": "A"
            }
        }
    
    def _load_risk_factors(self) -> Dict[str, List[str]]:
        """Load pressure injury risk factors."""
        return {
            "mobility": [
                "Immobility",
                "Limited mobility", 
                "Bedbound status",
                "Wheelchair dependency"
            ],
            "sensory": [
                "Sensory impairment",
                "Decreased pain sensation",
                "Neurological conditions"
            ],
            "moisture": [
                "Incontinence",
                "Excessive sweating",
                "Wound drainage"
            ],
            "nutrition": [
                "Malnutrition",
                "Dehydration",
                "Low albumin",
                "Weight loss"
            ],
            "friction_shear": [
                "Sliding in bed",
                "Poor repositioning technique",
                "Spasticity"
            ],
            "medical": [
                "Diabetes mellitus",
                "Vascular disease",
                "Advanced age",
                "Immunocompromised status",
                "Critical illness"
            ]
        }
    
    def create_tools(self) -> List[Tool]:
        """Create clinical assessment tools."""
        
        tools = super().create_medical_tools()
        
        def assess_lpp_grade(
            image_analysis: dict,
            patient_history: dict,
            physical_exam: dict = None
        ) -> dict:
            """Perform clinical assessment of pressure injury grade.
            
            Args:
                image_analysis: Results from image analysis agent
                patient_history: Patient medical history and risk factors
                physical_exam: Optional physical examination findings
                
            Returns:
                dict: Clinical assessment with evidence-based recommendations
            """
            
            # Extract image analysis data
            detected_grade = image_analysis.get("analysis", {}).get("lpp_grade", 0)
            confidence = image_analysis.get("analysis", {}).get("confidence", 0)
            anatomical_location = image_analysis.get("analysis", {}).get("anatomical_location", "unknown")
            
            # Assess using NPUAP guidelines
            if detected_grade == 0:
                clinical_grade = 0
                recommendations = self._get_prevention_recommendations(patient_history)
            else:
                # Clinical correlation with image findings
                clinical_grade = self._correlate_clinical_findings(
                    detected_grade, confidence, patient_history, physical_exam
                )
                recommendations = self._get_treatment_recommendations(clinical_grade, patient_history)
            
            # Risk stratification
            risk_assessment = self._assess_risk_factors(patient_history)
            
            # Generate evidence-based assessment
            assessment = {
                "clinical_grade": clinical_grade,
                "image_detected_grade": detected_grade,
                "confidence_correlation": self._assess_confidence_correlation(confidence, clinical_grade),
                "anatomical_location": anatomical_location,
                "risk_assessment": risk_assessment,
                "recommendations": recommendations,
                "evidence_level": self.npuap_guidelines.get(f"grade_{clinical_grade}", {}).get("evidence_level", "C"),
                "follow_up_plan": self._generate_follow_up_plan(clinical_grade, risk_assessment),
                "escalation_criteria": self._get_escalation_criteria(clinical_grade),
                "assessment_timestamp": datetime.now().isoformat()
            }
            
            return {
                "status": "success",
                "clinical_assessment": assessment,
                "npuap_compliance": True,
                "evidence_based": True
            }
        
        tools.append(Tool(
            name="assess_lpp_grade",
            function=assess_lpp_grade,
            description="Perform evidence-based clinical assessment of pressure injury following NPUAP guidelines"
        ))
        
        def generate_care_plan(assessment: dict, patient_context: dict) -> dict:
            """Generate comprehensive care plan based on clinical assessment.
            
            Args:
                assessment: Clinical assessment results
                patient_context: Patient context and preferences
                
            Returns:
                dict: Comprehensive care plan with interventions
            """
            
            clinical_grade = assessment.get("clinical_grade", 0)
            risk_level = assessment.get("risk_assessment", {}).get("overall_risk", "medium")
            
            # Generate care plan components
            care_plan = {
                "pressure_management": self._get_pressure_management_plan(clinical_grade, risk_level),
                "wound_care": self._get_wound_care_plan(clinical_grade),
                "nutrition": self._get_nutrition_plan(assessment, patient_context),
                "monitoring": self._get_monitoring_plan(clinical_grade),
                "patient_education": self._get_education_plan(clinical_grade),
                "interdisciplinary_referrals": self._get_referral_recommendations(clinical_grade, assessment)
            }
            
            return {
                "status": "success",
                "care_plan": care_plan,
                "implementation_priority": self._determine_implementation_priority(clinical_grade),
                "expected_outcomes": self._define_expected_outcomes(clinical_grade),
                "review_schedule": self._determine_review_schedule(clinical_grade)
            }
        
        tools.append(Tool(
            name="generate_care_plan",
            function=generate_care_plan,
            description="Generate comprehensive evidence-based care plan for pressure injury management"
        ))
        
        def assess_healing_progress(
            baseline_assessment: dict,
            current_findings: dict,
            timeframe_days: int
        ) -> dict:
            """Assess healing progress and adjust care plan.
            
            Args:
                baseline_assessment: Initial clinical assessment
                current_findings: Current clinical findings
                timeframe_days: Days since baseline assessment
                
            Returns:
                dict: Healing progress assessment and care plan adjustments
            """
            
            # Compare baseline to current
            baseline_grade = baseline_assessment.get("clinical_grade", 0)
            current_grade = current_findings.get("clinical_grade", 0)
            
            # Assess progression
            if current_grade < baseline_grade:
                progress = "improving"
            elif current_grade > baseline_grade:
                progress = "worsening"
            else:
                progress = "stable"
            
            # Generate progress assessment
            progress_assessment = {
                "healing_trajectory": progress,
                "grade_change": current_grade - baseline_grade,
                "timeframe_days": timeframe_days,
                "expected_healing_time": self._estimate_healing_time(baseline_grade),
                "barriers_to_healing": self._identify_healing_barriers(current_findings),
                "care_plan_adjustments": self._recommend_care_adjustments(progress, current_findings)
            }
            
            return {
                "status": "success",
                "progress_assessment": progress_assessment,
                "continue_current_plan": progress == "improving",
                "escalation_needed": progress == "worsening"
            }
        
        tools.append(Tool(
            name="assess_healing_progress",
            function=assess_healing_progress,
            description="Assess pressure injury healing progress and recommend care plan adjustments"
        ))
        
        return tools
    
    def _correlate_clinical_findings(
        self,
        detected_grade: int,
        confidence: float,
        patient_history: dict,
        physical_exam: dict = None
    ) -> int:
        """Correlate image analysis with clinical findings."""
        
        # Start with detected grade
        clinical_grade = detected_grade
        
        # Adjust based on confidence level
        if confidence < 0.6:
            # Low confidence - be conservative
            clinical_grade = max(0, detected_grade - 1)
        
        # Consider risk factors that might increase severity
        high_risk_factors = sum([
            patient_history.get("diabetes", False),
            patient_history.get("vascular_disease", False),
            patient_history.get("immunocompromised", False),
            patient_history.get("malnutrition", False)
        ])
        
        if high_risk_factors >= 2 and confidence > 0.7:
            # Multiple risk factors with good confidence might indicate higher grade
            clinical_grade = min(4, detected_grade + 1)
        
        return clinical_grade
    
    def _assess_risk_factors(self, patient_history: dict) -> Dict[str, Any]:
        """Assess patient risk factors for pressure injury development."""
        
        risk_scores = {}
        total_risk = 0
        
        # Mobility risk
        mobility_issues = sum([
            patient_history.get("immobile", False),
            patient_history.get("wheelchair_bound", False),
            patient_history.get("limited_mobility", False)
        ])
        risk_scores["mobility"] = mobility_issues
        total_risk += mobility_issues * 2
        
        # Medical risk factors
        medical_risks = sum([
            patient_history.get("diabetes", False),
            patient_history.get("vascular_disease", False),
            patient_history.get("advanced_age", False),
            patient_history.get("critical_illness", False)
        ])
        risk_scores["medical"] = medical_risks
        total_risk += medical_risks
        
        # Nutritional risk
        nutrition_risks = sum([
            patient_history.get("malnutrition", False),
            patient_history.get("dehydration", False),
            patient_history.get("weight_loss", False)
        ])
        risk_scores["nutrition"] = nutrition_risks
        total_risk += nutrition_risks
        
        # Overall risk level
        if total_risk >= 6:
            overall_risk = "high"
        elif total_risk >= 3:
            overall_risk = "medium"
        else:
            overall_risk = "low"
        
        return {
            "risk_scores": risk_scores,
            "total_score": total_risk,
            "overall_risk": overall_risk,
            "primary_risk_factors": self._identify_primary_risks(risk_scores)
        }
    
    def _get_treatment_recommendations(self, grade: int, patient_history: dict) -> List[Dict[str, Any]]:
        """Get evidence-based treatment recommendations."""
        
        if grade == 0:
            return self._get_prevention_recommendations(patient_history)
        
        base_recommendations = self.npuap_guidelines.get(f"grade_{grade}", {}).get("interventions", [])
        
        recommendations = []
        for intervention in base_recommendations:
            recommendations.append({
                "intervention": intervention,
                "evidence_level": "A",
                "priority": "high" if grade >= 3 else "medium",
                "implementation_timeframe": "immediate" if grade >= 3 else "within_24h"
            })
        
        # Add patient-specific recommendations
        if patient_history.get("diabetes"):
            recommendations.append({
                "intervention": "Glucose control optimization",
                "evidence_level": "B",
                "priority": "high",
                "implementation_timeframe": "immediate"
            })
        
        if patient_history.get("malnutrition"):
            recommendations.append({
                "intervention": "Nutritional consultation and supplementation",
                "evidence_level": "A", 
                "priority": "high",
                "implementation_timeframe": "within_24h"
            })
        
        return recommendations
    
    def _get_prevention_recommendations(self, patient_history: dict) -> List[Dict[str, Any]]:
        """Get prevention recommendations for at-risk patients."""
        
        return [
            {
                "intervention": "Regular skin assessment (every shift)",
                "evidence_level": "A",
                "priority": "high",
                "implementation_timeframe": "immediate"
            },
            {
                "intervention": "Pressure redistribution every 2 hours",
                "evidence_level": "A",
                "priority": "high", 
                "implementation_timeframe": "immediate"
            },
            {
                "intervention": "Use of pressure-redistributing surfaces",
                "evidence_level": "A",
                "priority": "medium",
                "implementation_timeframe": "within_24h"
            },
            {
                "intervention": "Optimize nutrition and hydration",
                "evidence_level": "B",
                "priority": "medium",
                "implementation_timeframe": "ongoing"
            }
        ]
    
    def _generate_follow_up_plan(self, grade: int, risk_assessment: dict) -> Dict[str, str]:
        """Generate follow-up plan based on grade and risk."""
        
        if grade >= 3:
            return {
                "frequency": "daily",
                "duration": "until_healed",
                "assessments": "wound_measurement_photography_pain",
                "specialist_follow_up": "weekly"
            }
        elif grade >= 1:
            return {
                "frequency": "every_shift", 
                "duration": "until_resolved",
                "assessments": "skin_condition_pain_progression",
                "specialist_follow_up": "as_needed"
            }
        else:
            return {
                "frequency": "daily",
                "duration": "while_at_risk",
                "assessments": "skin_integrity_risk_factors",
                "specialist_follow_up": "not_required"
            }
    
    def _get_escalation_criteria(self, grade: int) -> List[str]:
        """Get escalation criteria for clinical cases."""
        
        base_criteria = [
            "Signs of infection (erythema, warmth, purulent drainage)",
            "Increase in wound size or depth",
            "Development of new pressure injuries",
            "Failure to improve within expected timeframe"
        ]
        
        if grade >= 3:
            base_criteria.extend([
                "Exposed bone, tendon, or muscle",
                "Suspected osteomyelitis",
                "Need for surgical intervention"
            ])
        
        return base_criteria
    
    # Additional helper methods for care planning...
    def _get_pressure_management_plan(self, grade: int, risk_level: str) -> dict:
        """Generate pressure management plan."""
        return {
            "repositioning_frequency": "2_hours" if grade >= 1 else "2_hours",
            "support_surface": "pressure_redistributing" if grade >= 2 else "standard_plus",
            "heel_elevation": True if grade >= 1 else risk_level == "high",
            "positioning_devices": ["pillows", "wedges"] if grade >= 1 else []
        }
    
    def _get_wound_care_plan(self, grade: int) -> dict:
        """Generate wound care plan."""
        if grade == 0:
            return {"intervention": "skin_protection_only"}
        elif grade <= 2:
            return {
                "dressing_type": "moist_wound_healing",
                "change_frequency": "as_needed_or_per_manufacturer",
                "cleansing": "normal_saline_gentle"
            }
        else:
            return {
                "dressing_type": "advanced_wound_care",
                "change_frequency": "per_wound_specialist_recommendation", 
                "cleansing": "normal_saline_gentle",
                "debridement": "as_indicated"
            }
    
    def _get_nutrition_plan(self, assessment: dict, patient_context: dict) -> dict:
        """Generate nutrition plan."""
        return {
            "protein_target": "1.2-1.5_g_per_kg" if assessment.get("clinical_grade", 0) >= 1 else "standard",
            "calorie_target": "30-35_kcal_per_kg",
            "supplements": ["vitamin_c", "zinc"] if assessment.get("clinical_grade", 0) >= 2 else [],
            "hydration": "adequate_unless_contraindicated"
        }
    
    def _get_monitoring_plan(self, grade: int) -> dict:
        """Generate monitoring plan."""
        return {
            "skin_assessment_frequency": "every_shift",
            "wound_measurement": "weekly" if grade >= 1 else "not_applicable",
            "photography": "weekly" if grade >= 1 else "not_applicable",
            "pain_assessment": "with_each_dressing_change" if grade >= 1 else "as_needed"
        }
    
    def _get_education_plan(self, grade: int) -> list:
        """Generate patient/family education plan."""
        base_education = [
            "pressure_injury_prevention",
            "importance_of_repositioning",
            "skin_inspection_techniques"
        ]
        
        if grade >= 1:
            base_education.extend([
                "wound_care_techniques",
                "signs_of_infection",
                "when_to_call_healthcare_provider"
            ])
        
        return base_education
    
    def _get_referral_recommendations(self, grade: int, assessment: dict) -> list:
        """Generate interdisciplinary referral recommendations."""
        referrals = []
        
        if grade >= 2:
            referrals.append("wound_care_specialist")
        
        if grade >= 3:
            referrals.extend(["plastic_surgery", "infectious_disease"])
        
        if assessment.get("risk_assessment", {}).get("nutrition", 0) >= 1:
            referrals.append("dietitian")
        
        return referrals
    
    async def process_medical_case(
        self,
        case_id: str,
        patient_data: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Process clinical assessment case using LLM reasoning.
        
        Args:
            case_id: Unique case identifier
            patient_data: Contains image analysis results and patient history
            context: Agent execution context
            
        Returns:
            Clinical assessment and recommendations
        """
        
        # Store case for tracking
        self.active_cases[case_id] = {
            "patient_id": patient_data.get("patient_id", case_id),
            "started_at": datetime.now().isoformat(),
            "status": "processing"
        }
        
        # Extract data for assessment
        image_analysis = patient_data.get("image_analysis", {})
        patient_history = patient_data.get("patient_history", {})
        physical_exam = patient_data.get("physical_exam", {})
        
        # Perform clinical assessment using tools
        tools = self.create_tools()
        assess_tool = next(tool for tool in tools if tool.name == "assess_lpp_grade")
        
        assessment_result = assess_tool.function(image_analysis, patient_history, physical_exam)
        
        # Generate care plan if assessment successful
        if assessment_result.get("status") == "success":
            care_plan_tool = next(tool for tool in tools if tool.name == "generate_care_plan")
            care_plan = care_plan_tool.function(
                assessment_result.get("clinical_assessment", {}),
                patient_data
            )
            assessment_result["care_plan"] = care_plan
        
        # Update case status
        self.active_cases[case_id]["status"] = "completed"
        self.active_cases[case_id]["completed_at"] = datetime.now().isoformat()
        self.active_cases[case_id]["result"] = assessment_result
        
        # Send A2A message to protocol agent for additional guidelines if high grade
        clinical_grade = assessment_result.get("clinical_assessment", {}).get("clinical_grade", 0)
        if clinical_grade >= 2:
            protocol_agent = await self.discover_medical_agent(
                AgentCapability.KNOWLEDGE_RETRIEVAL,
                "medical_protocols"
            )
            
            if protocol_agent:
                await self.send_medical_message(
                    protocol_agent.agent_id,
                    "protocol_consultation",
                    {
                        "case_id": case_id,
                        "lpp_grade": clinical_grade,
                        "patient_context": patient_history,
                        "requires_advanced_protocols": True
                    },
                    patient_id=patient_data.get("patient_id"),
                    urgency="high" if clinical_grade >= 3 else "medium"
                )
        
        return assessment_result