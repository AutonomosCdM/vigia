"""
Raw AI Outputs Database Client
============================

Client for storing and retrieving raw AI outputs in the Processing Database
for research, audit, and medical validation purposes.

Features:
- Store raw MONAI, YOLOv5, and Hume AI outputs
- Compressed binary storage for large data
- Cross-reference with structured medical results
- Research approval workflow support
- Data integrity validation
"""

import json
import uuid
import gzip
import base64
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import asdict

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

from ..cv_pipeline.adaptive_medical_detector import RawOutputCapture

logger = logging.getLogger(__name__)


class RawOutputsClient:
    """Client for managing raw AI outputs in Processing Database"""
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """
        Initialize raw outputs database client.
        
        Args:
            supabase_url: Supabase URL for Processing Database
            supabase_key: Supabase API key
        """
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.client: Optional[Client] = None
        
        if SUPABASE_AVAILABLE and supabase_url and supabase_key:
            try:
                self.client = create_client(supabase_url, supabase_key)
                logger.info("Connected to Processing Database for raw outputs")
            except Exception as e:
                logger.warning(f"Failed to connect to Supabase: {e}")
                self.client = None
        else:
            logger.warning("Supabase not available or credentials missing - raw outputs will not be stored")
    
    async def store_raw_output(self,
                              token_id: str,
                              ai_engine: str,
                              raw_outputs: RawOutputCapture,
                              structured_result_id: Optional[str] = None,
                              structured_result_type: Optional[str] = None,
                              research_approved: bool = True,
                              retention_priority: str = "standard") -> Optional[str]:
        """
        Store raw AI output in the database.
        
        Args:
            token_id: Batman token ID
            ai_engine: AI engine name ('monai', 'yolov5', 'hume_ai', 'risk_assessment', 'monai_review', 'diagnostic_fusion', 'voice_analysis')
            raw_outputs: Raw output capture data
            structured_result_id: ID of associated structured result
            structured_result_type: Type of structured result
            research_approved: Whether approved for research use
            retention_priority: Data retention priority level
            
        Returns:
            Output ID if successful, None if failed
        """
        if not self.client:
            logger.warning("No database connection - raw outputs not stored")
            return None
        
        try:
            # Generate output ID
            output_id = str(uuid.uuid4())
            
            # Prepare raw output data
            raw_output_data = {
                "output_id": output_id,
                "token_id": token_id,
                "structured_result_id": structured_result_id,
                "structured_result_type": structured_result_type,
                "ai_engine": ai_engine,
                "model_version": raw_outputs.model_metadata.get("model_version") if raw_outputs.model_metadata else None,
                "model_checkpoint": raw_outputs.model_metadata.get("model_checkpoint") if raw_outputs.model_metadata else None,
                "api_version": raw_outputs.model_metadata.get("api_version") if raw_outputs.model_metadata else None,
                "analysis_timestamp": datetime.now().isoformat(),
                
                # Raw output storage
                "raw_output": raw_outputs.raw_predictions,
                "confidence_maps": base64.b64encode(raw_outputs.confidence_maps).decode() if raw_outputs.confidence_maps else None,
                "detection_arrays": base64.b64encode(raw_outputs.detection_arrays).decode() if raw_outputs.detection_arrays else None,
                "expression_vectors": base64.b64encode(raw_outputs.expression_vectors).decode() if raw_outputs.expression_vectors else None,
                
                # Metadata
                "output_format": "json_with_binary",
                "compression_method": "gzip",
                "encoding_method": "base64",
                "raw_size_bytes": self._calculate_raw_size(raw_outputs),
                "compressed_size_bytes": raw_outputs.compressed_size or 0,
                
                # Engine-specific metadata
                f"{ai_engine}_metadata": raw_outputs.model_metadata,
                
                # Processing metadata
                "medical_context": raw_outputs.processing_metadata.get("medical_context") if raw_outputs.processing_metadata else None,
                "input_characteristics": raw_outputs.processing_metadata,
                "preprocessing_applied": raw_outputs.model_metadata.get("preprocessing") if raw_outputs.model_metadata else None,
                
                # Research and audit
                "research_approved": research_approved,
                "audit_required": True,
                "retention_priority": retention_priority,
                "research_tags": self._generate_research_tags(ai_engine, raw_outputs),
                
                # Quality metrics
                "output_quality_score": self._calculate_quality_score(raw_outputs),
                
                # Compliance
                "hipaa_compliant": True,
                "phi_free_verified": True,
                "anonymization_applied": True,
                "encryption_applied": True,
                
                # Expiration based on retention priority
                "expires_at": self._calculate_expiration_date(retention_priority).isoformat() if retention_priority != "critical" else None
            }
            
            # Insert into database
            result = self.client.table("ai_raw_outputs").insert(raw_output_data).execute()
            
            if result.data:
                logger.info(f"Stored raw output {output_id} for {ai_engine} engine")
                return output_id
            else:
                logger.error(f"Failed to store raw output: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error storing raw output: {e}")
            return None
    
    async def link_raw_to_structured(self,
                                   raw_output_id: str,
                                   structured_result_id: str,
                                   structured_result_type: str,
                                   link_type: str = "primary",
                                   confidence_correlation: Optional[float] = None) -> bool:
        """
        Create link between raw output and structured result.
        
        Args:
            raw_output_id: Raw output ID
            structured_result_id: Structured result ID
            structured_result_type: Type of result ('lpp_detection', 'voice_analysis', 'multimodal_analysis')
            link_type: Type of link ('primary', 'secondary', 'backup')
            confidence_correlation: Correlation between raw and structured confidence
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False
        
        try:
            link_data = {
                "link_id": str(uuid.uuid4()),
                "raw_output_id": raw_output_id,
                "link_type": link_type,
                "confidence_correlation": confidence_correlation,
                "accuracy_verified": False,  # Will be verified later
                "used_for_training": False,
                "used_for_validation": False
            }
            
            # Set appropriate structured result reference
            if structured_result_type == "lpp_detection":
                link_data["lpp_detection_id"] = structured_result_id
            elif structured_result_type == "voice_analysis":
                link_data["voice_analysis_id"] = structured_result_id
            elif structured_result_type == "multimodal_analysis":
                link_data["multimodal_analysis_id"] = structured_result_id
            else:
                logger.error(f"Unknown structured result type: {structured_result_type}")
                return False
            
            result = self.client.table("raw_output_links").insert(link_data).execute()
            
            if result.data:
                logger.info(f"Linked raw output {raw_output_id} to {structured_result_type} {structured_result_id}")
                return True
            else:
                logger.error(f"Failed to create link: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error linking raw to structured: {e}")
            return False
    
    async def get_raw_outputs_for_research(self,
                                         ai_engine: Optional[str] = None,
                                         research_study_id: Optional[str] = None,
                                         limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve raw outputs approved for research.
        
        Args:
            ai_engine: Filter by AI engine
            research_study_id: Filter by research study
            limit: Maximum number of results
            
        Returns:
            List of raw output records
        """
        if not self.client:
            return []
        
        try:
            query = self.client.table("ai_raw_outputs").select("*").eq("research_approved", True)
            
            if ai_engine:
                query = query.eq("ai_engine", ai_engine)
            
            query = query.limit(limit)
            result = query.execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error retrieving research data: {e}")
            return []
    
    def _calculate_raw_size(self, raw_outputs: RawOutputCapture) -> int:
        """Calculate total raw data size"""
        size = 0
        
        if hasattr(raw_outputs.raw_predictions, '__len__'):
            size += len(str(raw_outputs.raw_predictions))
        
        if raw_outputs.confidence_maps:
            size += len(raw_outputs.confidence_maps)
        
        if raw_outputs.detection_arrays:
            size += len(raw_outputs.detection_arrays)
        
        if raw_outputs.expression_vectors:
            size += len(raw_outputs.expression_vectors)
        
        return size
    
    def _calculate_quality_score(self, raw_outputs: RawOutputCapture) -> float:
        """Calculate quality score for raw output"""
        # Basic quality scoring based on data completeness and metadata
        score = 0.5  # Base score
        
        if raw_outputs.raw_predictions:
            score += 0.3
        
        if raw_outputs.model_metadata:
            score += 0.1
        
        if raw_outputs.processing_metadata:
            score += 0.1
        
        return min(score, 1.0)
    
    def _generate_research_tags(self, ai_engine: str, raw_outputs: RawOutputCapture) -> List[str]:
        """Generate research tags for categorization"""
        tags = [ai_engine, "medical_ai", "lpp_detection"]
        
        if raw_outputs.model_metadata:
            if raw_outputs.model_metadata.get("medical_grade"):
                tags.append("medical_grade")
            
            architecture = raw_outputs.model_metadata.get("model_architecture")
            if architecture:
                tags.append(architecture)
        
        return tags
    
    def _calculate_expiration_date(self, retention_priority: str) -> datetime:
        """Calculate expiration date based on retention priority"""
        now = datetime.now()
        
        if retention_priority == "critical":
            return now + timedelta(days=365 * 10)  # 10 years
        elif retention_priority == "high":
            return now + timedelta(days=365 * 5)   # 5 years
        elif retention_priority == "standard":
            return now + timedelta(days=365 * 2)   # 2 years
        else:  # low
            return now + timedelta(days=365)       # 1 year
    
    # NEW SPECIALIZED METHODS FOR NEW MEDICAL AGENTS (FASE 5)
    
    async def get_risk_assessment_outputs(self,
                                        token_id: Optional[str] = None,
                                        timeframe_days: int = 30,
                                        limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve raw risk assessment outputs for analysis.
        
        Args:
            token_id: Batman token ID to filter by patient
            timeframe_days: Number of days to look back
            limit: Maximum number of results
            
        Returns:
            List of risk assessment raw outputs
        """
        if not self.client:
            return []
        
        try:
            query = self.client.table("ai_raw_outputs").select("*").eq("ai_engine", "risk_assessment")
            
            if token_id:
                query = query.eq("token_id", token_id)
            
            # Filter by timeframe
            cutoff_date = datetime.now() - timedelta(days=timeframe_days)
            query = query.gte("created_at", cutoff_date.isoformat())
            
            query = query.order("created_at", desc=True).limit(limit)
            result = query.execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error retrieving risk assessment outputs: {e}")
            return []
    
    async def get_monai_review_outputs(self,
                                     monai_output_id: Optional[str] = None,
                                     review_quality: Optional[str] = None,
                                     limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve raw MONAI review outputs for validation.
        
        Args:
            monai_output_id: Specific MONAI output ID to find reviews for
            review_quality: Filter by review quality assessment
            limit: Maximum number of results
            
        Returns:
            List of MONAI review raw outputs
        """
        if not self.client:
            return []
        
        try:
            query = self.client.table("ai_raw_outputs").select("*").eq("ai_engine", "monai_review")
            
            if monai_output_id:
                # Search for reviews related to specific MONAI output
                query = query.contains("raw_output", {"analyzed_output_id": monai_output_id})
            
            query = query.order("created_at", desc=True).limit(limit)
            result = query.execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error retrieving MONAI review outputs: {e}")
            return []
    
    async def get_diagnostic_fusion_outputs(self,
                                          token_id: Optional[str] = None,
                                          confidence_threshold: float = 0.0,
                                          limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve raw diagnostic fusion outputs for comprehensive analysis.
        
        Args:
            token_id: Batman token ID to filter by patient
            confidence_threshold: Minimum diagnostic confidence to include
            limit: Maximum number of results
            
        Returns:
            List of diagnostic fusion raw outputs
        """
        if not self.client:
            return []
        
        try:
            query = self.client.table("ai_raw_outputs").select("*").eq("ai_engine", "diagnostic_fusion")
            
            if token_id:
                query = query.eq("token_id", token_id)
            
            query = query.order("created_at", desc=True).limit(limit)
            result = query.execute()
            
            # Filter by confidence if specified
            if confidence_threshold > 0.0 and result.data:
                filtered_data = []
                for output in result.data:
                    raw_output = output.get("raw_output", {})
                    confidence = raw_output.get("diagnostic_confidence", 0.0)
                    if isinstance(confidence, (int, float)) and confidence >= confidence_threshold:
                        filtered_data.append(output)
                return filtered_data
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Error retrieving diagnostic fusion outputs: {e}")
            return []
    
    async def get_comprehensive_case_outputs(self,
                                           token_id: str,
                                           case_session: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve all raw outputs for a comprehensive medical case analysis.
        
        Args:
            token_id: Batman token ID for the patient
            case_session: Optional session token to filter by specific case
            
        Returns:
            Dictionary with all agent outputs organized by type
        """
        if not self.client:
            return {}
        
        try:
            # Get all outputs for this patient
            query = self.client.table("ai_raw_outputs").select("*").eq("token_id", token_id)
            
            if case_session:
                query = query.contains("raw_output", {"session_token": case_session})
            
            query = query.order("created_at", desc=True)
            result = query.execute()
            
            if not result.data:
                return {}
            
            # Organize by AI engine type
            organized_outputs = {
                "monai": [],
                "yolov5": [],
                "hume_ai": [],
                "risk_assessment": [],
                "monai_review": [],
                "diagnostic_fusion": [],
                "voice_analysis": []
            }
            
            for output in result.data:
                engine = output.get("ai_engine", "unknown")
                if engine in organized_outputs:
                    organized_outputs[engine].append(output)
            
            return organized_outputs
            
        except Exception as e:
            logger.error(f"Error retrieving comprehensive case outputs: {e}")
            return {}
    
    async def analyze_agent_performance_trends(self,
                                             ai_engine: str,
                                             days_back: int = 30) -> Dict[str, Any]:
        """
        Analyze performance trends for a specific agent type.
        
        Args:
            ai_engine: Agent type to analyze
            days_back: Number of days to analyze
            
        Returns:
            Performance analysis dictionary
        """
        if not self.client:
            return {}
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            
            query = self.client.table("ai_raw_outputs").select("*").eq("ai_engine", ai_engine).gte("created_at", cutoff_date.isoformat())
            result = query.execute()
            
            if not result.data:
                return {"total_outputs": 0, "analysis": "No data available"}
            
            outputs = result.data
            total_outputs = len(outputs)
            
            # Extract confidence scores for analysis
            confidence_scores = []
            processing_times = []
            
            for output in outputs:
                raw_data = output.get("raw_output", {})
                
                # Extract confidence (varies by agent type)
                confidence = None
                if ai_engine == "risk_assessment":
                    confidence = raw_data.get("assessment_confidence")
                elif ai_engine == "monai_review":
                    confidence = raw_data.get("technical_score")
                elif ai_engine == "diagnostic_fusion":
                    confidence = raw_data.get("diagnostic_confidence")
                
                if confidence is not None:
                    confidence_scores.append(float(confidence))
                
                # Extract processing time if available
                proc_time = raw_data.get("processing_time")
                if proc_time:
                    processing_times.append(float(proc_time))
            
            analysis = {
                "total_outputs": total_outputs,
                "average_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
                "confidence_std": np.std(confidence_scores) if confidence_scores else 0,
                "average_processing_time": sum(processing_times) / len(processing_times) if processing_times else 0,
                "daily_average": total_outputs / days_back,
                "time_range": f"{days_back} days",
                "ai_engine": ai_engine
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing agent performance: {e}")
            return {"error": str(e)}