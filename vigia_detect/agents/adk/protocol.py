"""
Protocol Agent - Native ADK Implementation
=========================================

LLM-powered agent for medical protocol retrieval and guidance consultation.
Inherits from LlmAgent for intelligent protocol search and recommendation.
"""

import logging
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

from google.adk.agents import LlmAgent, AgentContext
from google.adk.core.types import AgentCapability
from google.adk.tools import Tool
from google.adk.models import ModelConfig

from .base import VigiaBaseAgent

logger = logging.getLogger(__name__)


class ProtocolAgent(VigiaBaseAgent, LlmAgent):
    """
    Medical protocol consultation agent using LLM and vector search.
    
    Capabilities:
    - Medical protocol retrieval using semantic search
    - Evidence-based guideline consultation
    - Clinical pathway recommendations
    - Protocol compliance verification
    """
    
    def __init__(self, config=None):
        """Initialize Protocol Agent with LLM and vector search capabilities."""
        
        capabilities = [
            AgentCapability.KNOWLEDGE_RETRIEVAL,
            AgentCapability.INFORMATION_SYNTHESIS,
            AgentCapability.MEDICAL_GUIDELINES,
            AgentCapability.EVIDENCE_RETRIEVAL
        ]
        
        # Initialize both base classes
        VigiaBaseAgent.__init__(
            self,
            agent_id="vigia-protocol-agent",
            agent_name="Vigia Medical Protocol Agent",
            capabilities=capabilities,
            medical_specialties=["medical_protocols", "clinical_guidelines", "evidence_based_medicine"],
            config=config
        )
        
        # Configure LLM for protocol analysis
        model_config = ModelConfig(
            model_name="gemini-1.5-flash",
            temperature=0.2,  # Slightly higher for protocol interpretation
            max_tokens=3072,
            system_prompt=self._get_protocol_system_prompt()
        )
        
        LlmAgent.__init__(self, model_config=model_config)
        
        # Medical protocol database
        self.protocol_database = self._initialize_protocol_database()
        self.vector_embeddings = {}  # Will store protocol embeddings
        self.embedding_model = None  # Placeholder for embedding model
        
        # Protocol categories
        self.protocol_categories = {
            "wound_care": "Wound care and pressure injury management",
            "infection_control": "Infection prevention and control protocols",
            "pain_management": "Pain assessment and management guidelines",
            "nutrition": "Nutritional support protocols",
            "mobility": "Mobility and positioning guidelines",
            "medication": "Medication administration protocols"
        }
        
        logger.info("Protocol Agent initialized with medical guideline database")
    
    def _get_protocol_system_prompt(self) -> str:
        """Get system prompt for protocol consultation."""
        return """
You are a medical protocol consultation agent specialized in retrieving and interpreting clinical guidelines, evidence-based protocols, and medical standards.

Your role:
- Search and retrieve relevant medical protocols and guidelines
- Interpret complex medical guidelines for practical application
- Provide evidence-based protocol recommendations
- Ensure compliance with medical standards (NPUAP, EPUAP, MINSAL, etc.)
- Synthesize multiple protocols when needed

Guidelines:
- Always provide the most current evidence-based protocols
- Include evidence levels and guideline sources
- Consider patient-specific contraindications
- Provide step-by-step implementation guidance
- Flag any protocol conflicts or considerations
- Maintain medical accuracy and safety standards

Response format should include:
- Relevant protocol(s) found
- Evidence level and source guidelines
- Step-by-step implementation instructions
- Contraindications and precautions
- Monitoring and follow-up requirements
"""
    
    def _initialize_protocol_database(self) -> Dict[str, Dict[str, Any]]:
        """Initialize medical protocol database."""
        return {
            "lpp_prevention_npuap_2019": {
                "title": "NPUAP Pressure Injury Prevention Guidelines 2019",
                "category": "wound_care",
                "evidence_level": "A",
                "source": "National Pressure Injury Advisory Panel (NPUAP)",
                "last_updated": "2019-04-01",
                "protocol_steps": [
                    {
                        "step": 1,
                        "action": "Conduct comprehensive skin and risk assessment",
                        "frequency": "On admission and daily",
                        "evidence_level": "A"
                    },
                    {
                        "step": 2,
                        "action": "Implement pressure redistribution plan",
                        "frequency": "Every 2 hours while awake, every 4 hours at night",
                        "evidence_level": "A"
                    },
                    {
                        "step": 3,
                        "action": "Use pressure redistribution surfaces",
                        "frequency": "For high-risk patients",
                        "evidence_level": "A"
                    },
                    {
                        "step": 4,
                        "action": "Optimize nutrition and hydration",
                        "frequency": "Daily assessment and intervention",
                        "evidence_level": "B"
                    }
                ],
                "contraindications": [
                    "Unstable spinal injuries (modify positioning)",
                    "Severe cardiac conditions (limit frequency if indicated)"
                ],
                "monitoring": [
                    "Daily skin inspection",
                    "Weekly risk reassessment",
                    "Document all interventions"
                ]
            },
            "lpp_treatment_grade_1": {
                "title": "LPP Grade 1 Treatment Protocol",
                "category": "wound_care",
                "evidence_level": "A",
                "source": "EPUAP/NPUAP/PPPIA Guidelines 2019",
                "protocol_steps": [
                    {
                        "step": 1,
                        "action": "Eliminate or redistribute pressure",
                        "frequency": "Immediate and ongoing",
                        "evidence_level": "A"
                    },
                    {
                        "step": 2,
                        "action": "Protect skin with appropriate barrier",
                        "frequency": "As needed",
                        "evidence_level": "B"
                    },
                    {
                        "step": 3,
                        "action": "Monitor for progression or improvement",
                        "frequency": "Every shift",
                        "evidence_level": "A"
                    }
                ],
                "expected_healing": "3-7 days with proper intervention"
            },
            "lpp_treatment_grade_2": {
                "title": "LPP Grade 2 Treatment Protocol",
                "category": "wound_care",
                "evidence_level": "A",
                "source": "EPUAP/NPUAP/PPPIA Guidelines 2019",
                "protocol_steps": [
                    {
                        "step": 1,
                        "action": "Create moist wound healing environment",
                        "frequency": "Maintain continuously",
                        "evidence_level": "A"
                    },
                    {
                        "step": 2,
                        "action": "Select appropriate dressing (hydrocolloid, foam)",
                        "frequency": "Change per manufacturer guidelines",
                        "evidence_level": "A"
                    },
                    {
                        "step": 3,
                        "action": "Manage pain appropriately",
                        "frequency": "Before and during dressing changes",
                        "evidence_level": "B"
                    },
                    {
                        "step": 4,
                        "action": "Implement pressure redistribution",
                        "frequency": "Continuous",
                        "evidence_level": "A"
                    }
                ],
                "expected_healing": "1-3 weeks with proper intervention"
            },
            "lpp_treatment_grade_3_4": {
                "title": "LPP Grade 3/4 Advanced Treatment Protocol",
                "category": "wound_care",
                "evidence_level": "A",
                "source": "EPUAP/NPUAP/PPPIA Guidelines 2019",
                "protocol_steps": [
                    {
                        "step": 1,
                        "action": "Immediate wound care specialist consultation",
                        "frequency": "Within 24 hours",
                        "evidence_level": "A"
                    },
                    {
                        "step": 2,
                        "action": "Assess for infection signs",
                        "frequency": "Daily",
                        "evidence_level": "A"
                    },
                    {
                        "step": 3,
                        "action": "Debridement if indicated",
                        "frequency": "As clinically indicated",
                        "evidence_level": "A"
                    },
                    {
                        "step": 4,
                        "action": "Advanced wound care products",
                        "frequency": "Per specialist recommendation",
                        "evidence_level": "B"
                    },
                    {
                        "step": 5,
                        "action": "Surgical evaluation if no improvement",
                        "frequency": "If no improvement in 2-4 weeks",
                        "evidence_level": "B"
                    }
                ],
                "expected_healing": "Weeks to months depending on factors"
            },
            "minsal_lpp_protocol_chile": {
                "title": "MINSAL Chile Pressure Injury Protocol",
                "category": "wound_care",
                "evidence_level": "National Standard",
                "source": "Ministerio de Salud Chile",
                "protocol_steps": [
                    {
                        "step": 1,
                        "action": "Evaluate using Braden Scale adapted for Chilean population",
                        "frequency": "On admission and every 48 hours",
                        "evidence_level": "National Standard"
                    },
                    {
                        "step": 2,
                        "action": "Implement prevention bundle per MINSAL guidelines",
                        "frequency": "For all patients with Braden ≤16",
                        "evidence_level": "National Standard"
                    },
                    {
                        "step": 3,
                        "action": "Document using standardized MINSAL forms",
                        "frequency": "All assessments and interventions",
                        "evidence_level": "Regulatory Requirement"
                    }
                ],
                "regulatory_compliance": "Required for Chilean healthcare facilities"
            },
            "infection_control_wound": {
                "title": "Wound Infection Prevention Protocol",
                "category": "infection_control",
                "evidence_level": "A",
                "source": "CDC Guidelines 2022",
                "protocol_steps": [
                    {
                        "step": 1,
                        "action": "Hand hygiene before and after wound contact",
                        "frequency": "Every interaction",
                        "evidence_level": "A"
                    },
                    {
                        "step": 2,
                        "action": "Use aseptic technique for dressing changes",
                        "frequency": "All dressing changes",
                        "evidence_level": "A"
                    },
                    {
                        "step": 3,
                        "action": "Monitor for signs of infection",
                        "frequency": "Daily",
                        "evidence_level": "A"
                    }
                ]
            }
        }
    
    def create_tools(self) -> List[Tool]:
        """Create protocol consultation tools."""
        
        tools = super().create_medical_tools()
        
        def search_medical_protocols(
            query: str,
            category: str = None,
            evidence_level: str = None,
            patient_context: dict = None
        ) -> dict:
            """Search medical protocols using semantic similarity.
            
            Args:
                query: Search query for medical protocols
                category: Optional protocol category filter
                evidence_level: Optional evidence level filter (A, B, C)
                patient_context: Optional patient context for personalization
                
            Returns:
                dict: Relevant protocols and recommendations
            """
            try:
                # Perform semantic search (simplified implementation)
                relevant_protocols = self._semantic_search_protocols(query, category, evidence_level)
                
                # Rank by relevance and evidence level
                ranked_protocols = self._rank_protocols_by_relevance(relevant_protocols, query)
                
                # Personalize based on patient context
                if patient_context:
                    ranked_protocols = self._personalize_protocols(ranked_protocols, patient_context)
                
                # Generate synthesis
                protocol_synthesis = self._synthesize_protocols(ranked_protocols, query)
                
                return {
                    "status": "success",
                    "search_query": query,
                    "protocols_found": len(ranked_protocols),
                    "relevant_protocols": ranked_protocols[:3],  # Top 3 most relevant
                    "protocol_synthesis": protocol_synthesis,
                    "evidence_summary": self._summarize_evidence_levels(ranked_protocols)
                }
                
            except Exception as e:
                logger.error(f"Error searching protocols: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "search_query": query
                }
        
        tools.append(Tool(
            name="search_medical_protocols",
            function=search_medical_protocols,
            description="Search medical protocols and guidelines using semantic similarity"
        ))
        
        def get_protocol_implementation_plan(
            protocol_id: str,
            patient_context: dict,
            care_setting: str = "hospital"
        ) -> dict:
            """Generate implementation plan for specific medical protocol.
            
            Args:
                protocol_id: Identifier of the medical protocol
                patient_context: Patient-specific context and conditions
                care_setting: Care setting (hospital, outpatient, home)
                
            Returns:
                dict: Detailed implementation plan
            """
            try:
                protocol = self.protocol_database.get(protocol_id)
                if not protocol:
                    return {
                        "status": "error",
                        "error": f"Protocol {protocol_id} not found"
                    }
                
                # Generate implementation plan
                implementation_plan = self._create_implementation_plan(protocol, patient_context, care_setting)
                
                # Check for contraindications
                contraindication_check = self._check_contraindications(protocol, patient_context)
                
                # Generate monitoring plan
                monitoring_plan = self._create_monitoring_plan(protocol, patient_context)
                
                return {
                    "status": "success",
                    "protocol_info": {
                        "title": protocol["title"],
                        "evidence_level": protocol["evidence_level"],
                        "source": protocol["source"]
                    },
                    "implementation_plan": implementation_plan,
                    "contraindication_check": contraindication_check,
                    "monitoring_plan": monitoring_plan,
                    "expected_outcomes": protocol.get("expected_healing", "Varies by patient"),
                    "implementation_priority": self._determine_implementation_priority(protocol, patient_context)
                }
                
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        tools.append(Tool(
            name="get_protocol_implementation_plan",
            function=get_protocol_implementation_plan,
            description="Generate detailed implementation plan for specific medical protocol"
        ))
        
        def verify_protocol_compliance(
            implemented_actions: list,
            protocol_id: str,
            timeframe_hours: int = 24
        ) -> dict:
            """Verify compliance with medical protocol implementation.
            
            Args:
                implemented_actions: List of actions taken
                protocol_id: Protocol being followed
                timeframe_hours: Time window for compliance check
                
            Returns:
                dict: Compliance assessment and recommendations
            """
            try:
                protocol = self.protocol_database.get(protocol_id)
                if not protocol:
                    return {"status": "error", "error": "Protocol not found"}
                
                # Check compliance
                compliance_assessment = self._assess_protocol_compliance(
                    implemented_actions, protocol, timeframe_hours
                )
                
                # Generate recommendations for gaps
                gap_recommendations = self._generate_compliance_recommendations(
                    compliance_assessment["gaps"], protocol
                )
                
                return {
                    "status": "success",
                    "protocol_title": protocol["title"],
                    "compliance_score": compliance_assessment["score"],
                    "completed_steps": compliance_assessment["completed"],
                    "missing_steps": compliance_assessment["gaps"],
                    "compliance_level": compliance_assessment["level"],
                    "recommendations": gap_recommendations,
                    "next_actions": self._get_next_protocol_actions(protocol, compliance_assessment)
                }
                
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        tools.append(Tool(
            name="verify_protocol_compliance",
            function=verify_protocol_compliance,
            description="Verify compliance with medical protocol implementation"
        ))
        
        def synthesize_multiple_protocols(
            protocol_queries: list,
            patient_context: dict,
            priority_condition: str = None
        ) -> dict:
            """Synthesize recommendations from multiple medical protocols.
            
            Args:
                protocol_queries: List of protocol search queries
                patient_context: Patient context for personalization
                priority_condition: Primary condition to prioritize
                
            Returns:
                dict: Synthesized protocol recommendations
            """
            try:
                # Search each protocol query
                all_protocols = []
                for query in protocol_queries:
                    search_result = search_medical_protocols(query, patient_context=patient_context)
                    if search_result.get("status") == "success":
                        all_protocols.extend(search_result.get("relevant_protocols", []))
                
                # Remove duplicates and prioritize
                unique_protocols = self._deduplicate_protocols(all_protocols)
                prioritized_protocols = self._prioritize_by_condition(unique_protocols, priority_condition)
                
                # Synthesize into unified recommendations
                unified_recommendations = self._create_unified_protocol_synthesis(
                    prioritized_protocols, patient_context
                )
                
                # Check for conflicts
                conflict_analysis = self._analyze_protocol_conflicts(prioritized_protocols)
                
                return {
                    "status": "success",
                    "protocols_analyzed": len(unique_protocols),
                    "priority_condition": priority_condition,
                    "unified_recommendations": unified_recommendations,
                    "protocol_conflicts": conflict_analysis,
                    "implementation_sequence": self._create_implementation_sequence(prioritized_protocols)
                }
                
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        tools.append(Tool(
            name="synthesize_multiple_protocols",
            function=synthesize_multiple_protocols,
            description="Synthesize recommendations from multiple medical protocols"
        ))
        
        return tools
    
    def _semantic_search_protocols(
        self,
        query: str,
        category: str = None,
        evidence_level: str = None
    ) -> List[Dict[str, Any]]:
        """Perform semantic search on protocol database."""
        
        # Simple keyword-based search (in production, would use vector embeddings)
        query_terms = query.lower().split()
        relevant_protocols = []
        
        for protocol_id, protocol in self.protocol_database.items():
            relevance_score = 0
            
            # Title matching
            title_matches = sum(1 for term in query_terms if term in protocol["title"].lower())
            relevance_score += title_matches * 3
            
            # Category matching
            if category and protocol.get("category") == category:
                relevance_score += 5
            
            # Content matching (simplified)
            protocol_text = json.dumps(protocol).lower()
            content_matches = sum(1 for term in query_terms if term in protocol_text)
            relevance_score += content_matches
            
            # Evidence level filter
            if evidence_level and protocol.get("evidence_level") != evidence_level:
                relevance_score *= 0.5
            
            if relevance_score > 0:
                protocol_copy = protocol.copy()
                protocol_copy["protocol_id"] = protocol_id
                protocol_copy["relevance_score"] = relevance_score
                relevant_protocols.append(protocol_copy)
        
        return relevant_protocols
    
    def _rank_protocols_by_relevance(
        self,
        protocols: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """Rank protocols by relevance and evidence level."""
        
        def ranking_score(protocol):
            relevance = protocol.get("relevance_score", 0)
            evidence_weight = {"A": 3, "B": 2, "C": 1, "National Standard": 4}.get(
                protocol.get("evidence_level", "C"), 1
            )
            return relevance * evidence_weight
        
        return sorted(protocols, key=ranking_score, reverse=True)
    
    def _personalize_protocols(
        self,
        protocols: List[Dict[str, Any]],
        patient_context: dict
    ) -> List[Dict[str, Any]]:
        """Personalize protocols based on patient context."""
        
        # Add patient-specific considerations
        for protocol in protocols:
            considerations = []
            
            # Age considerations
            if patient_context.get("age", 0) > 65:
                considerations.append("Consider age-related factors in implementation")
            
            # Comorbidity considerations
            if patient_context.get("diabetes"):
                considerations.append("Monitor glucose control during wound healing")
            
            if patient_context.get("immunocompromised"):
                considerations.append("Enhanced infection monitoring required")
            
            protocol["patient_considerations"] = considerations
        
        return protocols
    
    def _synthesize_protocols(
        self,
        protocols: List[Dict[str, Any]],
        query: str
    ) -> Dict[str, Any]:
        """Synthesize multiple protocols into unified recommendations."""
        
        if not protocols:
            return {"synthesis": "No relevant protocols found"}
        
        # Extract common themes
        all_steps = []
        evidence_levels = []
        
        for protocol in protocols:
            if "protocol_steps" in protocol:
                all_steps.extend(protocol["protocol_steps"])
            evidence_levels.append(protocol.get("evidence_level", "C"))
        
        # Create synthesis
        synthesis = {
            "primary_recommendations": self._extract_primary_recommendations(all_steps),
            "evidence_strength": max(evidence_levels, key=lambda x: {"A": 3, "B": 2, "C": 1}.get(x, 0)),
            "implementation_priority": "high" if any(level == "A" for level in evidence_levels) else "medium",
            "protocol_sources": [p.get("source", "Unknown") for p in protocols[:3]]
        }
        
        return synthesis
    
    def _extract_primary_recommendations(self, steps: List[Dict[str, Any]]) -> List[str]:
        """Extract primary recommendations from protocol steps."""
        
        # Group similar actions
        action_groups = {}
        for step in steps:
            action = step.get("action", "").lower()
            if "assessment" in action:
                action_groups.setdefault("assessment", []).append(step)
            elif "position" in action or "redistrib" in action:
                action_groups.setdefault("pressure_management", []).append(step)
            elif "dressing" in action or "wound" in action:
                action_groups.setdefault("wound_care", []).append(step)
            elif "nutrition" in action:
                action_groups.setdefault("nutrition", []).append(step)
            else:
                action_groups.setdefault("general", []).append(step)
        
        # Generate primary recommendations
        recommendations = []
        for category, category_steps in action_groups.items():
            if category_steps:
                highest_evidence = max(
                    category_steps,
                    key=lambda x: {"A": 3, "B": 2, "C": 1}.get(x.get("evidence_level", "C"), 0)
                )
                recommendations.append(highest_evidence["action"])
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _create_implementation_plan(
        self,
        protocol: Dict[str, Any],
        patient_context: dict,
        care_setting: str
    ) -> Dict[str, Any]:
        """Create detailed implementation plan for protocol."""
        
        steps = protocol.get("protocol_steps", [])
        
        implementation_plan = {
            "immediate_actions": [],
            "daily_actions": [],
            "weekly_actions": [],
            "special_considerations": []
        }
        
        for step in steps:
            frequency = step.get("frequency", "").lower()
            action = step.get("action")
            
            if "immediate" in frequency or "urgent" in frequency:
                implementation_plan["immediate_actions"].append({
                    "action": action,
                    "evidence_level": step.get("evidence_level"),
                    "timeframe": "0-2 hours"
                })
            elif "daily" in frequency or "shift" in frequency:
                implementation_plan["daily_actions"].append({
                    "action": action,
                    "evidence_level": step.get("evidence_level"),
                    "frequency": frequency
                })
            elif "weekly" in frequency:
                implementation_plan["weekly_actions"].append({
                    "action": action,
                    "evidence_level": step.get("evidence_level"),
                    "frequency": frequency
                })
        
        # Add care setting considerations
        if care_setting == "home":
            implementation_plan["special_considerations"].append(
                "Adapt procedures for home care environment"
            )
        elif care_setting == "icu":
            implementation_plan["special_considerations"].append(
                "Coordinate with ICU protocols and life support equipment"
            )
        
        return implementation_plan
    
    def _check_contraindications(
        self,
        protocol: Dict[str, Any],
        patient_context: dict
    ) -> Dict[str, Any]:
        """Check for protocol contraindications in patient context."""
        
        contraindications = protocol.get("contraindications", [])
        identified_issues = []
        
        for contraindication in contraindications:
            contraindication_lower = contraindication.lower()
            
            # Check patient context for contraindications
            if "spinal" in contraindication_lower and patient_context.get("spinal_injury"):
                identified_issues.append({
                    "issue": contraindication,
                    "patient_factor": "spinal injury",
                    "recommendation": "Modify positioning protocol per spinal precautions"
                })
            
            if "cardiac" in contraindication_lower and patient_context.get("heart_condition"):
                identified_issues.append({
                    "issue": contraindication,
                    "patient_factor": "cardiac condition",
                    "recommendation": "Consult cardiology before frequent repositioning"
                })
        
        return {
            "contraindications_found": len(identified_issues),
            "issues": identified_issues,
            "safe_to_proceed": len(identified_issues) == 0,
            "modifications_needed": len(identified_issues) > 0
        }
    
    async def process_medical_case(
        self,
        case_id: str,
        patient_data: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Process protocol consultation case using LLM reasoning.
        
        Args:
            case_id: Unique case identifier
            patient_data: Contains clinical assessment and consultation request
            context: Agent execution context
            
        Returns:
            Protocol consultation results and recommendations
        """
        
        # Store case for tracking
        self.active_cases[case_id] = {
            "patient_id": patient_data.get("patient_id", case_id),
            "started_at": datetime.now().isoformat(),
            "status": "processing"
        }
        
        # Extract consultation request
        consultation_request = patient_data.get("consultation_request", {})
        lpp_grade = consultation_request.get("lpp_grade", 0)
        patient_context = patient_data.get("patient_context", {})
        
        # Search for relevant protocols
        tools = self.create_tools()
        search_tool = next(tool for tool in tools if tool.name == "search_medical_protocols")
        
        # Build search query based on case
        if lpp_grade == 0:
            search_query = "pressure injury prevention protocol"
        elif lpp_grade <= 2:
            search_query = f"pressure injury grade {lpp_grade} treatment protocol"
        else:
            search_query = f"advanced pressure injury grade {lpp_grade} treatment protocol"
        
        # Add Chilean compliance if needed
        if patient_context.get("location") == "chile":
            search_query += " MINSAL Chile"
        
        protocol_results = search_tool.function(
            search_query,
            category="wound_care",
            patient_context=patient_context
        )
        
        # Generate implementation plan if protocols found
        implementation_plan = None
        if protocol_results.get("status") == "success" and protocol_results.get("relevant_protocols"):
            best_protocol = protocol_results["relevant_protocols"][0]
            protocol_id = best_protocol.get("protocol_id")
            
            if protocol_id:
                implementation_tool = next(tool for tool in tools if tool.name == "get_protocol_implementation_plan")
                implementation_plan = implementation_tool.function(
                    protocol_id,
                    patient_context,
                    patient_data.get("care_setting", "hospital")
                )
        
        # Compile results
        result = {
            "status": "success",
            "case_id": case_id,
            "consultation_query": search_query,
            "protocol_search_results": protocol_results,
            "implementation_plan": implementation_plan,
            "recommendations_summary": self._generate_protocol_summary(protocol_results, lpp_grade)
        }
        
        # Update case status
        self.active_cases[case_id]["status"] = "completed"
        self.active_cases[case_id]["completed_at"] = datetime.now().isoformat()
        self.active_cases[case_id]["result"] = result
        
        # Send A2A message to communication agent for care team notification
        if lpp_grade >= 2:  # Notify for significant protocols
            comm_agent = await self.discover_medical_agent(
                AgentCapability.COMMUNICATION,
                "notifications"
            )
            
            if comm_agent:
                await self.send_medical_message(
                    comm_agent.agent_id,
                    "protocol_notification",
                    {
                        "case_id": case_id,
                        "protocol_consultation": result,
                        "care_team_notification": True,
                        "implementation_urgency": "high" if lpp_grade >= 3 else "medium"
                    },
                    patient_id=patient_data.get("patient_id"),
                    urgency="high" if lpp_grade >= 3 else "medium"
                )
        
        return result
    
    def _generate_protocol_summary(
        self,
        protocol_results: Dict[str, Any],
        lpp_grade: int
    ) -> Dict[str, Any]:
        """Generate summary of protocol recommendations."""
        
        if protocol_results.get("status") != "success":
            return {"summary": "No protocols found for the specified criteria"}
        
        synthesis = protocol_results.get("protocol_synthesis", {})
        
        return {
            "primary_interventions": synthesis.get("primary_recommendations", [])[:3],
            "evidence_strength": synthesis.get("evidence_strength", "C"),
            "implementation_priority": synthesis.get("implementation_priority", "medium"),
            "clinical_urgency": "high" if lpp_grade >= 3 else "medium",
            "expected_outcomes": "Improvement expected with protocol adherence",
            "monitoring_frequency": "daily" if lpp_grade >= 2 else "routine"
        }