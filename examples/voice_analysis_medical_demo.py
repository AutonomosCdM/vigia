#!/usr/bin/env python3
"""
Voice Analysis Medical Demo
==========================

Demonstrates the VoiceAnalysisAgent capabilities for medical voice processing.
Shows how to analyze patient voice recordings for stress, pain, and emotional indicators.
"""

import asyncio
import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from vigia_detect.agents.adk.voice_analysis import VoiceAnalysisAgent, create_voice_analysis_agent
from vigia_detect.utils.shared_utilities import VigiaLogger

logger = VigiaLogger.get_logger(__name__)


class VoiceAnalysisMedicalDemo:
    """Demo class for voice analysis medical capabilities"""
    
    def __init__(self):
        """Initialize the demo"""
        self.agent = None
        
    async def initialize_agent(self):
        """Initialize the voice analysis agent"""
        try:
            logger.info("Initializing Voice Analysis Agent...")
            self.agent = create_voice_analysis_agent()
            logger.info("✅ Voice Analysis Agent initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize Voice Analysis Agent: {str(e)}")
            logger.info("💡 Make sure HUME_API_KEY environment variable is set")
            return False
    
    async def demo_voice_analysis_capabilities(self):
        """Demonstrate voice analysis capabilities"""
        if not self.agent:
            logger.error("Agent not initialized")
            return
        
        logger.info("🎯 Voice Analysis Agent Capabilities Demo")
        logger.info("=" * 60)
        
        # Demo 1: Mock voice analysis (since we don't have actual audio files)
        await self._demo_mock_voice_analysis()
        
        # Demo 2: Patient voice history
        await self._demo_patient_history()
        
        # Demo 3: Voice trend analysis
        await self._demo_voice_trends()
        
        # Demo 4: Medical interpretation
        await self._demo_medical_interpretation()
    
    async def _demo_mock_voice_analysis(self):
        """Demo voice analysis with mock data"""
        logger.info("\\n📊 Demo 1: Voice Analysis Processing")
        logger.info("-" * 40)
        
        # Mock patient contexts for different scenarios
        patient_scenarios = [
            {
                "patient_id": "PAT-001",
                "scenario": "Post-surgical patient",
                "context": {
                    "age": 65,
                    "post_surgical": True,
                    "surgery_type": "hip_replacement",
                    "days_post_surgery": 3,
                    "pain_medication": "opioids",
                    "mobility": "limited"
                },
                "mock_expressions": {
                    "Empathic Pain": 0.75,
                    "Anguish": 0.45,
                    "Anxiety": 0.60,
                    "Tiredness": 0.70,
                    "Stress": 0.55
                }
            },
            {
                "patient_id": "PAT-002",
                "scenario": "Chronic pain patient",
                "context": {
                    "age": 58,
                    "chronic_pain": True,
                    "condition": "fibromyalgia",
                    "pain_duration_years": 8,
                    "mental_health": "depression_history",
                    "pain_level": 7
                },
                "mock_expressions": {
                    "Empathic Pain": 0.85,
                    "Sadness": 0.70,
                    "Anxiety": 0.75,
                    "Depression": 0.65,
                    "Tiredness": 0.80
                }
            },
            {
                "patient_id": "PAT-003",
                "scenario": "Elderly patient with dementia",
                "context": {
                    "age": 82,
                    "dementia": True,
                    "dementia_stage": "moderate",
                    "confusion": True,
                    "anxiety": "frequent",
                    "family_support": True
                },
                "mock_expressions": {
                    "Confusion": 0.85,
                    "Anxiety": 0.70,
                    "Fear": 0.55,
                    "Sadness": 0.50,
                    "Distress": 0.60
                }
            }
        ]
        
        for i, scenario in enumerate(patient_scenarios, 1):
            logger.info(f"\\n  Scenario {i}: {scenario['scenario']}")
            logger.info(f"  Patient ID: {scenario['patient_id']}")
            
            # Simulate voice analysis result processing
            mock_result = self._create_mock_analysis_result(
                scenario["patient_id"],
                scenario["mock_expressions"],
                scenario["context"]
            )
            
            # Display analysis results
            logger.info(f"  📈 Medical Indicators:")
            medical_indicators = mock_result["medical_indicators"]
            logger.info(f"    • Pain Score: {medical_indicators['pain_score']:.2f}")
            logger.info(f"    • Stress Level: {medical_indicators['stress_level']:.2f}")
            logger.info(f"    • Emotional Distress: {medical_indicators['emotional_distress']:.2f}")
            logger.info(f"    • Alert Level: {medical_indicators['alert_level'].upper()}")
            
            logger.info(f"  💡 Recommendations:")
            for rec in medical_indicators["medical_recommendations"][:2]:  # Show first 2
                logger.info(f"    • {rec}")
            
            # Store in agent history (mock)
            if scenario["patient_id"] not in self.agent.patient_voice_history:
                self.agent.patient_voice_history[scenario["patient_id"]] = []
            
            self.agent.patient_voice_history[scenario["patient_id"]].append(mock_result)
    
    async def _demo_patient_history(self):
        """Demo patient voice history functionality"""
        logger.info("\\n📚 Demo 2: Patient Voice History")
        logger.info("-" * 40)
        
        for patient_id in ["PAT-001", "PAT-002", "PAT-003"]:
            history = await self.agent.get_patient_voice_history(patient_id)
            
            logger.info(f"\\n  Patient {patient_id}:")
            logger.info(f"    Total analyses: {len(history)}")
            
            if history:
                latest = history[-1]
                logger.info(f"    Latest analysis: {latest['timestamp']}")
                logger.info(f"    Alert level: {latest['clinical_interpretation']['alert_level']}")
    
    async def _demo_voice_trends(self):
        """Demo voice trend analysis"""
        logger.info("\\n📈 Demo 3: Voice Trend Analysis")
        logger.info("-" * 40)
        
        # Add some historical data points for trend analysis
        for patient_id in ["PAT-001", "PAT-002"]:
            # Add mock historical data
            await self._add_mock_historical_data(patient_id)
            
            try:
                trends = await self.agent.analyze_voice_trends(patient_id)
                
                logger.info(f"\\n  Patient {patient_id} Trends:")
                logger.info(f"    Data points: {trends['data_points']}")
                logger.info(f"    Pain trend: {trends['pain_trend']}")
                logger.info(f"    Stress trend: {trends['stress_trend']}")
                
            except Exception as e:
                logger.warning(f"    Trend analysis failed: {str(e)}")
    
    async def _demo_medical_interpretation(self):
        """Demo medical interpretation capabilities"""
        logger.info("\\n🩺 Demo 4: Medical Interpretation")
        logger.info("-" * 40)
        
        logger.info("\\n  Voice Analysis Medical Specialties:")
        logger.info("    • Stress detection through speech prosody")
        logger.info("    • Pain assessment via voice biomarkers")
        logger.info("    • Emotional distress identification")
        logger.info("    • Mental health screening via voice")
        logger.info("    • Patient monitoring and early warning systems")
        
        logger.info("\\n  Medical Decision Support:")
        logger.info("    • Evidence-based recommendations")
        logger.info("    • HIPAA-compliant voice processing")
        logger.info("    • Integration with patient medical context")
        logger.info("    • Automatic escalation for high-risk indicators")
        logger.info("    • Real-time streaming analysis capability")
        
        logger.info("\\n  Clinical Integration:")
        logger.info("    • A2A communication with other medical agents")
        logger.info("    • Medical alert generation")
        logger.info("    • Patient history tracking")
        logger.info("    • Trend analysis and longitudinal monitoring")
    
    def _create_mock_analysis_result(self, patient_id: str, expressions: dict, context: dict) -> dict:
        """Create mock analysis result"""
        from vigia_detect.ai.hume_ai_client import MedicalVoiceIndicators
        
        # Calculate medical indicators based on expressions
        pain_score = self._calculate_mock_score(expressions, ["Empathic Pain", "Anguish"])
        stress_level = self._calculate_mock_score(expressions, ["Anxiety", "Stress"])
        emotional_distress = self._calculate_mock_score(expressions, ["Sadness", "Distress"])
        
        # Determine alert level
        max_score = max(pain_score, stress_level, emotional_distress)
        if max_score >= 0.8:
            alert_level = "critical"
        elif max_score >= 0.6:
            alert_level = "high"
        elif max_score >= 0.4:
            alert_level = "elevated"
        else:
            alert_level = "normal"
        
        # Generate recommendations
        recommendations = []
        if pain_score >= 0.6:
            recommendations.append("Consider pain assessment and management consultation")
        if stress_level >= 0.6:
            recommendations.append("Patient showing elevated stress - consider stress management interventions")
        if emotional_distress >= 0.7:
            recommendations.append("High emotional distress detected - psychological support may be beneficial")
        
        # Context-specific recommendations
        if context.get("chronic_pain") and pain_score >= 0.5:
            recommendations.append("Chronic pain patient showing elevated pain indicators - review pain management plan")
        if context.get("post_surgical") and stress_level >= 0.5:
            recommendations.append("Post-surgical patient showing stress - provide additional support and education")
        
        medical_indicators = {
            "pain_score": pain_score,
            "stress_level": stress_level,
            "emotional_distress": emotional_distress,
            "anxiety_indicators": self._calculate_mock_score(expressions, ["Anxiety", "Fear"]),
            "depression_markers": self._calculate_mock_score(expressions, ["Sadness", "Depression"]),
            "overall_wellbeing": max(0.0, 1.0 - max_score),
            "alert_level": alert_level,
            "medical_recommendations": recommendations
        }
        
        return {
            "patient_id": patient_id,
            "analysis_id": f"voice_analysis_{int(datetime.now().timestamp())}",
            "timestamp": datetime.now().isoformat(),
            "technical_analysis": {
                "expressions": expressions,
                "medical_indicators": medical_indicators,
                "processing_time": 2.5
            },
            "clinical_interpretation": {
                "confidence_level": 0.85,
                "alert_level": alert_level,
                "recommendations": recommendations
            },
            "medical_context": context
        }
    
    def _calculate_mock_score(self, expressions: dict, target_expressions: list) -> float:
        """Calculate weighted score for specific expressions"""
        total_score = 0.0
        count = 0
        
        for expr in target_expressions:
            if expr in expressions:
                total_score += expressions[expr]
                count += 1
        
        return total_score / count if count > 0 else 0.0
    
    async def _add_mock_historical_data(self, patient_id: str):
        """Add mock historical data for trend analysis"""
        import random
        
        # Add 3 additional historical points
        for i in range(3):
            # Vary the scores slightly for trend analysis
            base_pain = 0.6 + (i * 0.05) + random.uniform(-0.1, 0.1)
            base_stress = 0.55 + (i * 0.03) + random.uniform(-0.1, 0.1)
            
            mock_expressions = {
                "Empathic Pain": max(0.0, min(1.0, base_pain)),
                "Anxiety": max(0.0, min(1.0, base_stress)),
                "Sadness": max(0.0, min(1.0, 0.4 + random.uniform(-0.1, 0.1)))
            }
            
            result = self._create_mock_analysis_result(
                patient_id,
                mock_expressions,
                {"historical_data_point": i + 1}
            )
            
            # Adjust timestamp to be in the past
            result["timestamp"] = datetime.now().replace(hour=datetime.now().hour - (i + 1)).isoformat()
            
            self.agent.patient_voice_history[patient_id].append(result)


async def main():
    """Main demo function"""
    demo = VoiceAnalysisMedicalDemo()
    
    logger.info("🎙️ Vigia Voice Analysis Medical Demo")
    logger.info("=" * 80)
    
    # Initialize the agent
    if not await demo.initialize_agent():
        logger.error("❌ Failed to initialize agent. Demo cannot continue.")
        logger.info("💡 To run with Hume AI integration:")
        logger.info("   export HUME_API_KEY='your_hume_api_key'")
        logger.info("   python examples/voice_analysis_medical_demo.py")
        return
    
    # Run the demo
    await demo.demo_voice_analysis_capabilities()
    
    logger.info("\\n" + "=" * 80)
    logger.info("🎉 Voice Analysis Medical Demo completed successfully!")
    logger.info("\\n📋 Summary:")
    logger.info("  • Voice Analysis Agent provides empathic AI voice processing")
    logger.info("  • Hume AI integration for 48 vocal expression dimensions")
    logger.info("  • Medical interpretation of voice patterns")
    logger.info("  • Patient monitoring and trend analysis")
    logger.info("  • HIPAA-compliant voice processing")
    logger.info("  • A2A integration with other medical agents")


if __name__ == "__main__":
    asyncio.run(main())