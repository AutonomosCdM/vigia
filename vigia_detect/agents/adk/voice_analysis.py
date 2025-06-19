"""
Voice Analysis Agent - Native Google ADK Implementation
======================================================

ADK LLMAgent for voice analysis using Hume AI.
Detects stress, pain, and emotional indicators in patient voice recordings.
"""

import asyncio
import json
import logging
import os
import tempfile
from typing import Dict, Any, List, Optional, AsyncIterator
from datetime import datetime
from pathlib import Path

from google.adk.agents import LLMAgent, AgentContext
from google.adk.core.types import AgentMessage, AgentResponse, AgentCapability
from google.adk.tools import Tool

from .base import VigiaBaseAgent
from ..ai.hume_ai_client import HumeAIClient, create_hume_ai_client, VoiceAnalysisResult
from ..systems.medical_decision_engine import MedicalDecisionEngine
from ..utils.shared_utilities import VigiaLogger

logger = VigiaLogger.get_logger(__name__)


class VoiceAnalysisTool(Tool):
    """
    ADK Tool for voice analysis operations.
    
    Provides capabilities for:
    - Batch voice file analysis
    - Real-time voice streaming analysis
    - Medical interpretation of voice patterns
    """
    
    def __init__(self, hume_client: HumeAIClient):
        """Initialize voice analysis tool"""
        self.hume_client = hume_client
        
        super().__init__(
            name="voice_analysis",
            description="Analyze voice recordings for stress, pain, and emotional indicators",
            parameters={
                "audio_file_path": {
                    "type": "string",
                    "description": "Path to audio file for analysis"
                },
                "patient_context": {
                    "type": "object",
                    "description": "Optional patient context for medical analysis",
                    "required": False
                },
                "analysis_type": {
                    "type": "string",
                    "enum": ["batch", "streaming"],
                    "description": "Type of analysis to perform",
                    "default": "batch"
                }
            }
        )
    
    async def execute(self, context: AgentContext, **kwargs) -> Dict[str, Any]:
        """Execute voice analysis"""
        try:
            audio_file_path = kwargs.get("audio_file_path")
            patient_context = kwargs.get("patient_context", {})
            analysis_type = kwargs.get("analysis_type", "batch")
            
            if not audio_file_path:
                return {
                    "success": False,
                    "error": "audio_file_path is required"
                }
            
            if not os.path.exists(audio_file_path):
                return {
                    "success": False,
                    "error": f"Audio file not found: {audio_file_path}"
                }
            
            # Perform voice analysis
            if analysis_type == "batch":
                async with self.hume_client as client:
                    result = await client.analyze_voice_file(
                        audio_file_path=audio_file_path,
                        patient_context=patient_context
                    )
                    
                    return {
                        "success": True,
                        "analysis_result": {
                            "request_id": result.request_id,
                            "timestamp": result.timestamp.isoformat(),
                            "expressions": result.expressions,
                            "medical_indicators": result.medical_indicators,
                            "processing_time": result.processing_time
                        }
                    }
            else:
                return {
                    "success": False,
                    "error": "Streaming analysis not implemented in this tool"
                }
                
        except Exception as e:
            logger.error(f"Voice analysis tool execution failed: {str(e)}")
            return {
                "success": False,
                "error": f"Voice analysis failed: {str(e)}"
            }


class StreamingVoiceAnalysisTool(Tool):
    """
    ADK Tool for real-time streaming voice analysis.
    """
    
    def __init__(self, hume_client: HumeAIClient):
        """Initialize streaming voice analysis tool"""
        self.hume_client = hume_client
        
        super().__init__(
            name="streaming_voice_analysis",
            description="Real-time streaming voice analysis for live patient monitoring",
            parameters={
                "stream_duration": {
                    "type": "integer",
                    "description": "Duration to stream in seconds",
                    "default": 60
                },
                "patient_context": {
                    "type": "object",
                    "description": "Patient context for medical analysis",
                    "required": False
                }
            }
        )
    
    async def execute(self, context: AgentContext, **kwargs) -> Dict[str, Any]:
        """Execute streaming voice analysis"""
        # Note: In a real implementation, this would connect to an audio stream
        # For now, we return a placeholder indicating streaming capability
        return {
            "success": True,
            "message": "Streaming voice analysis capability available",
            "note": "Connect to audio stream source for real-time analysis"
        }


