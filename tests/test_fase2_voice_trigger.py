#!/usr/bin/env python3
"""
Test FASE 2 Voice + Image Trigger Integration
===========================================

Test script to validate the complete FASE 2 multimodal trigger system
with Bruce Wayne case including voice analysis integration.

This tests:
1. Medical Dispatcher multimodal routing
2. Master Orchestrator voice analysis coordination  
3. FASE 2 completion handler
4. Batman tokenization throughout the pipeline
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the enhanced components
from vigia_detect.core.medical_dispatcher import MedicalDispatcher, ProcessingRoute
from vigia_detect.agents.master_medical_orchestrator import MasterMedicalOrchestrator
from vigia_detect.webhook.handlers import WebhookHandlers
from vigia_detect.webhook.models import EventType


class FASE2VoiceTriggerTest:
    """Test suite for FASE 2 voice trigger integration"""
    
    def __init__(self):
        self.dispatcher = None
        self.orchestrator = None
        self.webhook_handlers = None
        
    async def setup(self):
        """Initialize test components"""
        logger.info("🔧 Setting up FASE 2 voice trigger test environment...")
        
        # Initialize dispatcher
        self.dispatcher = MedicalDispatcher()
        await self.dispatcher.initialize()
        
        # Initialize orchestrator
        self.orchestrator = MasterMedicalOrchestrator()
        await self.orchestrator.initialize()
        
        # Initialize webhook handlers
        self.webhook_handlers = WebhookHandlers()
        
        logger.info("✅ Test environment setup complete")
    
    def create_bruce_wayne_multimodal_case(self) -> Dict[str, Any]:
        """Create Bruce Wayne test case with image + voice data"""
        
        # Simulate audio data (base64 encoded mock)
        mock_audio_data = "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="  # Mock WAV header
        
        return {
            'session_id': 'test_session_bw_001',
            'token_id': 'batman_token_001',  # Pre-tokenized for testing
            'patient_code': 'MRN-2025-001-BW',  # Original PHI (would be tokenized in real flow)
            'message_text': 'Paciente con dolor severo y angustia emocional en región sacra',  # Multimodal indicators
            'image_path': '/test/images/bruce_wayne_talon.jpg',
            'audio_data': mock_audio_data,
            'has_audio': True,
            'has_voice': True,
            'patient_context': {
                'age': 45,
                'chronic_conditions': ['diabetes'],
                'pain_history': True,
                'previous_lpp': True
            },
            'raw_content': {
                'text': 'Paciente con dolor severo y angustia emocional',
                'image_data': 'mock_image_data',
                'audio_data': mock_audio_data
            },
            'metadata': {
                'has_media': True,
                'has_text': True,
                'has_voice': True,
                'has_audio': True,
                'multimodal_context': True
            }
        }
    
    def create_standardized_input(self, case_data: Dict[str, Any]):
        """Create standardized input for medical dispatcher"""
        from vigia_detect.core.medical_dispatcher import StandardizedInput
        
        return StandardizedInput(
            session_id=case_data['session_id'],
            input_type='multimodal_medical',
            raw_content=case_data['raw_content'],
            metadata=case_data['metadata'],
            timestamp=datetime.now()
        )
    
    async def test_medical_dispatcher_multimodal_routing(self) -> Dict[str, Any]:
        """Test 1: Medical Dispatcher recognizes multimodal context and routes appropriately"""
        logger.info("🧪 Test 1: Medical Dispatcher Multimodal Routing")
        
        case_data = self.create_bruce_wayne_multimodal_case()
        standardized_input = self.create_standardized_input(case_data)
        
        # Test triage decision
        triage_decision = await self.dispatcher._perform_medical_triage(standardized_input)
        
        # Validate routing
        expected_route = ProcessingRoute.MULTIMODAL_ANALYSIS
        actual_route = triage_decision.route
        
        success = actual_route == expected_route
        
        result = {
            'test': 'medical_dispatcher_routing',
            'success': success,
            'expected_route': expected_route.value,
            'actual_route': actual_route.value,
            'confidence': triage_decision.confidence,
            'reason': triage_decision.reason,
            'flags': triage_decision.flags
        }
        
        if success:
            logger.info(f"✅ Test 1 PASSED: Routed to {actual_route.value}")
        else:
            logger.error(f"❌ Test 1 FAILED: Expected {expected_route.value}, got {actual_route.value}")
        
        return result
    
    async def test_voice_analysis_requirement_detection(self) -> Dict[str, Any]:
        """Test 2: Master Orchestrator detects voice analysis requirement"""
        logger.info("🧪 Test 2: Voice Analysis Requirement Detection")
        
        case_data = self.create_bruce_wayne_multimodal_case()
        
        # Mock image analysis result that would trigger voice analysis
        mock_image_result = {
            'success': True,
            'image_analysis': {
                'lpp_detected': True,
                'lpp_grade': 2,
                'confidence': 0.85,
                'anatomical_location': 'sacrum'
            }
        }
        
        # Test voice analysis requirement detection
        requires_voice = self.orchestrator._requires_voice_analysis(mock_image_result, case_data)
        
        result = {
            'test': 'voice_analysis_requirement',
            'success': requires_voice,
            'case_has_voice_data': case_data.get('has_voice', False),
            'image_confidence': mock_image_result['image_analysis']['confidence'],
            'lpp_grade': mock_image_result['image_analysis']['lpp_grade'],
            'multimodal_indicators_in_text': 'dolor' in case_data['message_text'].lower()
        }
        
        if requires_voice:
            logger.info("✅ Test 2 PASSED: Voice analysis requirement detected")
        else:
            logger.error("❌ Test 2 FAILED: Voice analysis requirement not detected")
        
        return result
    
    async def test_multimodal_analysis_combination(self) -> Dict[str, Any]:
        """Test 3: Multimodal analysis combination logic"""
        logger.info("🧪 Test 3: Multimodal Analysis Combination")
        
        # Mock image analysis result
        mock_image_result = {
            'success': True,
            'image_analysis': {
                'lpp_detected': True,
                'lpp_grade': 2,
                'confidence': 0.85,
                'anatomical_location': 'sacrum'
            }
        }
        
        # Mock voice analysis result
        mock_voice_result = {
            'success': True,
            'voice_expressions': {
                'expressions': {
                    'Pain': 0.8,
                    'Anxiety': 0.7,
                    'Distress': 0.6
                }
            },
            'medical_assessment': {
                'urgency_level': 'high',
                'confidence_score': 0.82,
                'primary_concerns': ['High pain levels detected', 'Anxiety indicators present'],
                'medical_recommendations': ['Immediate pain assessment required'],
                'follow_up_required': True
            },
            'fase2_completed': True
        }
        
        # Test combination logic
        combined_analysis = self.orchestrator._combine_multimodal_analysis(
            mock_image_result, mock_voice_result
        )
        
        # Validate combination
        enhanced_assessment = combined_analysis.get('enhanced_assessment', {})
        multimodal_available = enhanced_assessment.get('multimodal_available', False)
        enhanced_confidence = enhanced_assessment.get('confidence', 0)
        enhanced_urgency = enhanced_assessment.get('urgency_level', 'normal')
        
        success = (
            multimodal_available and 
            enhanced_confidence > 0.8 and 
            enhanced_urgency in ['high', 'critical'] and
            combined_analysis.get('fase2_completed', False)
        )
        
        result = {
            'test': 'multimodal_combination',
            'success': success,
            'multimodal_available': multimodal_available,
            'enhanced_confidence': enhanced_confidence,
            'enhanced_urgency': enhanced_urgency,
            'fase2_completed': combined_analysis.get('fase2_completed', False),
            'analysis_type': combined_analysis.get('analysis_type', 'unknown')
        }
        
        if success:
            logger.info(f"✅ Test 3 PASSED: Enhanced confidence: {enhanced_confidence:.2f}, Urgency: {enhanced_urgency}")
        else:
            logger.error(f"❌ Test 3 FAILED: Multimodal combination logic failed")
        
        return result
    
    async def test_fase2_completion_handler(self) -> Dict[str, Any]:
        """Test 4: FASE 2 completion webhook handler"""
        logger.info("🧪 Test 4: FASE 2 Completion Handler")
        
        # Create FASE 2 completion payload
        fase2_payload = {
            'token_id': 'batman_token_001',
            'image_analysis': {
                'lpp_detected': True,
                'lpp_grade': 2,
                'confidence': 0.85,
                'anatomical_location': 'sacrum'
            },
            'voice_analysis': {
                'voice_available': True,
                'medical_assessment': {
                    'urgency_level': 'high',
                    'confidence_score': 0.82,
                    'primary_concerns': ['High pain levels detected'],
                    'follow_up_required': True
                }
            },
            'enhanced_assessment': {
                'confidence': 0.88,
                'urgency_level': 'high',
                'multimodal_available': True,
                'primary_concerns': ['High pain levels detected', 'LPP Grade 2 identified'],
                'medical_recommendations': ['Immediate medical evaluation required'],
                'follow_up_required': True
            }
        }
        
        # Test webhook handler
        handler_result = await self.webhook_handlers.handle_fase2_completion(
            EventType.ANALYSIS_COMPLETED, 
            fase2_payload
        )
        
        # Validate handler result
        success = (
            handler_result.get('status') == 'fase2_completed' and
            handler_result.get('combined_risk_level') in ['HIGH', 'CRITICAL'] and
            handler_result.get('multimodal_analysis', False) and
            handler_result.get('fase3_triggered', False)  # Should be True for high-risk
        )
        
        result = {
            'test': 'fase2_completion_handler',
            'success': success,
            'handler_result': handler_result
        }
        
        if success:
            logger.info(f"✅ Test 4 PASSED: FASE 2 completion handled successfully")
            logger.info(f"   Risk Level: {handler_result.get('combined_risk_level')}")
            logger.info(f"   FASE 3 Triggered: {handler_result.get('fase3_triggered')}")
        else:
            logger.error(f"❌ Test 4 FAILED: FASE 2 completion handler failed")
        
        return result
    
    async def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run complete FASE 2 voice trigger test suite"""
        logger.info("🚀 Starting FASE 2 Voice + Image Trigger Integration Test")
        logger.info("=" * 70)
        
        await self.setup()
        
        # Run all tests
        test_results = []
        
        try:
            # Test 1: Medical Dispatcher Routing
            result1 = await self.test_medical_dispatcher_multimodal_routing()
            test_results.append(result1)
            
            # Test 2: Voice Analysis Requirement Detection
            result2 = await self.test_voice_analysis_requirement_detection()
            test_results.append(result2)
            
            # Test 3: Multimodal Analysis Combination
            result3 = await self.test_multimodal_analysis_combination()
            test_results.append(result3)
            
            # Test 4: FASE 2 Completion Handler
            result4 = await self.test_fase2_completion_handler()
            test_results.append(result4)
            
        except Exception as e:
            logger.error(f"❌ Test suite failed with error: {str(e)}")
            return {
                'overall_success': False,
                'error': str(e),
                'completed_tests': len(test_results),
                'test_results': test_results
            }
        
        # Calculate overall results
        successful_tests = sum(1 for result in test_results if result['success'])
        total_tests = len(test_results)
        overall_success = successful_tests == total_tests
        
        # Summary
        logger.info("=" * 70)
        logger.info("🏁 FASE 2 Voice Trigger Integration Test Summary")
        logger.info(f"✅ Successful Tests: {successful_tests}/{total_tests}")
        
        if overall_success:
            logger.info("🎉 ALL TESTS PASSED - FASE 2 Voice + Image Integration Ready!")
            logger.info("🎯 Bruce Wayne case can now trigger FASE 2 with:")
            logger.info("   • Image analysis (existing)")
            logger.info("   • Voice analysis (NEW)")
            logger.info("   • Multimodal assessment (NEW)")
            logger.info("   • Enhanced medical insights (NEW)")
            logger.info("   • FASE 3 trigger capability (NEW)")
        else:
            logger.error("❌ Some tests failed - Review integration issues")
        
        return {
            'overall_success': overall_success,
            'successful_tests': successful_tests,
            'total_tests': total_tests,
            'test_results': test_results,
            'timestamp': datetime.now().isoformat()
        }


async def main():
    """Main test execution"""
    test_suite = FASE2VoiceTriggerTest()
    results = await test_suite.run_complete_test_suite()
    
    # Pretty print results
    print("\n" + "=" * 50)
    print("FASE 2 VOICE TRIGGER TEST RESULTS")
    print("=" * 50)
    print(json.dumps(results, indent=2, default=str))
    
    return results['overall_success']


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)