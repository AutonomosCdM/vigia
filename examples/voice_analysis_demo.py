#!/usr/bin/env python3
"""
Hume AI Voice Analysis Demo
===========================

Demonstration of voice analysis capabilities for stress and pain detection.
Shows integration between Hume AI, medical analysis, and Slack notifications.
"""

import asyncio
import json
import tempfile
import wave
import numpy as np
from datetime import datetime
from pathlib import Path
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vigia_detect.agents.adk.voice_analysis import create_voice_analysis_agent
from vigia_detect.agents.adk.slack_block_kit import create_slack_block_kit_agent
from vigia_detect.ai.hume_ai_client import create_hume_ai_client
from vigia_detect.systems.voice_medical_analysis import create_voice_medical_analysis_engine


def create_synthetic_audio_file(duration_seconds: float = 5.0, sample_rate: int = 16000) -> str:
    """
    Create synthetic audio file for demonstration.
    
    Args:
        duration_seconds: Duration of audio
        sample_rate: Audio sample rate
        
    Returns:
        Path to created audio file
    """
    # Generate synthetic audio with varying frequencies to simulate speech
    samples = int(duration_seconds * sample_rate)
    t = np.linspace(0, duration_seconds, samples)
    
    # Create synthetic "stressed" speech pattern
    # Mix multiple frequencies to simulate complex speech
    audio_data = (
        0.3 * np.sin(2 * np.pi * 200 * t) +  # Base frequency
        0.2 * np.sin(2 * np.pi * 400 * t) +  # Higher frequency  
        0.1 * np.sin(2 * np.pi * 800 * t) +  # Even higher
        0.1 * np.random.normal(0, 0.1, samples)  # Add noise for realism
    )
    
    # Add stress-like modulation (tremor effect)
    tremor = 0.05 * np.sin(2 * np.pi * 5 * t)  # 5 Hz tremor
    audio_data = audio_data * (1 + tremor)
    
    # Normalize to 16-bit range
    audio_data = np.clip(audio_data, -1.0, 1.0)
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Create temporary WAV file
    temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    
    with wave.open(temp_file.name, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    return temp_file.name


async def demo_voice_analysis():
    """Demonstrate voice analysis capabilities"""
    print("🎤 Hume AI Voice Analysis Demo - Vigia Medical System")
    print("=" * 60)
    
    # Check if Hume AI API key is available
    hume_api_key = os.getenv("HUME_API_KEY")
    if not hume_api_key:
        print("⚠️  HUME_API_KEY not found in environment")
        print("   Using simulated results for demonstration")
        use_real_api = False
    else:
        print(f"✅ Hume AI API key found: {hume_api_key[:8]}***")
        use_real_api = True
    
    print()
    
    # Create synthetic audio file
    print("🔊 Creating synthetic audio file...")
    audio_file_path = create_synthetic_audio_file(duration_seconds=3.0)
    print(f"   Audio file created: {audio_file_path}")
    print()
    
    # Patient context for demonstration
    patient_context = {
        "patient_id": "PAT-DEMO-001",
        "age": 68,
        "chronic_pain": True,
        "diabetes": True,
        "recent_surgery": False,
        "anxiety_disorder": False
    }
    
    print("👤 Patient Context:")
    for key, value in patient_context.items():
        print(f"   {key}: {value}")
    print()
    
    try:
        if use_real_api:
            # Real Hume AI analysis
            print("🧠 Initializing Hume AI client...")
            hume_client = create_hume_ai_client()
            
            print("🎵 Analyzing voice with Hume AI...")
            async with hume_client as client:
                voice_result = await client.analyze_voice_file(
                    audio_file_path=audio_file_path,
                    patient_context=patient_context
                )
            
            print("✅ Hume AI analysis completed")
            print(f"   Processing time: {voice_result.processing_time:.2f} seconds")
            print(f"   Expressions detected: {len(voice_result.expressions)}")
            print()
            
        else:
            # Simulated results for demonstration
            print("🔄 Simulating Hume AI analysis...")
            
            # Create simulated voice analysis result
            from vigia_detect.ai.hume_ai_client import VoiceAnalysisResult
            
            voice_result = VoiceAnalysisResult(
                request_id=f"demo_{int(datetime.now().timestamp())}",
                timestamp=datetime.now(),
                expressions={
                    "Empathic Pain": 0.75,
                    "Anxiety": 0.68,
                    "Sadness": 0.45,
                    "Fear": 0.52,
                    "Tiredness": 0.63,
                    "Stress": 0.71,
                    "Confusion": 0.38,
                    "Distress": 0.59,
                    "Joy": 0.12,
                    "Calmness": 0.08
                },
                medical_indicators={
                    "pain_score": 0.73,
                    "stress_level": 0.67,
                    "emotional_distress": 0.54,
                    "anxiety_indicators": 0.65,
                    "depression_markers": 0.42,
                    "overall_wellbeing": 0.31,
                    "alert_level": "high",
                    "medical_recommendations": [
                        "Elevated pain indicators - immediate assessment recommended",
                        "High stress levels detected - stress management intervention needed",
                        "Consider psychological support for emotional distress"
                    ]
                },
                raw_hume_response={"simulation": True},
                processing_time=1.5
            )
            
            print("✅ Simulated analysis completed")
            print()
        
        # Create voice analysis agent
        print("🤖 Initializing Voice Analysis Agent...")
        voice_agent = create_voice_analysis_agent()
        
        # Process results with medical interpretation
        print("🏥 Processing medical interpretation...")
        if use_real_api:
            comprehensive_result = await voice_agent.process_voice_file(
                audio_file_path=audio_file_path,
                patient_id=patient_context["patient_id"],
                patient_context=patient_context
            )
        else:
            # Create simulated comprehensive result
            comprehensive_result = {
                "patient_id": patient_context["patient_id"],
                "analysis_id": voice_result.request_id,
                "timestamp": voice_result.timestamp.isoformat(),
                "technical_analysis": {
                    "expressions": voice_result.expressions,
                    "medical_indicators": voice_result.medical_indicators,
                    "processing_time": voice_result.processing_time
                },
                "clinical_interpretation": {
                    "llm_assessment": "Clinical assessment indicates elevated pain and stress levels. Patient shows significant empathic pain response (0.75) and high anxiety markers (0.68). Given the patient's chronic pain history, these findings suggest inadequate pain management and psychological distress requiring immediate medical attention.",
                    "confidence_level": 0.82,
                    "alert_level": "high",
                    "recommendations": voice_result.medical_indicators["medical_recommendations"]
                },
                "medical_context": patient_context
            }
        
        print("✅ Medical interpretation completed")
        print()
        
        # Display analysis results
        print("📊 Voice Analysis Results")
        print("-" * 30)
        
        technical = comprehensive_result["technical_analysis"]
        clinical = comprehensive_result["clinical_interpretation"]
        
        print(f"🆔 Analysis ID: {comprehensive_result['analysis_id']}")
        print(f"⏰ Timestamp: {comprehensive_result['timestamp']}")
        print(f"🎯 Confidence: {clinical['confidence_level']:.2f}")
        print(f"🚨 Alert Level: {clinical['alert_level'].upper()}")
        print()
        
        print("🧠 Expression Scores:")
        expressions = technical["expressions"]
        sorted_expressions = sorted(expressions.items(), key=lambda x: x[1], reverse=True)
        
        for expression, score in sorted_expressions[:10]:  # Top 10
            bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
            print(f"   {expression:20} │{bar}│ {score:.3f}")
        print()
        
        print("🏥 Medical Indicators:")
        medical_indicators = technical["medical_indicators"]
        indicators = [
            ("Pain Score", medical_indicators["pain_score"]),
            ("Stress Level", medical_indicators["stress_level"]),
            ("Emotional Distress", medical_indicators["emotional_distress"]),
            ("Anxiety Indicators", medical_indicators["anxiety_indicators"]),
            ("Depression Markers", medical_indicators["depression_markers"]),
            ("Overall Wellbeing", medical_indicators["overall_wellbeing"])
        ]
        
        for indicator, score in indicators:
            bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
            color = "🔴" if score >= 0.7 else "🟡" if score >= 0.4 else "🟢"
            print(f"   {indicator:20} │{color}{bar}│ {score:.3f}")
        print()
        
        print("💡 Clinical Assessment:")
        assessment_lines = clinical["llm_assessment"].split(". ")
        for line in assessment_lines:
            if line.strip():
                print(f"   • {line.strip()}.")
        print()
        
        print("📋 Medical Recommendations:")
        for i, recommendation in enumerate(clinical["recommendations"], 1):
            print(f"   {i}. {recommendation}")
        print()
        
        # Generate Slack notification
        print("📱 Generating Slack Block Kit notification...")
        slack_agent = create_slack_block_kit_agent()
        tools = slack_agent._create_adk_tools()
        
        slack_blocks = tools["generate_voice_analysis_alert_blocks"](
            comprehensive_result,
            patient_context
        )
        
        print("✅ Slack notification generated")
        print()
        
        print("📱 Slack Block Kit Preview:")
        print("-" * 30)
        
        # Display a simplified version of the Slack blocks
        blocks = slack_blocks["blocks"]
        for block in blocks[:3]:  # Show first 3 blocks
            if block["type"] == "header":
                print(f"📌 {block['text']['text']}")
            elif block["type"] == "section":
                if "text" in block:
                    text = block["text"]["text"].replace("*", "").replace("\n", " ")
                    print(f"📄 {text[:100]}...")
        print()
        
        # Save results for inspection
        results_file = f"voice_analysis_demo_results_{int(datetime.now().timestamp())}.json"
        with open(results_file, 'w') as f:
            json.dump({
                "comprehensive_result": comprehensive_result,
                "slack_blocks": slack_blocks
            }, f, indent=2, default=str)
        
        print(f"💾 Results saved to: {results_file}")
        print()
        
        # Voice trend analysis simulation
        print("📈 Voice Trend Analysis Demo...")
        
        # Simulate historical data
        voice_agent.patient_voice_history[patient_context["patient_id"]] = [
            {
                "timestamp": "2024-01-01T10:00:00",
                "technical_analysis": {
                    "medical_indicators": {
                        "pain_score": 0.4,
                        "stress_level": 0.3
                    }
                }
            },
            {
                "timestamp": "2024-01-02T10:00:00",
                "technical_analysis": {
                    "medical_indicators": {
                        "pain_score": 0.6,
                        "stress_level": 0.5
                    }
                }
            },
            comprehensive_result  # Current analysis
        ]
        
        if use_real_api:
            trend_analysis = await voice_agent.analyze_voice_trends(patient_context["patient_id"])
        else:
            # Simulated trend analysis
            trend_analysis = {
                "patient_id": patient_context["patient_id"],
                "trend_analysis": "Voice analysis shows a concerning upward trend in both pain and stress indicators over the past 3 recordings. Pain scores have increased from 0.4 to 0.73, and stress levels from 0.3 to 0.67. This suggests inadequate pain management and increasing psychological distress. Immediate medical intervention is recommended.",
                "data_points": 3,
                "pain_trend": "increasing",
                "stress_trend": "increasing"
            }
        
        print("✅ Trend analysis completed")
        print()
        
        print("📊 Trend Analysis Results:")
        print(f"   Data Points: {trend_analysis['data_points']}")
        print(f"   Pain Trend: {trend_analysis['pain_trend']} 📈")
        print(f"   Stress Trend: {trend_analysis['stress_trend']} 📈")
        print()
        
        print("🔍 Trend Interpretation:")
        trend_lines = trend_analysis["trend_analysis"].split(". ")
        for line in trend_lines:
            if line.strip():
                print(f"   • {line.strip()}.")
        print()
        
        print("🎉 Voice Analysis Demo Completed Successfully!")
        print("=" * 60)
        
        if not use_real_api:
            print()
            print("📝 Note: This demo used simulated results.")
            print("   Set HUME_API_KEY environment variable for real API integration.")
        
    except Exception as e:
        print(f"❌ Error during voice analysis demo: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            os.unlink(audio_file_path)
            print(f"🧹 Cleaned up temporary audio file")
        except:
            pass


async def demo_medical_analysis_engine():
    """Demonstrate medical analysis engine capabilities"""
    print("\n🏥 Medical Analysis Engine Demo")
    print("-" * 40)
    
    # Create medical analysis engine
    engine = create_voice_medical_analysis_engine()
    
    # Sample voice expressions with high pain/stress indicators
    sample_expressions = {
        "Empathic Pain": 0.85,
        "Anxiety": 0.78,
        "Anguish": 0.72,
        "Fear": 0.65,
        "Sadness": 0.58,
        "Distress": 0.69,
        "Tiredness": 0.63,
        "Confusion": 0.45,
        "Joy": 0.08,
        "Calmness": 0.05
    }
    
    patient_context = {
        "age": 72,
        "chronic_pain": True,
        "diabetes": True,
        "hospital_setting": True
    }
    
    print("🧪 Analyzing voice expressions...")
    assessment = engine.analyze_patient_voice(
        sample_expressions,
        patient_context,
        "PAT-DEMO-002"
    )
    
    print("✅ Medical assessment completed")
    print()
    
    print("📋 Medical Assessment Summary:")
    print(f"   Patient ID: {assessment.patient_id}")
    print(f"   Urgency Level: {assessment.urgency_level.value.upper()}")
    print(f"   Evidence Level: {assessment.evidence_level.level}")
    print(f"   Confidence: {assessment.evidence_level.confidence:.2f}")
    print(f"   Follow-up Required: {assessment.follow_up_required}")
    if assessment.follow_up_timeframe:
        print(f"   Follow-up Timeframe: {assessment.follow_up_timeframe}")
    if assessment.specialist_referral:
        print(f"   Specialist Referral: {assessment.specialist_referral}")
    print()
    
    print("🔍 Primary Concerns:")
    for concern in assessment.primary_concerns:
        print(f"   • {concern}")
    print()
    
    print("💊 Medical Recommendations:")
    for recommendation in assessment.medical_recommendations:
        print(f"   • {recommendation}")
    print()
    
    print("📊 Pain Assessment:")
    pain = assessment.pain_assessment
    print(f"   Overall Pain Score: {pain['overall_pain_score']:.3f}")
    print(f"   Pain Level: {pain['pain_level']}")
    print()
    
    print("😰 Stress Evaluation:")
    stress = assessment.stress_evaluation
    print(f"   Overall Stress Score: {stress['overall_stress_score']:.3f}")
    print(f"   Stress Level: {stress['stress_level']}")
    print()


if __name__ == "__main__":
    # Set up basic configuration
    import logging
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 Starting Hume AI Voice Analysis Demonstration")
    print()
    
    # Run main demo
    asyncio.run(demo_voice_analysis())
    
    # Run medical analysis engine demo
    asyncio.run(demo_medical_analysis_engine())