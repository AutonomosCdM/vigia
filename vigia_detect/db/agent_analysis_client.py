"""
Agent Analysis Storage Client
============================

Comprehensive storage system for all agent analyses in the medical workflow.
Maintains complete audit trail and traceability for medical compliance.

Key Features:
- Store structured analysis results from all agents
- Cross-reference agent analyses within medical cases
- Query analysis chains to understand decision pathways
- Medical compliance and audit trail support
- Batman tokenization for HIPAA compliance

Agents Supported:
- ImageAnalysisAgent (CV pipeline results)
- ClinicalAssessmentAgent (Evidence-based decisions)
- ProtocolAgent (Medical protocol consultations)
- CommunicationAgent (Notification results)
- WorkflowOrchestrationAgent (Pipeline orchestration)
- RiskAssessmentAgent (LPP risk analysis)
- MonaiReviewAgent (MONAI output validation)
- DiagnosticAgent (Integrated diagnosis)
- VoiceAnalysisAgent (Voice expression analysis)
"""

import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

# Import Supabase client
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase not available - agent analyses will not be stored")

import os


class AgentType(Enum):
    """Supported agent types for analysis storage"""
    IMAGE_ANALYSIS = "image_analysis"
    CLINICAL_ASSESSMENT = "clinical_assessment"
    PROTOCOL = "protocol"
    COMMUNICATION = "communication"
    WORKFLOW = "workflow"
    RISK_ASSESSMENT = "risk_assessment"
    MONAI_REVIEW = "monai_review"
    DIAGNOSTIC = "diagnostic"
    VOICE_ANALYSIS = "voice_analysis"


class AnalysisStatus(Enum):
    """Analysis processing status"""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


@dataclass
class AgentAnalysisRecord:
    """Complete agent analysis record"""
    analysis_id: str
    token_id: str  # Batman token
    agent_type: str
    agent_id: str
    case_session: str
    analysis_status: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    processing_metadata: Dict[str, Any]
    medical_context: Dict[str, Any]
    confidence_scores: Dict[str, float]
    evidence_references: List[str]
    escalation_triggers: List[str]
    timestamp: datetime
    processing_time_ms: int
    raw_output_id: Optional[str] = None
    parent_analysis_id: Optional[str] = None
    hipaa_compliant: bool = True