class VoiceAnalysisAgent(VigiaBaseAgent, LLMAgent):
    """
    Voice Analysis Agent - Native ADK LLMAgent Implementation
    
    Capabilities:
    - Voice emotion detection and analysis
    - Medical interpretation of voice patterns
    - Real-time patient voice monitoring
    - Integration with medical decision engine
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Voice Analysis Agent.
        
        Args:
            config: Agent configuration
        """
        # Initialize base agents
        VigiaBaseAgent.__init__(
            self,
            agent_id="voice_analysis_agent",
            agent_name="Voice Analysis Agent",
            capabilities=[
                AgentCapability.REASONING,
                AgentCapability.PLANNING,
                AgentCapability.TOOL_USE
            ],
            medical_specialties=["voice_analysis", "stress_detection", "pain_assessment"]
        )
        
        # Initialize LLMAgent with medical-focused system prompt
        LLMAgent.__init__(
            self,
            system_prompt=self._get_system_prompt(),
            model_name="claude-3-sonnet-20240229",
            temperature=0.2,
            max_tokens=4000
        )
        
        # Initialize Hume AI client
        try:
            self.hume_client = create_hume_ai_client()
        except ValueError as e:
            logger.error(f"Failed to initialize Hume AI client: {str(e)}")
            self.hume_client = None
        
        # Initialize medical decision engine
        self.medical_engine = MedicalDecisionEngine()
        
        # Register tools
        if self.hume_client:
            self.voice_analysis_tool = VoiceAnalysisTool(self.hume_client)
            self.streaming_tool = StreamingVoiceAnalysisTool(self.hume_client)
            self.add_tool(self.voice_analysis_tool)
            self.add_tool(self.streaming_tool)
        
        # Agent state
        self.active_analyses = {}
        self.patient_voice_history = {}
        
        logger.info("Voice Analysis Agent initialized successfully")
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for voice analysis agent"""
        return """You are a specialized Voice Analysis Agent for the Vigia medical system.

Your primary responsibilities:
1. Analyze patient voice recordings for emotional and medical indicators
2. Detect stress, pain, anxiety, and depression markers in speech
3. Provide clinical interpretations of voice analysis results
4. Generate medical recommendations based on voice patterns
5. Monitor patient wellbeing through voice analysis

Medical expertise areas:
- Voice biomarkers for pain assessment
- Stress detection through speech prosody
- Emotional distress identification
- Mental health screening via voice
- Patient monitoring and early warning systems

Key capabilities:
- Process audio files for batch analysis
- Provide real-time streaming voice analysis
- Generate evidence-based medical recommendations
- Integrate voice analysis with patient medical context
- Ensure HIPAA compliance in all voice processing

When analyzing voice data:
1. Always consider patient medical context
2. Provide confidence levels for all assessments
3. Recommend appropriate medical follow-up when needed
4. Maintain patient privacy and data security
5. Document findings for medical record integration

