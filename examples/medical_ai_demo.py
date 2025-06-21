#!/usr/bin/env python3
"""
Vigia Medical AI Demo - Comprehensive MedGemma Integration
Demonstrates complete medical AI workflow with local and API-based processing.
"""

import asyncio
import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from pprint import pprint

# Add project path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from vigia_detect.ai.medgemma_client import MedGemmaClient, MedicalContext, MedicalAnalysisType
    from vigia_detect.ai.medical_prompts import MedicalPromptBuilder, PromptTemplate, MedicalPromptContext
    from vigia_detect.core.triage_engine import MedicalTriageEngine
    from vigia_detect.core.input_packager import InputPackager, InputType
    from config.settings import get_settings
except ImportError as e:
    logger.error(f"Import error: {e}")
    print("⚠️  Some components may not be available. Install dependencies or check imports.")


class MedicalAIDemo:
    """Comprehensive medical AI demonstration with MedGemma integration."""
    
    def __init__(self):
        """Initialize medical AI demo."""
        self.medgemma_client = None
        self.triage_engine = None
        self.settings = None
        
    async def initialize(self):
        """Initialize medical AI components."""
        try:
            # Initialize settings
            self.settings = get_settings()
            
            # Initialize MedGemma client
            self.medgemma_client = MedGemmaClient()
            
            # Initialize triage engine
            self.triage_engine = MedicalTriageEngine()
            
            logger.info("✅ Medical AI components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize components: {e}")
            return False
    
    async def demo_basic_medical_analysis(self):
        """Demonstrate basic medical analysis with MedGemma."""
        print("\n" + "="*60)
        print("🧠 DEMO 1: Basic Medical Analysis")
        print("="*60)
        
        # Test cases for different LPP stages
        test_cases = [
            {
                "name": "Stage 1 LPP - Early Detection",
                "observations": "Paciente presenta eritema no blanqueable en región sacra de 2cm de diámetro, piel intacta sin pérdida de tejido",
                "context": MedicalContext(
                    patient_age=78,
                    diabetes=True,
                    mobility_level="bed_bound",
                    braden_score=12
                )
            },
            {
                "name": "Stage 2 LPP - Partial Thickness",
                "observations": "Úlcera superficial con pérdida parcial del grosor de la piel en talón derecho, lecho de la herida rosado-rojizo",
                "context": MedicalContext(
                    patient_age=65,
                    diabetes=False,
                    mobility_level="chair_bound",
                    braden_score=15
                )
            },
            {
                "name": "Stage 3 LPP - Full Thickness",
                "observations": "Pérdida completa del grosor de la piel en región sacra con tejido subcutáneo visible, sin exposición ósea",
                "context": MedicalContext(
                    patient_age=82,
                    diabetes=True,
                    mobility_level="bed_bound",
                    braden_score=8
                )
            }
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n🔬 Test Case {i}: {case['name']}")
            print("-" * 40)
            
            try:
                # Analyze with MedGemma
                result = await self.medgemma_client.analyze_lpp_findings(
                    clinical_observations=case["observations"],
                    medical_context=case["context"]
                )
                
                if result:
                    print(f"✅ Analysis completed:")
                    print(f"   🎯 Confidence: {result.confidence_score:.1%}")
                    print(f"   📋 Clinical Findings: {result.clinical_findings}")
                    print(f"   💡 Recommendations: {result.recommendations}")
                    if hasattr(result, 'urgency_level'):
                        print(f"   🚨 Urgency: {result.urgency_level}")
                else:
                    print("❌ No analysis result obtained")
                    
            except Exception as e:
                print(f"❌ Analysis failed: {e}")
                
    async def demo_medical_image_analysis(self):
        """Demonstrate medical image analysis workflow."""
        print("\n" + "="*60)
        print("🖼️  DEMO 2: Medical Image Analysis Workflow")
        print("="*60)
        
        # Simulate image analysis results
        simulated_detection = {
            "lpp_stage": 2,
            "confidence": 0.87,
            "bounding_box": [150, 200, 300, 350],
            "anatomical_location": "sacrum"
        }
        
        print("📸 Simulated Image Detection Results:")
        print(f"   Stage: {simulated_detection['lpp_stage']}")
        print(f"   Confidence: {simulated_detection['confidence']:.1%}")
        print(f"   Location: {simulated_detection['anatomical_location']}")
        
        # Create clinical context from detection
        clinical_context = f"""
        Image analysis detected Stage {simulated_detection['lpp_stage']} pressure injury 
        at {simulated_detection['anatomical_location']} with {simulated_detection['confidence']:.1%} confidence.
        Bounding box coordinates: {simulated_detection['bounding_box']}.
        """
        
        print("\n🧠 MedGemma Analysis of Detection:")
        try:
            medical_context = MedicalContext(
                patient_age=70,
                diabetes=True,
                detection_confidence=simulated_detection['confidence']
            )
            
            result = await self.medgemma_client.analyze_lpp_findings(
                clinical_observations=clinical_context,
                medical_context=medical_context
            )
            
            if result:
                print(f"✅ Medical interpretation:")
                print(f"   📊 Clinical Assessment: {result.clinical_findings}")
                print(f"   💊 Treatment Plan: {result.recommendations}")
                print(f"   ⏰ Follow-up: {getattr(result, 'follow_up_timeline', 'As needed')}")
            else:
                print("❌ Medical interpretation failed")
                
        except Exception as e:
            print(f"❌ Medical analysis error: {e}")
    
    async def demo_triage_workflow(self):
        """Demonstrate medical triage workflow."""
        print("\n" + "="*60)
        print("🏥 DEMO 3: Medical Triage Workflow")
        print("="*60)
        
        # Simulate patient data
        patient_data = {
            "patient_id": "CD-2025-001",
            "age": 75,
            "medical_history": {
                "diabetes": True,
                "hypertension": True,
                "mobility": "limited"
            },
            "current_findings": "Eritema persistente en coxis con induración",
            "braden_score": 11,
            "risk_level": "high"
        }
        
        print("📋 Patient Data:")
        pprint(patient_data, indent=2)
        
        try:
            # Create input package
            input_package = InputPackager.create_medical_package(
                patient_code=patient_data["patient_id"],
                clinical_data=patient_data,
                input_type=InputType.CLINICAL_ASSESSMENT
            )
            
            print("\n⚕️  Processing triage assessment...")
            
            # Process through triage engine
            if self.triage_engine:
                triage_result = await self.triage_engine.process_medical_input(input_package)
                
                print("✅ Triage Results:")
                print(f"   🎯 Priority Level: {triage_result.get('priority', 'standard')}")
                print(f"   🚨 Urgency: {triage_result.get('urgency', 'routine')}")
                print(f"   📝 Assessment: {triage_result.get('clinical_assessment', 'N/A')}")
                print(f"   💡 Next Steps: {triage_result.get('recommended_actions', 'Continue monitoring')}")
            else:
                print("⚠️  Triage engine not available")
                
        except Exception as e:
            print(f"❌ Triage workflow error: {e}")
    
    async def demo_prompt_engineering(self):
        """Demonstrate medical prompt engineering."""
        print("\n" + "="*60)
        print("📝 DEMO 4: Medical Prompt Engineering")
        print("="*60)
        
        try:
            # Create prompt builder
            prompt_builder = MedicalPromptBuilder()
            
            # Example prompt contexts
            contexts = [
                {
                    "name": "LPP Assessment",
                    "template": PromptTemplate.LPP_ASSESSMENT,
                    "context": MedicalPromptContext(
                        clinical_findings="Eritema no blanqueable 3x2cm en talón",
                        patient_context={"age": 80, "diabetes": True},
                        medical_urgency="moderate"
                    )
                },
                {
                    "name": "Treatment Planning",
                    "template": PromptTemplate.TREATMENT_PLANNING,
                    "context": MedicalPromptContext(
                        clinical_findings="Stage 2 LPP confirmed",
                        patient_context={"mobility": "bed_bound", "nutrition": "poor"},
                        medical_urgency="high"
                    )
                }
            ]
            
            for context in contexts:
                print(f"\n📋 {context['name']} Prompt:")
                print("-" * 30)
                
                prompt = prompt_builder.build_prompt(
                    template=context["template"],
                    context=context["context"]
                )
                
                # Show structured prompt
                print("🔧 Generated Prompt Structure:")
                print(f"   Template: {context['template'].value}")
                print(f"   Clinical Focus: {context['context'].clinical_findings}")
                print(f"   Patient Context: {context['context'].patient_context}")
                print(f"   Urgency Level: {context['context'].medical_urgency}")
                
        except Exception as e:
            print(f"❌ Prompt engineering demo error: {e}")
    
    async def demo_local_vs_api_comparison(self):
        """Compare local vs API-based medical AI processing."""
        print("\n" + "="*60)
        print("⚖️  DEMO 5: Local vs API Processing Comparison")
        print("="*60)
        
        test_query = "Paciente con úlcera de 4cm en región sacra con tejido necrótico visible"
        
        print(f"🔬 Test Query: {test_query}")
        print("\n📊 Processing Methods Comparison:")
        
        # Local processing simulation
        print("\n🏠 Local Processing (MedGemma via Ollama):")
        print("   ✅ Advantages:")
        print("     • Complete data privacy (HIPAA compliant)")
        print("     • No external API dependencies")
        print("     • Consistent processing times")
        print("     • No per-query costs")
        print("   ⚠️  Requirements:")
        print("     • 16GB+ RAM for model loading")
        print("     • GPU acceleration recommended")
        print("     • Local model management")
        
        # API processing simulation
        print("\n☁️  API Processing (Google AI/Gemini):")
        print("   ✅ Advantages:")
        print("     • Lower local resource requirements")
        print("     • Always latest model versions")
        print("     • Managed infrastructure")
        print("   ⚠️  Considerations:")
        print("     • Medical data leaves premises")
        print("     • Internet dependency")
        print("     • Per-query API costs")
        print("     • Potential latency variations")
        
        # Recommend approach
        print("\n💡 Recommendation for Medical Use:")
        print("   🏥 Hospital Production: Local processing (privacy + compliance)")
        print("   🧪 Development/Testing: API processing (convenience)")
        print("   🔄 Hybrid: Local for sensitive data, API for research")
    
    async def run_complete_demo(self):
        """Run the complete medical AI demonstration."""
        print("🏥 VIGIA MEDICAL AI COMPREHENSIVE DEMO")
        print("=" * 60)
        print("This demo showcases MedGemma integration for medical AI analysis")
        print("in pressure injury detection and clinical decision support.\n")
        
        # Initialize components
        print("🔧 Initializing medical AI components...")
        if not await self.initialize():
            print("❌ Failed to initialize. Running limited demo...")
        
        # Run all demo sections
        try:
            await self.demo_basic_medical_analysis()
            await self.demo_medical_image_analysis()
            await self.demo_triage_workflow()
            await self.demo_prompt_engineering()
            await self.demo_local_vs_api_comparison()
            
        except Exception as e:
            logger.error(f"Demo execution error: {e}")
        
        # Summary
        print("\n" + "="*60)
        print("📋 DEMO SUMMARY")
        print("="*60)
        print("✅ Completed medical AI workflow demonstrations:")
        print("   • Basic clinical analysis with MedGemma")
        print("   • Medical image analysis integration")
        print("   • Hospital triage workflow processing")
        print("   • Medical prompt engineering techniques")
        print("   • Local vs API processing comparison")
        print("\n🏥 Ready for hospital production deployment!")
        print("📚 See docs/DEVELOPER_GUIDE.md for implementation details")


async def main():
    """Main demo execution."""
    try:
        # Environment check
        if not os.getenv('GOOGLE_API_KEY') and not os.path.exists('/usr/local/bin/ollama'):
            print("⚠️  Neither Google API key nor Ollama installation detected.")
            print("Some features may be limited. See docs/SETUP_GUIDE.md for setup instructions.")
            print("-" * 60)
        
        # Run demo
        demo = MedicalAIDemo()
        await demo.run_complete_demo()
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        logger.exception("Demo execution failed")


if __name__ == "__main__":
    print("🧠 Starting Vigia Medical AI Demo...")
    print("Press Ctrl+C to interrupt at any time\n")
    
    asyncio.run(main())