class AgentAnalysisClient:
    """
    Client for storing and retrieving agent analysis records in the Processing Database.
    Maintains complete audit trail for medical decision-making processes.
    """
    
    def __init__(self):
        """Initialize the agent analysis storage client"""
        self.client = None
        
        # Get Supabase credentials for Processing Database
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if SUPABASE_AVAILABLE and supabase_url and supabase_key:
            try:
                self.client = create_client(supabase_url, supabase_key)
                logger.info("Connected to Processing Database for agent analyses")
            except Exception as e:
                logger.warning(f"Failed to connect to Supabase: {e}")
                self.client = None
        else:
            logger.warning("Supabase not available or credentials missing - agent analyses will not be stored")
    
    async def store_agent_analysis(self,
                                 token_id: str,
                                 agent_type: str,
                                 agent_id: str,
                                 case_session: str,
                                 input_data: Dict[str, Any],
                                 output_data: Dict[str, Any],
                                 processing_metadata: Optional[Dict[str, Any]] = None,
                                 medical_context: Optional[Dict[str, Any]] = None,
                                 confidence_scores: Optional[Dict[str, float]] = None,
                                 evidence_references: Optional[List[str]] = None,
                                 escalation_triggers: Optional[List[str]] = None,
                                 raw_output_id: Optional[str] = None,
                                 parent_analysis_id: Optional[str] = None,
                                 processing_time_ms: int = 0) -> Optional[str]:
        """
        Store complete agent analysis record.
        
        Args:
            token_id: Batman token ID (NO PHI)
            agent_type: Type of agent performing analysis
            agent_id: Unique agent identifier
            case_session: Medical case session identifier
            input_data: Complete input data provided to agent
            output_data: Complete output data from agent
            processing_metadata: Technical processing information
            medical_context: Medical context and patient factors
            confidence_scores: Confidence scores for various aspects
            evidence_references: Medical evidence references used
            escalation_triggers: Conditions that triggered escalations
            raw_output_id: Associated raw output ID if available
            parent_analysis_id: Parent analysis if this is a sub-analysis
            processing_time_ms: Processing time in milliseconds
            
        Returns:
            Analysis ID if successful, None if failed
        """
        if not self.client:
            logger.warning("No database connection - agent analysis not stored")
            return None
        
        try:
            # Generate analysis ID
            analysis_id = str(uuid.uuid4())
            
            # Prepare analysis record
            analysis_record = {
                "analysis_id": analysis_id,
                "token_id": token_id,
                "agent_type": agent_type,
                "agent_id": agent_id,
                "case_session": case_session,
                "analysis_status": AnalysisStatus.COMPLETED.value,
                "input_data": input_data,
                "output_data": output_data,
                "processing_metadata": processing_metadata or {},
                "medical_context": medical_context or {},
                "confidence_scores": confidence_scores or {},
                "evidence_references": evidence_references or [],
                "escalation_triggers": escalation_triggers or [],
                "timestamp": datetime.now().isoformat(),
                "processing_time_ms": processing_time_ms,
                "raw_output_id": raw_output_id,
                "parent_analysis_id": parent_analysis_id,
                "hipaa_compliant": True,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Store in database
            result = self.client.table("agent_analyses").insert(analysis_record).execute()
            
            if result.data:
                logger.info(f"Stored {agent_type} analysis: {analysis_id}")
                return analysis_id
            else:
                logger.error(f"Failed to store agent analysis: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error storing agent analysis: {e}")
            return None
    
    async def get_case_analysis_chain(self,
                                    case_session: str,
                                    token_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve complete analysis chain for a medical case.
        
        Args:
            case_session: Medical case session identifier
            token_id: Optional Batman token to filter by patient
            
        Returns:
            List of all agent analyses in chronological order
        """
        if not self.client:
            return []
        
        try:
            query = self.client.table("agent_analyses").select("*").eq("case_session", case_session)
            
            if token_id:
                query = query.eq("token_id", token_id)
            
            query = query.order("timestamp", desc=False)  # Chronological order
            result = query.execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error retrieving analysis chain: {e}")
            return []
    
    async def get_agent_analyses_by_type(self,
                                       agent_type: str,
                                       token_id: Optional[str] = None,
                                       days_back: int = 30,
                                       limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve analyses by specific agent type.
        
        Args:
            agent_type: Type of agent to filter by
            token_id: Optional Batman token to filter by patient
            days_back: Number of days to look back
            limit: Maximum number of results
            
        Returns:
            List of agent analyses
        """
        if not self.client:
            return []
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            query = self.client.table("agent_analyses").select("*").eq("agent_type", agent_type)
            
            if token_id:
                query = query.eq("token_id", token_id)
            
            query = query.gte("timestamp", cutoff_date.isoformat())
            query = query.order("timestamp", desc=True).limit(limit)
            
            result = query.execute()
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error retrieving {agent_type} analyses: {e}")
            return []
    
    async def trace_decision_pathway(self,
                                   analysis_id: str) -> Dict[str, Any]:
        """
        Trace complete decision pathway from a specific analysis.
        
        Args:
            analysis_id: Starting analysis ID to trace from
            
        Returns:
            Complete decision pathway with all related analyses
        """
        if not self.client:
            return {}
        
        try:
            # Get the target analysis
            result = self.client.table("agent_analyses").select("*").eq("analysis_id", analysis_id).execute()
            
            if not result.data:
                return {"error": "Analysis not found"}
            
            target_analysis = result.data[0]
            case_session = target_analysis["case_session"]
            
            # Get all analyses in the same case session
            case_analyses = await self.get_case_analysis_chain(case_session)
            
            # Find parent and child analyses
            parent_chain = []
            child_chain = []
            
            # Trace parent chain
            current_parent = target_analysis.get("parent_analysis_id")
            while current_parent:
                parent_result = self.client.table("agent_analyses").select("*").eq("analysis_id", current_parent).execute()
                if parent_result.data:
                    parent_analysis = parent_result.data[0]
                    parent_chain.append(parent_analysis)
                    current_parent = parent_analysis.get("parent_analysis_id")
                else:
                    break
            
            # Find child analyses
            for analysis in case_analyses:
                if analysis.get("parent_analysis_id") == analysis_id:
                    child_chain.append(analysis)
            
            decision_pathway = {
                "target_analysis": target_analysis,
                "parent_chain": parent_chain[::-1],  # Reverse to show oldest first
                "child_chain": child_chain,
                "case_session": case_session,
                "total_analyses_in_case": len(case_analyses),
                "decision_flow": self._build_decision_flow(parent_chain, target_analysis, child_chain),
                "confidence_evolution": self._trace_confidence_evolution(parent_chain + [target_analysis] + child_chain),
                "evidence_accumulation": self._trace_evidence_accumulation(parent_chain + [target_analysis] + child_chain)
            }
            
            return decision_pathway
            
        except Exception as e:
            logger.error(f"Error tracing decision pathway: {e}")
            return {"error": str(e)}
    
    async def analyze_agent_performance(self,
                                      agent_type: str,
                                      days_back: int = 30) -> Dict[str, Any]:
        """
        Analyze performance metrics for a specific agent type.
        
        Args:
            agent_type: Type of agent to analyze
            days_back: Number of days to analyze
            
        Returns:
            Performance analysis metrics
        """
        if not self.client:
            return {}
        
        try:
            analyses = await self.get_agent_analyses_by_type(agent_type, days_back=days_back, limit=1000)
            
            if not analyses:
                return {"agent_type": agent_type, "analysis": "No data available"}
            
            # Calculate performance metrics
            total_analyses = len(analyses)
            successful_analyses = len([a for a in analyses if a.get("analysis_status") == "completed"])
            failed_analyses = len([a for a in analyses if a.get("analysis_status") == "failed"])
            escalated_analyses = len([a for a in analyses if a.get("analysis_status") == "escalated"])
            
            # Processing time analysis
            processing_times = [a.get("processing_time_ms", 0) for a in analyses if a.get("processing_time_ms")]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            
            # Confidence analysis
            confidence_scores = []
            for analysis in analyses:
                scores = analysis.get("confidence_scores", {})
                if scores:
                    avg_confidence = sum(scores.values()) / len(scores)
                    confidence_scores.append(avg_confidence)
            
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            # Escalation analysis
            escalation_triggers = []
            for analysis in analyses:
                triggers = analysis.get("escalation_triggers", [])
                escalation_triggers.extend(triggers)
            
            # Count trigger frequencies
            trigger_counts = {}
            for trigger in escalation_triggers:
                trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1
            
            performance_metrics = {
                "agent_type": agent_type,
                "analysis_period": f"{days_back} days",
                "total_analyses": total_analyses,
                "success_rate": (successful_analyses / total_analyses) * 100 if total_analyses > 0 else 0,
                "failure_rate": (failed_analyses / total_analyses) * 100 if total_analyses > 0 else 0,
                "escalation_rate": (escalated_analyses / total_analyses) * 100 if total_analyses > 0 else 0,
                "average_processing_time_ms": avg_processing_time,
                "average_confidence": avg_confidence,
                "common_escalation_triggers": sorted(trigger_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                "daily_average": total_analyses / days_back,
                "performance_trend": self._calculate_performance_trend(analyses)
            }
            
            return performance_metrics
            
        except Exception as e:
            logger.error(f"Error analyzing agent performance: {e}")
            return {"error": str(e)}
    
    async def get_cross_agent_correlations(self,
                                         case_session: str) -> Dict[str, Any]:
        """
        Analyze correlations between different agent analyses in a case.
        
        Args:
            case_session: Medical case session to analyze
            
        Returns:
            Cross-agent correlation analysis
        """
        if not self.client:
            return {}
        
        try:
            case_analyses = await self.get_case_analysis_chain(case_session)
            
            if len(case_analyses) < 2:
                return {"analysis": "Insufficient analyses for correlation"}
            
            # Group analyses by agent type
            agent_groups = {}
            for analysis in case_analyses:
                agent_type = analysis.get("agent_type")
                if agent_type not in agent_groups:
                    agent_groups[agent_type] = []
                agent_groups[agent_type].append(analysis)
            
            # Calculate cross-correlations
            correlations = {}
            
            # Confidence correlation
            confidence_by_agent = {}
            for agent_type, analyses in agent_groups.items():
                confidences = []
                for analysis in analyses:
                    scores = analysis.get("confidence_scores", {})
                    if scores:
                        avg_confidence = sum(scores.values()) / len(scores)
                        confidences.append(avg_confidence)
                if confidences:
                    confidence_by_agent[agent_type] = sum(confidences) / len(confidences)
            
            # Evidence consistency
            evidence_overlap = self._calculate_evidence_overlap(agent_groups)
            
            # Decision agreement
            decision_agreement = self._calculate_decision_agreement(agent_groups)
            
            correlations = {
                "case_session": case_session,
                "agent_types_involved": list(agent_groups.keys()),
                "total_analyses": len(case_analyses),
                "confidence_correlations": confidence_by_agent,
                "evidence_overlap": evidence_overlap,
                "decision_agreement": decision_agreement,
                "recommendation_consistency": self._analyze_recommendation_consistency(agent_groups),
                "temporal_analysis": self._analyze_temporal_patterns(case_analyses)
            }
            
            return correlations
            
        except Exception as e:
            logger.error(f"Error analyzing cross-agent correlations: {e}")
            return {"error": str(e)}
    
    # UTILITY METHODS
    
    def _build_decision_flow(self,
                           parent_chain: List[Dict],
                           target_analysis: Dict,
                           child_chain: List[Dict]) -> List[str]:
        """Build human-readable decision flow"""
        flow = []
        
        for parent in parent_chain:
            agent_type = parent.get("agent_type", "unknown")
            output_summary = self._summarize_output(parent.get("output_data", {}))
            flow.append(f"{agent_type}: {output_summary}")
        
        agent_type = target_analysis.get("agent_type", "unknown")
        output_summary = self._summarize_output(target_analysis.get("output_data", {}))
        flow.append(f">>> {agent_type}: {output_summary} <<<")
        
        for child in child_chain:
            agent_type = child.get("agent_type", "unknown")
            output_summary = self._summarize_output(child.get("output_data", {}))
            flow.append(f"{agent_type}: {output_summary}")
        
        return flow
    
    def _summarize_output(self, output_data: Dict) -> str:
        """Summarize agent output for decision flow"""
        if not output_data:
            return "No output data"
        
        # Extract key summary information
        summary_fields = ["primary_diagnosis", "risk_level", "confidence", "recommendation", "status", "grade"]
        
        for field in summary_fields:
            if field in output_data:
                return f"{field}: {output_data[field]}"
        
        # Fallback to first available value
        if output_data:
            key, value = next(iter(output_data.items()))
            return f"{key}: {value}"
        
        return "No summary available"
    
    def _trace_confidence_evolution(self, analyses: List[Dict]) -> List[Dict[str, float]]:
        """Trace how confidence evolves through the analysis chain"""
        evolution = []
        
        for analysis in analyses:
            scores = analysis.get("confidence_scores", {})
            if scores:
                avg_confidence = sum(scores.values()) / len(scores)
                evolution.append({
                    "agent_type": analysis.get("agent_type"),
                    "timestamp": analysis.get("timestamp"),
                    "average_confidence": avg_confidence,
                    "confidence_scores": scores
                })
        
        return evolution
    
    def _trace_evidence_accumulation(self, analyses: List[Dict]) -> List[Dict[str, Any]]:
        """Trace how medical evidence accumulates through the analysis chain"""
        accumulation = []
        cumulative_evidence = set()
        
        for analysis in analyses:
            evidence = analysis.get("evidence_references", [])
            cumulative_evidence.update(evidence)
            
            accumulation.append({
                "agent_type": analysis.get("agent_type"),
                "timestamp": analysis.get("timestamp"),
                "new_evidence": evidence,
                "cumulative_evidence_count": len(cumulative_evidence),
                "cumulative_evidence": list(cumulative_evidence)
            })
        
        return accumulation
    
    def _calculate_performance_trend(self, analyses: List[Dict]) -> str:
        """Calculate performance trend over time"""
        if len(analyses) < 5:
            return "insufficient_data"
        
        # Sort by timestamp
        sorted_analyses = sorted(analyses, key=lambda x: x.get("timestamp", ""))
        
        # Compare first half vs second half success rates
        mid_point = len(sorted_analyses) // 2
        first_half = sorted_analyses[:mid_point]
        second_half = sorted_analyses[mid_point:]
        
        first_success_rate = len([a for a in first_half if a.get("analysis_status") == "completed"]) / len(first_half)
        second_success_rate = len([a for a in second_half if a.get("analysis_status") == "completed"]) / len(second_half)
        
        if second_success_rate > first_success_rate + 0.05:
            return "improving"
        elif second_success_rate < first_success_rate - 0.05:
            return "declining"
        else:
            return "stable"
    
    def _calculate_evidence_overlap(self, agent_groups: Dict[str, List[Dict]]) -> Dict[str, float]:
        """Calculate evidence overlap between different agents"""
        evidence_by_agent = {}
        
        for agent_type, analyses in agent_groups.items():
            evidence_set = set()
            for analysis in analyses:
                evidence = analysis.get("evidence_references", [])
                evidence_set.update(evidence)
            evidence_by_agent[agent_type] = evidence_set
        
        # Calculate pairwise overlaps
        overlaps = {}
        agent_types = list(evidence_by_agent.keys())
        
        for i, agent1 in enumerate(agent_types):
            for agent2 in agent_types[i+1:]:
                evidence1 = evidence_by_agent[agent1]
                evidence2 = evidence_by_agent[agent2]
                
                if evidence1 and evidence2:
                    overlap = len(evidence1.intersection(evidence2))
                    total = len(evidence1.union(evidence2))
                    overlap_percentage = (overlap / total) * 100 if total > 0 else 0
                    overlaps[f"{agent1}_{agent2}"] = overlap_percentage
        
        return overlaps
    
    def _calculate_decision_agreement(self, agent_groups: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Calculate decision agreement between agents"""
        # This is a simplified implementation
        # In production, this would analyze specific decision fields
        
        decision_fields = ["primary_diagnosis", "risk_level", "grade", "urgency"]
        agreements = {}
        
        for field in decision_fields:
            field_values = []
            for agent_type, analyses in agent_groups.items():
                for analysis in analyses:
                    output_data = analysis.get("output_data", {})
                    if field in output_data:
                        field_values.append(output_data[field])
            
            if field_values:
                unique_values = set(field_values)
                agreement_rate = (1 - (len(unique_values) - 1) / len(field_values)) * 100
                agreements[field] = {
                    "agreement_rate": agreement_rate,
                    "unique_values": list(unique_values),
                    "total_instances": len(field_values)
                }
        
        return agreements
    
    def _analyze_recommendation_consistency(self, agent_groups: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Analyze consistency of recommendations across agents"""
        # Extract recommendations from all agents
        all_recommendations = []
        
        for agent_type, analyses in agent_groups.items():
            for analysis in analyses:
                output_data = analysis.get("output_data", {})
                recommendations = output_data.get("recommendations", [])
                if isinstance(recommendations, list):
                    all_recommendations.extend(recommendations)
                elif isinstance(recommendations, str):
                    all_recommendations.append(recommendations)
        
        # Analyze consistency
        unique_recommendations = set(all_recommendations)
        consistency_score = len(unique_recommendations) / len(all_recommendations) if all_recommendations else 1
        
        return {
            "total_recommendations": len(all_recommendations),
            "unique_recommendations": len(unique_recommendations),
            "consistency_score": consistency_score,
            "common_recommendations": list(unique_recommendations)[:10]  # Top 10
        }
    
    def _analyze_temporal_patterns(self, case_analyses: List[Dict]) -> Dict[str, Any]:
        """Analyze temporal patterns in the analysis chain"""
        if len(case_analyses) < 2:
            return {"analysis": "Insufficient data for temporal analysis"}
        
        # Sort by timestamp
        sorted_analyses = sorted(case_analyses, key=lambda x: x.get("timestamp", ""))
        
        # Calculate time intervals
        intervals = []
        for i in range(1, len(sorted_analyses)):
            prev_time = datetime.fromisoformat(sorted_analyses[i-1].get("timestamp", ""))
            curr_time = datetime.fromisoformat(sorted_analyses[i].get("timestamp", ""))
            interval = (curr_time - prev_time).total_seconds()
            intervals.append(interval)
        
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        
        return {
            "total_duration_seconds": intervals and sum(intervals) or 0,
            "average_interval_seconds": avg_interval,
            "analysis_sequence": [a.get("agent_type") for a in sorted_analyses],
            "temporal_efficiency": "efficient" if avg_interval < 300 else "slow"  # 5 minutes threshold
        }


# Export for use
__all__ = ["AgentAnalysisClient", "AgentType", "AnalysisStatus", "AgentAnalysisRecord"]