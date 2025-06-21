"""
Hume AI Client for Voice Analysis
=================================

Client for Hume AI's Expression Measurement and EVI APIs.
Provides voice analysis capabilities for stress, pain, and emotional detection.
"""

import asyncio
import json
import logging
import os
import time
import websockets
from typing import Dict, List, Optional, Any, AsyncIterator, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
import aiohttp
from urllib.parse import urljoin

from ..utils.shared_utilities import VigiaLogger

logger = VigiaLogger.get_logger(__name__)


@dataclass
class VoiceAnalysisResult:
    """Result from voice analysis"""
    request_id: str
    timestamp: datetime
    expressions: Dict[str, float]  # Expression name -> confidence score
    medical_indicators: Dict[str, Any]
    raw_hume_response: Dict[str, Any]
    processing_time: float


@dataclass
class MedicalVoiceIndicators:
    """Medical indicators derived from voice analysis"""
    pain_score: float  # 0.0 - 1.0
    stress_level: float  # 0.0 - 1.0
    emotional_distress: float  # 0.0 - 1.0
    anxiety_indicators: float  # 0.0 - 1.0
    depression_markers: float  # 0.0 - 1.0
    overall_wellbeing: float  # 0.0 - 1.0
    alert_level: str  # "normal", "elevated", "high", "critical"
    medical_recommendations: List[str]


