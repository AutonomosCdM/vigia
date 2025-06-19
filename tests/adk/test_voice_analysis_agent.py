"""
Test Voice Analysis Agent - ADK Integration Tests
===============================================

Comprehensive tests for voice analysis agent functionality.
Tests Hume AI integration, medical interpretation, and clinical workflows.
"""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from typing import Dict, Any

from vigia_detect.agents.adk.voice_analysis import (
    VoiceAnalysisAgent,
    VoiceAnalysisTool,
    StreamingVoiceAnalysisTool,
    create_voice_analysis_agent
)
from vigia_detect.ai.hume_ai_client import VoiceAnalysisResult, MedicalVoiceIndicators
from vigia_detect.systems.voice_medical_analysis import VoiceMedicalAnalysisEngine


class TestVoiceAnalysisAgent:
    """Test suite for Voice Analysis Agent"""
    
    @pytest.fixture
    def mock_hume_client(self):
        """Mock Hume AI client"""
        client = Mock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        return client
    
    @pytest.fixture
    def sample_voice_analysis_result(self):
        """Sample voice analysis result"""
        return VoiceAnalysisResult(
            request_id="test_analysis_001",
            timestamp=datetime.now(),
            expressions={
                "Empathic Pain": 0.7,
                "Anxiety": 0.6,
                "Sadness": 0.5,
                "Stress": 0.4,
                "Calm": 0.2
            },
            medical_indicators={
                "pain_score": 0.7,
                "stress_level": 0.6,
                "emotional_distress": 0.5,
                "anxiety_indicators": 0.6,
                "depression_markers": 0.3,
                "overall_wellbeing": 0.4,
                "alert_level": "elevated",
                "medical_recommendations": [
                    "Consider pain assessment and management consultation",
                    "Patient showing elevated stress - consider stress management interventions"
                ]
            },
            raw_hume_response={"test": "data"},
            processing_time=2.5
        )
    
    @pytest.fixture
    def sample_patient_context(self):
        """Sample patient context"""
        return {
            "patient_id": "PAT-001",
            "age": 65,
            "chronic_pain": True,
            "diabetes": True,
            "recent_surgery": False
        }
    
    @pytest.fixture
    def voice_analysis_agent(self, mock_hume_client):
        """Create voice analysis agent with mocked client"""
        with patch('vigia_detect.agents.adk.voice_analysis.create_hume_ai_client') as mock_create:
            mock_create.return_value = mock_hume_client
            agent = VoiceAnalysisAgent()
            return agent
    
    def test_agent_initialization(self, voice_analysis_agent):
        """Test agent initialization"""
        assert voice_analysis_agent.agent_id == "voice_analysis_agent"
        assert voice_analysis_agent.agent_name == "Voice Analysis Agent"
        assert "voice_analysis" in voice_analysis_agent.medical_specialties
        assert "stress_detection" in voice_analysis_agent.medical_specialties
        assert "pain_assessment" in voice_analysis_agent.medical_specialties
    
    @pytest.mark.asyncio
    async def test_process_voice_file(
        self, 
        voice_analysis_agent, 
        sample_voice_analysis_result,
        sample_patient_context,
        mock_hume_client
    ):
        """Test processing voice file"""
        # Setup mock
        mock_hume_client.analyze_voice_file = AsyncMock(return_value=sample_voice_analysis_result)
        
        # Mock LLM response
        mock_llm_response = Mock()
        mock_llm_response.content = "Clinical assessment: Elevated pain and stress indicators detected. Recommend immediate evaluation."
        
        with patch.object(voice_analysis_agent, 'generate_response', return_value=mock_llm_response):
            # Test processing
            result = await voice_analysis_agent.process_voice_file(
                audio_file_path="/test/audio.wav",
                patient_id="PAT-001",
                patient_context=sample_patient_context
            )
        
        # Verify result structure
        assert result["patient_id"] == "PAT-001"
        assert result["analysis_id"] == "test_analysis_001"
        assert "technical_analysis" in result
        assert "clinical_interpretation" in result
        
        # Verify technical analysis
        technical = result["technical_analysis"]
        assert technical["expressions"]["Empathic Pain"] == 0.7
        assert technical["medical_indicators"]["pain_score"] == 0.7
        assert technical["medical_indicators"]["alert_level"] == "elevated"
        
        # Verify clinical interpretation
        clinical = result["clinical_interpretation"]
        assert "Clinical assessment" in clinical["llm_assessment"]
        assert clinical["alert_level"] == "elevated"
        assert len(clinical["recommendations"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_patient_voice_history(self, voice_analysis_agent):
        """Test getting patient voice history"""
        # Add test data to history
        test_history_item = {
            "patient_id": "PAT-001",
            "analysis_id": "test_001",
            "timestamp": datetime.now().isoformat()
        }
        
        voice_analysis_agent.patient_voice_history["PAT-001"] = [test_history_item]
        
        # Get history
        history = await voice_analysis_agent.get_patient_voice_history("PAT-001")
        
        assert len(history) == 1
        assert history[0]["analysis_id"] == "test_001"
    
    @pytest.mark.asyncio
    async def test_analyze_voice_trends(self, voice_analysis_agent):
        """Test voice trend analysis"""
        # Setup test history with multiple entries
        test_history = [
            {
                "timestamp": "2024-01-01T10:00:00",
                "technical_analysis": {
                    "medical_indicators": {
                        "pain_score": 0.3,
                        "stress_level": 0.4
                    }
                }
            },
            {
                "timestamp": "2024-01-02T10:00:00", 
                "technical_analysis": {
                    "medical_indicators": {
                        "pain_score": 0.6,
                        "stress_level": 0.7
                    }
                }
            }
        ]
        
        voice_analysis_agent.patient_voice_history["PAT-001"] = test_history
        
        # Mock LLM response
        mock_llm_response = Mock()
        mock_llm_response.content = "Voice trend analysis shows increasing pain and stress levels over time."
        
        with patch.object(voice_analysis_agent, 'generate_response', return_value=mock_llm_response):
            # Test trend analysis
            result = await voice_analysis_agent.analyze_voice_trends("PAT-001")
        
        assert result["patient_id"] == "PAT-001"
        assert result["data_points"] == 2
        assert result["pain_trend"] == "increasing"
        assert result["stress_trend"] == "increasing"
        assert "Voice trend analysis" in result["trend_analysis"]
    
    @pytest.mark.asyncio
    async def test_analyze_voice_trends_insufficient_data(self, voice_analysis_agent):
        """Test trend analysis with insufficient data"""
        # Setup minimal history
        voice_analysis_agent.patient_voice_history["PAT-001"] = []
        
        result = await voice_analysis_agent.analyze_voice_trends("PAT-001")
        
        assert "Insufficient data" in result["trend_analysis"]
        assert "Collect more voice samples" in result["recommendation"]
    
    def test_calculate_confidence(self, voice_analysis_agent, sample_voice_analysis_result):
        """Test confidence calculation"""
        confidence = voice_analysis_agent._calculate_confidence(sample_voice_analysis_result)
        
        assert 0.0 <= confidence <= 1.0
        assert isinstance(confidence, float)
    
    @pytest.mark.asyncio
    async def test_check_voice_alerts_high_priority(self, voice_analysis_agent):
        """Test voice alert checking for high priority cases"""
        # Create high priority analysis result
        high_priority_result = {
            "patient_id": "PAT-001",
            "clinical_interpretation": {
                "alert_level": "high"
            }
        }
        
        with patch.object(voice_analysis_agent, '_trigger_medical_alert') as mock_trigger:
            await voice_analysis_agent._check_voice_alerts(high_priority_result)
            mock_trigger.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_check_voice_alerts_normal_priority(self, voice_analysis_agent):
        """Test voice alert checking for normal priority cases"""
        # Create normal priority analysis result
        normal_result = {
            "patient_id": "PAT-001",
            "clinical_interpretation": {
                "alert_level": "normal"
            }
        }
        
        with patch.object(voice_analysis_agent, '_trigger_medical_alert') as mock_trigger:
            await voice_analysis_agent._check_voice_alerts(normal_result)
            mock_trigger.assert_not_called()


class TestVoiceAnalysisTool:
    """Test suite for Voice Analysis Tool"""
    
    @pytest.fixture
    def mock_hume_client(self):
        """Mock Hume AI client"""
        client = Mock()
        client.__aenter__ = AsyncMock(return_value=client)
        client.__aexit__ = AsyncMock(return_value=None)
        return client
    
    @pytest.fixture
    def voice_analysis_tool(self, mock_hume_client):
        """Create voice analysis tool"""
        return VoiceAnalysisTool(mock_hume_client)
    
    @pytest.fixture
    def mock_agent_context(self):
        """Mock agent context"""
        context = Mock()
        return context
    
    @pytest.mark.asyncio
    async def test_tool_execution_success(
        self, 
        voice_analysis_tool, 
        mock_agent_context,
        mock_hume_client
    ):
        """Test successful tool execution"""
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(b"fake audio data")
            temp_audio_path = temp_file.name
        
        try:
            # Mock successful analysis
            mock_result = VoiceAnalysisResult(
                request_id="test_001",
                timestamp=datetime.now(),
                expressions={"Anxiety": 0.6},
                medical_indicators={"stress_level": 0.6},
                raw_hume_response={},
                processing_time=1.0
            )
            
            mock_hume_client.analyze_voice_file = AsyncMock(return_value=mock_result)
            
            # Execute tool
            result = await voice_analysis_tool.execute(
                context=mock_agent_context,
                audio_file_path=temp_audio_path,
                patient_context={"age": 50}
            )
            
            assert result["success"] is True
            assert "analysis_result" in result
            assert result["analysis_result"]["request_id"] == "test_001"
            
        finally:
            # Cleanup
            os.unlink(temp_audio_path)
    
    @pytest.mark.asyncio
    async def test_tool_execution_missing_file(self, voice_analysis_tool, mock_agent_context):
        """Test tool execution with missing audio file"""
        result = await voice_analysis_tool.execute(
            context=mock_agent_context,
            audio_file_path="/nonexistent/file.wav"
        )
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_tool_execution_missing_path(self, voice_analysis_tool, mock_agent_context):
        """Test tool execution without audio file path"""
        result = await voice_analysis_tool.execute(
            context=mock_agent_context
        )
        
        assert result["success"] is False
        assert "audio_file_path is required" in result["error"]


class TestStreamingVoiceAnalysisTool:
    """Test suite for Streaming Voice Analysis Tool"""
    
    @pytest.fixture
    def mock_hume_client(self):
        """Mock Hume AI client"""
        return Mock()
    
    @pytest.fixture
    def streaming_tool(self, mock_hume_client):
        """Create streaming voice analysis tool"""
        return StreamingVoiceAnalysisTool(mock_hume_client)
    
    @pytest.fixture
    def mock_agent_context(self):
        """Mock agent context"""
        return Mock()
    
    @pytest.mark.asyncio
    async def test_streaming_tool_execution(self, streaming_tool, mock_agent_context):
        """Test streaming tool execution"""
        result = await streaming_tool.execute(
            context=mock_agent_context,
            stream_duration=30,
            patient_context={"age": 40}
        )
        
        assert result["success"] is True
        assert "Streaming voice analysis capability available" in result["message"]


class TestVoiceAnalysisIntegration:
    """Integration tests for voice analysis system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_voice_analysis(self):
        """Test end-to-end voice analysis workflow"""
        # This would test the complete flow from audio input to medical recommendations
        # In a real scenario, this would use actual audio files and API calls
        pass
    
    def test_factory_function(self):
        """Test factory function for agent creation"""
        with patch('vigia_detect.agents.adk.voice_analysis.create_hume_ai_client'):
            agent = create_voice_analysis_agent()
            assert isinstance(agent, VoiceAnalysisAgent)
    
    @pytest.mark.asyncio
    async def test_voice_analysis_with_medical_context(self):
        """Test voice analysis with various medical contexts"""
        contexts = [
            {"chronic_pain": True, "age": 70},
            {"recent_surgery": True, "post_surgical": True},
            {"anxiety_disorder": True, "mental_health_history": True},
            {"diabetes": True, "hypertension": True}
        ]
        
        for context in contexts:
            # Test that different contexts are handled appropriately
            # This would involve testing the medical analysis engine
            pass


# Pytest markers for test organization
pytestmark = [
    pytest.mark.adk,
    pytest.mark.voice_analysis,
    pytest.mark.hume_ai
]


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])