Response format:
- Clear clinical assessment
- Confidence levels (0.0-1.0)
- Medical recommendations
- Follow-up actions
- Alert levels (normal/elevated/high/critical)"""
    
    async def process_voice_file(
        self, 
        audio_file_path: str,
        patient_id: str,
        patient_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process voice file for medical analysis.
        
        Args:
            audio_file_path: Path to audio file
            patient_id: Patient identifier
            patient_context: Optional patient medical context
            
        Returns:
            Comprehensive voice analysis result
        """
        try:
            if not self.hume_client:
                raise Exception("Hume AI client not available")
            
            # Perform voice analysis
            async with self.hume_client as client:
                result = await client.analyze_voice_file(
                    audio_file_path=audio_file_path,
                    patient_context=patient_context
                )
            
            # Generate LLM interpretation
            analysis_prompt = self._create_analysis_prompt(result, patient_context)
            
            llm_response = await self.generate_response(
                AgentMessage(
                    message_id=f"voice_analysis_{result.request_id}",
                    sender_id="system",
                    recipient_id=self.agent_id,
                    message_type="voice_analysis",
                    content=analysis_prompt
                )
            )
            
            # Combine technical analysis with LLM interpretation
            comprehensive_result = {
                "patient_id": patient_id,
                "analysis_id": result.request_id,
                "timestamp": result.timestamp.isoformat(),
                "technical_analysis": {
                    "expressions": result.expressions,
                    "medical_indicators": result.medical_indicators,
                    "processing_time": result.processing_time
                },
                "clinical_interpretation": {
                    "llm_assessment": llm_response.content,
                    "confidence_level": self._calculate_confidence(result),
                    "alert_level": result.medical_indicators.get("alert_level", "normal"),
                    "recommendations": result.medical_indicators.get("medical_recommendations", [])
                },
                "medical_context": patient_context or {}
            }
            
            # Store in patient history
            if patient_id not in self.patient_voice_history:
                self.patient_voice_history[patient_id] = []
            
            self.patient_voice_history[patient_id].append(comprehensive_result)
            
            # Check for alerts
            await self._check_voice_alerts(comprehensive_result)
            
            return comprehensive_result
            
        except Exception as e:
            logger.error(f"Voice file processing failed: {str(e)}")
            raise
    
    async def start_streaming_analysis(
        self,
        patient_id: str,
        audio_stream: AsyncIterator[bytes],
        patient_context: Optional[Dict[str, Any]] = None
    ):
        """
        Start real-time streaming voice analysis.
        
        Args:
            patient_id: Patient identifier
            audio_stream: Stream of audio data
            patient_context: Optional patient context
        """
        if not self.hume_client:
            raise Exception("Hume AI client not available")
        
        # Callback for real-time results
        async def analysis_callback(result: Dict[str, Any]):
            """Handle real-time analysis results"""
            try:
                # Process streaming result
                await self._process_streaming_result(patient_id, result, patient_context)
                
            except Exception as e:
                logger.error(f"Error processing streaming result: {str(e)}")
        
        # Start streaming analysis
        async with self.hume_client as client:
            await client.stream_voice_analysis(
                audio_stream=audio_stream,
                callback=analysis_callback,
                patient_context=patient_context
            )
    
    async def get_patient_voice_history(self, patient_id: str) -> List[Dict[str, Any]]:
        """Get voice analysis history for patient"""
        return self.patient_voice_history.get(patient_id, [])
    
    async def analyze_voice_trends(self, patient_id: str) -> Dict[str, Any]:
        """Analyze voice pattern trends for patient"""
        history = await self.get_patient_voice_history(patient_id)
        
        if len(history) < 2:
            return {
                "trend_analysis": "Insufficient data for trend analysis",
                "recommendation": "Collect more voice samples for trend analysis"
            }
        
        # Calculate trends
        pain_trends = [h["technical_analysis"]["medical_indicators"]["pain_score"] for h in history]
        stress_trends = [h["technical_analysis"]["medical_indicators"]["stress_level"] for h in history]
        
        trend_prompt = f"""
        Analyze voice pattern trends for patient:
        
        Pain scores over time: {pain_trends}
        Stress levels over time: {stress_trends}
        
        Number of recordings: {len(history)}
        Time span: {history[0]['timestamp']} to {history[-1]['timestamp']}
        
        Provide trend analysis and medical recommendations.
        """
        
        llm_response = await self.generate_response(
            AgentMessage(
                message_id=f"trend_analysis_{patient_id}_{int(datetime.now().timestamp())}",
                sender_id="system",
                recipient_id=self.agent_id,
                message_type="trend_analysis",
                content=trend_prompt
            )
        )
        
        return {
            "patient_id": patient_id,
            "trend_analysis": llm_response.content,
            "data_points": len(history),
            "pain_trend": "increasing" if pain_trends[-1] > pain_trends[0] else "decreasing",
            "stress_trend": "increasing" if stress_trends[-1] > stress_trends[0] else "decreasing"
        }
    
    def _create_analysis_prompt(
        self, 
        result: VoiceAnalysisResult, 
        patient_context: Optional[Dict[str, Any]]
    ) -> str:
        """Create prompt for LLM analysis of voice results"""
        context_str = ""
        if patient_context:
            context_str = f"\nPatient Context: {json.dumps(patient_context, indent=2)}"
        
        return f"""
        Analyze the following voice analysis results and provide clinical interpretation:
        
        Voice Expressions Detected:
        {json.dumps(result.expressions, indent=2)}
        
        Medical Indicators:
        {json.dumps(result.medical_indicators, indent=2)}
        {context_str}
        
        Please provide:
        1. Clinical interpretation of the voice patterns
        2. Assessment of patient emotional state
        3. Pain and stress level evaluation
        4. Medical recommendations
        5. Urgency level and any needed interventions
        6. Confidence in the assessment
        
        Format your response as a structured clinical assessment.
        """
    
    def _calculate_confidence(self, result: VoiceAnalysisResult) -> float:
        """Calculate confidence level for analysis"""
        # Basic confidence calculation based on number of detected expressions
        num_expressions = len(result.expressions)
        max_score = max(result.expressions.values()) if result.expressions else 0.0
        
        # More expressions and higher scores = higher confidence
        confidence = min(1.0, (num_expressions / 20.0) + (max_score * 0.5))
        return round(confidence, 2)
    
    async def _check_voice_alerts(self, analysis_result: Dict[str, Any]):
        """Check for voice analysis alerts and trigger notifications"""
        alert_level = analysis_result["clinical_interpretation"]["alert_level"]
        
        if alert_level in ["high", "critical"]:
            # Trigger medical alert
            await self._trigger_medical_alert(analysis_result)
    
    async def _trigger_medical_alert(self, analysis_result: Dict[str, Any]):
        """Trigger medical alert for high-priority voice analysis results"""
        # This would integrate with the communication agent for alerts
        logger.warning(f"Medical alert triggered for patient {analysis_result['patient_id']}: "
                      f"Alert level {analysis_result['clinical_interpretation']['alert_level']}")
        
        # TODO: Integrate with CommunicationAgent for Slack/WhatsApp alerts
    
    async def _process_streaming_result(
        self, 
        patient_id: str, 
        result: Dict[str, Any],
        patient_context: Optional[Dict[str, Any]]
    ):
        """Process real-time streaming analysis result"""
        # Store streaming result
        if patient_id not in self.active_analyses:
            self.active_analyses[patient_id] = []
        
        self.active_analyses[patient_id].append(result)
        
        # Check for immediate alerts
        medical_indicators = result.get("medical_indicators", {})
        alert_level = medical_indicators.get("alert_level", "normal")
        
        if alert_level in ["high", "critical"]:
            await self._trigger_medical_alert({
                "patient_id": patient_id,
                "clinical_interpretation": {"alert_level": alert_level},
                "streaming_result": result
            })


# Factory function for agent creation
def create_voice_analysis_agent(config: Optional[Dict[str, Any]] = None) -> VoiceAnalysisAgent:
    """Create voice analysis agent with configuration"""
    return VoiceAnalysisAgent(config=config)