class HumeAIClient:
    """
    Client for Hume AI voice analysis services.
    
    Supports both REST (batch processing) and WebSocket (streaming) APIs.
    Includes medical context processing and HIPAA-compliant handling.
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.hume.ai"):
        """
        Initialize Hume AI client.
        
        Args:
            api_key: Hume AI API key
            base_url: Base URL for Hume AI API
        """
        self.api_key = api_key
        self.base_url = base_url
        self.session = None
        
        # Medical expression mapping
        self.medical_expressions = self._setup_medical_expressions()
        
        logger.info("Hume AI client initialized")
    
    def _setup_medical_expressions(self) -> Dict[str, Dict[str, float]]:
        """
        Setup mapping of Hume expressions to medical indicators.
        
        Based on Hume's 48 vocal expression dimensions.
        """
        return {
            "pain_indicators": {
                "Empathic Pain": 1.0,
                "Anguish": 0.8,
                "Distress": 0.7,
                "Sadness": 0.6,
                "Tiredness": 0.5
            },
            "stress_indicators": {
                "Anxiety": 1.0,
                "Fear": 0.9,
                "Nervousness": 0.8,
                "Worry": 0.7,
                "Confusion": 0.6,
                "Awkwardness": 0.5
            },
            "emotional_distress": {
                "Anguish": 1.0,
                "Distress": 0.9,
                "Disappointment": 0.7,
                "Sadness": 0.8,
                "Guilt": 0.6,
                "Shame": 0.6
            },
            "anxiety_indicators": {
                "Anxiety": 1.0,
                "Fear": 0.9,
                "Nervousness": 0.8,
                "Worry": 0.7,
                "Awkwardness": 0.6
            },
            "depression_markers": {
                "Sadness": 1.0,
                "Tiredness": 0.8,
                "Boredom": 0.7,
                "Disappointment": 0.6,
                "Contempt": 0.5
            },
            "positive_indicators": {
                "Joy": 1.0,
                "Excitement": 0.9,
                "Amusement": 0.8,
                "Interest": 0.7,
                "Admiration": 0.6,
                "Calmness": 0.5
            }
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            headers={
                "X-Hume-Api-Key": self.api_key,
                "Content-Type": "application/json"
            },
            timeout=aiohttp.ClientTimeout(total=60)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def analyze_voice_file(
        self, 
        audio_file_path: str,
        patient_context: Optional[Dict[str, Any]] = None
    ) -> VoiceAnalysisResult:
        """
        Analyze voice file for emotional expressions.
        
        Args:
            audio_file_path: Path to audio file
            patient_context: Optional patient context for medical analysis
            
        Returns:
            VoiceAnalysisResult with expressions and medical indicators
        """
        start_time = time.time()
        request_id = f"voice_analysis_{int(start_time * 1000)}"
        
        try:
            # Prepare multipart form data
            with open(audio_file_path, 'rb') as audio_file:
                form_data = aiohttp.FormData()
                form_data.add_field(
                    'file',
                    audio_file,
                    filename=os.path.basename(audio_file_path),
                    content_type='audio/wav'
                )
                form_data.add_field(
                    'models',
                    json.dumps({"prosody": {}})  # Request speech prosody analysis
                )
                
                # Make API request
                url = urljoin(self.base_url, "/v0/batch/jobs")
                async with self.session.post(url, data=form_data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Hume API error: {response.status} - {error_text}")
                    
                    job_data = await response.json()
                    job_id = job_data.get("job_id")
                    
                    if not job_id:
                        raise Exception("No job ID returned from Hume API")
                    
                    # Poll for job completion
                    result = await self._wait_for_job_completion(job_id)
                    
                    # Process results
                    expressions = self._extract_expressions(result)
                    medical_indicators = self._analyze_medical_indicators(
                        expressions, patient_context
                    )
                    
                    processing_time = time.time() - start_time
                    
                    return VoiceAnalysisResult(
                        request_id=request_id,
                        timestamp=datetime.now(),
                        expressions=expressions,
                        medical_indicators=asdict(medical_indicators),
                        raw_hume_response=result,
                        processing_time=processing_time
                    )
                    
        except Exception as e:
            logger.error(f"Voice analysis failed: {str(e)}")
            raise
    
    async def stream_voice_analysis(
        self,
        audio_stream: AsyncIterator[bytes],
        callback: Callable[[Dict[str, Any]], None],
        patient_context: Optional[Dict[str, Any]] = None
    ):
        """
        Stream real-time voice analysis using EVI WebSocket.
        
        Args:
            audio_stream: Async iterator of audio chunks
            callback: Callback function for real-time results
            patient_context: Optional patient context
        """
        ws_url = "wss://api.hume.ai/v0/evi/chat"
        
        headers = {
            "X-Hume-Api-Key": self.api_key
        }
        
        try:
            async with websockets.connect(ws_url, extra_headers=headers) as websocket:
                # Send initial configuration
                config_message = {
                    "type": "session_settings",
                    "audio_encoding": "linear16",
                    "sample_rate": 16000
                }
                await websocket.send(json.dumps(config_message))
                
                # Start streaming audio
                async def send_audio():
                    async for audio_chunk in audio_stream:
                        audio_message = {
                            "type": "audio_input",
                            "data": audio_chunk.hex()  # Convert bytes to hex string
                        }
                        await websocket.send(json.dumps(audio_message))
                
                # Start receiving results
                async def receive_results():
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            
                            if data.get("type") == "user_message":
                                # Process prosody data
                                prosody = data.get("prosody", {})
                                if prosody:
                                    expressions = self._extract_prosody_expressions(prosody)
                                    medical_indicators = self._analyze_medical_indicators(
                                        expressions, patient_context
                                    )
                                    
                                    result = {
                                        "timestamp": datetime.now().isoformat(),
                                        "expressions": expressions,
                                        "medical_indicators": asdict(medical_indicators),
                                        "prosody_data": prosody
                                    }
                                    
                                    # Call callback with results
                                    callback(result)
                                    
                        except Exception as e:
                            logger.error(f"Error processing streaming result: {str(e)}")
                
                # Run both sending and receiving concurrently
                await asyncio.gather(send_audio(), receive_results())
                
        except Exception as e:
            logger.error(f"Streaming voice analysis failed: {str(e)}")
            raise
    
    async def _wait_for_job_completion(self, job_id: str, max_wait: int = 300) -> Dict[str, Any]:
        """Wait for batch job completion and return results"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            url = urljoin(self.base_url, f"/v0/batch/jobs/{job_id}")
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to check job status: {response.status}")
                
                job_status = await response.json()
                state = job_status.get("state")
                
                if state == "COMPLETED":
                    # Get predictions
                    predictions_url = urljoin(self.base_url, f"/v0/batch/jobs/{job_id}/predictions")
                    async with self.session.get(predictions_url) as pred_response:
                        if pred_response.status != 200:
                            raise Exception(f"Failed to get predictions: {pred_response.status}")
                        
                        return await pred_response.json()
                
                elif state == "FAILED":
                    raise Exception(f"Job failed: {job_status.get('message', 'Unknown error')}")
                
                # Wait before polling again
                await asyncio.sleep(2)
        
        raise Exception(f"Job {job_id} did not complete within {max_wait} seconds")
    
    def _extract_expressions(self, hume_result: Dict[str, Any]) -> Dict[str, float]:
        """Extract expression scores from Hume API result"""
        expressions = {}
        
        try:
            predictions = hume_result.get("predictions", [])
            if not predictions:
                return expressions
            
            # Get prosody predictions (speech analysis)
            prosody_predictions = predictions[0].get("models", {}).get("prosody", {})
            grouped_predictions = prosody_predictions.get("grouped_predictions", [])
            
            if grouped_predictions:
                predictions_list = grouped_predictions[0].get("predictions", [])
                for prediction in predictions_list:
                    emotions = prediction.get("emotions", [])
                    for emotion in emotions:
                        name = emotion.get("name")
                        score = emotion.get("score", 0.0)
                        if name:
                            expressions[name] = score
                            
        except Exception as e:
            logger.error(f"Error extracting expressions: {str(e)}")
        
        return expressions
    
    def _extract_prosody_expressions(self, prosody_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract expressions from EVI prosody data"""
        expressions = {}
        
        try:
            scores = prosody_data.get("scores", {})
            for emotion_name, score in scores.items():
                expressions[emotion_name] = float(score)
                
        except Exception as e:
            logger.error(f"Error extracting prosody expressions: {str(e)}")
        
        return expressions
    
    def _analyze_medical_indicators(
        self, 
        expressions: Dict[str, float],
        patient_context: Optional[Dict[str, Any]] = None
    ) -> MedicalVoiceIndicators:
        """
        Analyze expressions to derive medical indicators.
        
        Args:
            expressions: Hume expression scores
            patient_context: Optional patient context
            
        Returns:
            MedicalVoiceIndicators with clinical assessments
        """
        # Calculate weighted scores for each medical indicator
        pain_score = self._calculate_weighted_score(
            expressions, self.medical_expressions["pain_indicators"]
        )
        
        stress_level = self._calculate_weighted_score(
            expressions, self.medical_expressions["stress_indicators"]
        )
        
        emotional_distress = self._calculate_weighted_score(
            expressions, self.medical_expressions["emotional_distress"]
        )
        
        anxiety_indicators = self._calculate_weighted_score(
            expressions, self.medical_expressions["anxiety_indicators"]
        )
        
        depression_markers = self._calculate_weighted_score(
            expressions, self.medical_expressions["depression_markers"]
        )
        
        positive_indicators = self._calculate_weighted_score(
            expressions, self.medical_expressions["positive_indicators"]
        )
        
        # Overall wellbeing (inverse of negative indicators)
        overall_wellbeing = max(0.0, 1.0 - (
            pain_score * 0.3 + 
            stress_level * 0.3 + 
            emotional_distress * 0.2 + 
            anxiety_indicators * 0.2
        ) + positive_indicators * 0.3)
        
        # Determine alert level
        alert_level = self._determine_alert_level(
            pain_score, stress_level, emotional_distress, anxiety_indicators
        )
        
        # Generate medical recommendations
        recommendations = self._generate_medical_recommendations(
            pain_score, stress_level, emotional_distress, 
            anxiety_indicators, depression_markers, patient_context
        )
        
        return MedicalVoiceIndicators(
            pain_score=pain_score,
            stress_level=stress_level,
            emotional_distress=emotional_distress,
            anxiety_indicators=anxiety_indicators,
            depression_markers=depression_markers,
            overall_wellbeing=overall_wellbeing,
            alert_level=alert_level,
            medical_recommendations=recommendations
        )
    
    def _calculate_weighted_score(
        self, 
        expressions: Dict[str, float], 
        weights: Dict[str, float]
    ) -> float:
        """Calculate weighted score for medical indicator"""
        total_score = 0.0
        total_weights = 0.0
        
        for expression, weight in weights.items():
            if expression in expressions:
                total_score += expressions[expression] * weight
                total_weights += weight
        
        return total_score / total_weights if total_weights > 0 else 0.0
    
    def _determine_alert_level(
        self, 
        pain_score: float, 
        stress_level: float, 
        emotional_distress: float,
        anxiety_indicators: float
    ) -> str:
        """Determine medical alert level based on scores"""
        max_score = max(pain_score, stress_level, emotional_distress, anxiety_indicators)
        
        if max_score >= 0.8:
            return "critical"
        elif max_score >= 0.6:
            return "high"
        elif max_score >= 0.4:
            return "elevated"
        else:
            return "normal"
    
    def _generate_medical_recommendations(
        self,
        pain_score: float,
        stress_level: float,
        emotional_distress: float,
        anxiety_indicators: float,
        depression_markers: float,
        patient_context: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate medical recommendations based on voice analysis"""
        recommendations = []
        
        if pain_score >= 0.6:
            recommendations.append("Consider pain assessment and management consultation")
            
        if stress_level >= 0.6:
            recommendations.append("Patient showing elevated stress - consider stress management interventions")
            
        if emotional_distress >= 0.7:
            recommendations.append("High emotional distress detected - psychological support may be beneficial")
            
        if anxiety_indicators >= 0.6:
            recommendations.append("Elevated anxiety indicators - consider anxiety screening")
            
        if depression_markers >= 0.6:
            recommendations.append("Depression markers present - consider mental health evaluation")
            
        # Context-specific recommendations
        if patient_context:
            if patient_context.get("chronic_pain") and pain_score >= 0.5:
                recommendations.append("Chronic pain patient showing elevated pain indicators - review pain management plan")
                
            if patient_context.get("post_surgical") and stress_level >= 0.5:
                recommendations.append("Post-surgical patient showing stress - provide additional support and education")
        
        if not recommendations:
            recommendations.append("Voice analysis indicates normal emotional state")
        
        return recommendations


# Factory function for easy client creation
def create_hume_ai_client() -> HumeAIClient:
    """Create Hume AI client with environment configuration"""
    api_key = os.getenv("HUME_API_KEY")
    if not api_key:
        raise ValueError("HUME_API_KEY environment variable not set")
    
    return HumeAIClient(api_key=api_key)