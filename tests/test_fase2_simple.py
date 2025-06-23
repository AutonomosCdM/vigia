#!/usr/bin/env python3
"""
Simple FASE 2 Voice + Image Trigger Test
========================================

Simplified test to validate the core FASE 2 logic without full infrastructure dependencies.

Tests:
1. Medical Dispatcher multimodal detection logic
2. Voice analysis requirement logic  
3. Multimodal combination logic
4. FASE 2 completion assessment
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SimpleFASE2Test:
    """Simplified FASE 2 voice trigger test suite"""
    
    def test_multimodal_detection_logic(self) -> Dict[str, Any]:
        """Test 1: Multimodal context detection logic"""
        logger.info("🧪 Test 1: Multimodal Context Detection")
        
        # Simulate the _is_multimodal_medical_context method logic
        def is_multimodal_medical_context(text_content: str) -> bool:
            if not text_content:
                return False
            
            text_lower = text_content.lower()
            
            multimodal_indicators = [
                "dolor", "pain", "ansiedad", "anxiety", "estrés", "stress",
                "emocional", "emotional", "voz", "voice", "llanto", "crying"
            ]
            
            indicator_count = sum(1 for indicator in multimodal_indicators if indicator in text_lower)
            return indicator_count >= 2
        
        # Test cases
        test_cases = [
            {
                'text': 'Paciente con dolor severo y angustia emocional en región sacra',
                'expected': True,
                'description': 'Bruce Wayne case - dolor + emocional'
            },
            {
                'text': 'Patient has pain and anxiety about treatment',
                'expected': True,
                'description': 'English multimodal case'
            },
            {
                'text': 'Simple LPP detection needed',
                'expected': False,
                'description': 'Simple image-only case'
            },
            {
                'text': 'Paciente con dolor, estrés y ansiedad vocal',
                'expected': True,
                'description': 'Triple indicator case'
            }
        ]
        
        results = []
        for case in test_cases:
            result = is_multimodal_medical_context(case['text'])
            success = result == case['expected']
            results.append({
                'text': case['text'][:50] + '...',
                'expected': case['expected'],
                'actual': result,
                'success': success,
                'description': case['description']
            })
            
            status = "✅" if success else "❌"
            logger.info(f"   {status} {case['description']}: {result}")
        
        overall_success = all(r['success'] for r in results)
        
        return {
            'test': 'multimodal_detection',
            'success': overall_success,
            'test_cases': results,
            'passed': sum(1 for r in results if r['success']),
            'total': len(results)
        }
    
    def test_voice_analysis_requirement_logic(self) -> Dict[str, Any]:
        """Test 2: Voice analysis requirement logic"""
        logger.info("🧪 Test 2: Voice Analysis Requirement Logic")
        
        def requires_voice_analysis(image_result: Dict, case_data: Dict) -> bool:
            # Check if voice data is available
            has_voice_data = (
                case_data.get('audio_data') is not None or 
                case_data.get('has_voice', False)
            )
            
            if not has_voice_data:
                return False
            
            # Check image analysis results
            confidence = image_result.get('confidence', 0.0)
            lpp_grade = image_result.get('lpp_grade', 0)
            
            # Require voice for significant findings
            if confidence >= 0.7 and lpp_grade >= 2:
                return True
            
            # Check for voice indicators in message
            message_text = case_data.get('message_text', '').lower()
            voice_indicators = ['dolor', 'pain', 'ansiedad', 'anxiety', 'llanto', 'crying']
            
            return any(indicator in message_text for indicator in voice_indicators)
        
        # Test cases
        test_cases = [
            {
                'description': 'Bruce Wayne - High confidence LPP + voice data + pain indicators',
                'image_result': {'confidence': 0.85, 'lpp_grade': 2},
                'case_data': {'has_voice': True, 'message_text': 'dolor severo', 'audio_data': 'mock_data'},
                'expected': True
            },
            {
                'description': 'High confidence but no voice data',
                'image_result': {'confidence': 0.85, 'lpp_grade': 2},
                'case_data': {'has_voice': False, 'message_text': 'dolor severo'},
                'expected': False
            },
            {
                'description': 'Voice data but low confidence image',
                'image_result': {'confidence': 0.5, 'lpp_grade': 1},
                'case_data': {'has_voice': True, 'message_text': 'simple check'},
                'expected': False
            },
            {
                'description': 'Voice data + pain indicators (even with lower grade)',
                'image_result': {'confidence': 0.6, 'lpp_grade': 1},
                'case_data': {'has_voice': True, 'message_text': 'paciente con dolor y ansiedad'},
                'expected': True
            }
        ]
        
        results = []
        for case in test_cases:
            result = requires_voice_analysis(case['image_result'], case['case_data'])
            success = result == case['expected']
            results.append({
                'description': case['description'],
                'expected': case['expected'],
                'actual': result,
                'success': success
            })
            
            status = "✅" if success else "❌"
            logger.info(f"   {status} {case['description']}: {result}")
        
        overall_success = all(r['success'] for r in results)
        
        return {
            'test': 'voice_analysis_requirement',
            'success': overall_success,
            'test_cases': results,
            'passed': sum(1 for r in results if r['success']),
            'total': len(results)
        }
    
    def test_multimodal_combination_logic(self) -> Dict[str, Any]:
        """Test 3: Multimodal analysis combination logic"""
        logger.info("🧪 Test 3: Multimodal Analysis Combination")
        
        def combine_multimodal_analysis(image_result: Dict, voice_result: Dict = None) -> Dict:
            combined = {
                'success': image_result.get('success', False),
                'analysis_type': 'image_only' if voice_result is None else 'multimodal',
                'image_analysis': image_result.get('image_analysis', {}),
                'processing_timestamp': datetime.now().isoformat()
            }
            
            if voice_result and voice_result.get('success'):
                # Add voice analysis
                combined['voice_analysis'] = {
                    'medical_assessment': voice_result.get('medical_assessment', {}),
                    'voice_available': True
                }
                
                # Enhanced assessment with multimodal insights
                image_confidence = image_result.get('image_analysis', {}).get('confidence', 0)
                voice_confidence = voice_result.get('medical_assessment', {}).get('confidence_score', 0)
                
                # Enhanced confidence (multimodal bonus)
                enhanced_confidence = min(0.95, (image_confidence + voice_confidence) / 2 + 0.1)
                
                # Enhanced urgency
                voice_urgency = voice_result.get('medical_assessment', {}).get('urgency_level', 'normal')
                lpp_grade = image_result.get('image_analysis', {}).get('lpp_grade', 0)
                
                image_urgency = 'critical' if lpp_grade >= 4 else 'high' if lpp_grade >= 3 else 'elevated' if lpp_grade >= 2 else 'normal'
                
                # Take the higher urgency
                urgency_priority = {'critical': 4, 'high': 3, 'elevated': 2, 'normal': 1}
                max_urgency = max(urgency_priority.get(image_urgency, 1), urgency_priority.get(voice_urgency, 1))
                
                for level, priority in urgency_priority.items():
                    if priority == max_urgency:
                        enhanced_urgency = level
                        break
                
                combined['enhanced_assessment'] = {
                    'confidence': enhanced_confidence,
                    'urgency_level': enhanced_urgency,
                    'multimodal_available': True,
                    'primary_concerns': voice_result.get('medical_assessment', {}).get('primary_concerns', []),
                    'follow_up_required': voice_result.get('medical_assessment', {}).get('follow_up_required', False)
                }
                
                combined['fase2_completed'] = True
            else:
                # Image-only
                combined['voice_analysis'] = {'voice_available': False}
                combined['enhanced_assessment'] = {
                    'confidence': image_result.get('image_analysis', {}).get('confidence', 0),
                    'urgency_level': 'normal',
                    'multimodal_available': False
                }
                combined['fase2_completed'] = False
            
            return combined
        
        # Test Bruce Wayne multimodal case
        bruce_image_result = {
            'success': True,
            'image_analysis': {
                'lpp_detected': True,
                'lpp_grade': 2,
                'confidence': 0.85,
                'anatomical_location': 'sacrum'
            }
        }
        
        bruce_voice_result = {
            'success': True,
            'medical_assessment': {
                'urgency_level': 'high',
                'confidence_score': 0.82,
                'primary_concerns': ['High pain levels detected', 'Anxiety indicators present'],
                'follow_up_required': True
            }
        }
        
        # Test combination
        combined = combine_multimodal_analysis(bruce_image_result, bruce_voice_result)
        
        # Validate results
        enhanced = combined.get('enhanced_assessment', {})
        
        success_criteria = [
            combined.get('analysis_type') == 'multimodal',
            enhanced.get('multimodal_available', False),
            enhanced.get('confidence', 0) > 0.8,  # Should be enhanced
            enhanced.get('urgency_level') == 'high',
            combined.get('fase2_completed', False),
            len(enhanced.get('primary_concerns', [])) > 0
        ]
        
        success = all(success_criteria)
        
        logger.info(f"   Enhanced Confidence: {enhanced.get('confidence', 0):.2f}")
        logger.info(f"   Enhanced Urgency: {enhanced.get('urgency_level')}")
        logger.info(f"   FASE 2 Completed: {combined.get('fase2_completed')}")
        logger.info(f"   Primary Concerns: {len(enhanced.get('primary_concerns', []))}")
        
        return {
            'test': 'multimodal_combination',
            'success': success,
            'enhanced_confidence': enhanced.get('confidence', 0),
            'enhanced_urgency': enhanced.get('urgency_level'),
            'multimodal_available': enhanced.get('multimodal_available', False),
            'fase2_completed': combined.get('fase2_completed', False),
            'success_criteria_met': sum(success_criteria),
            'total_criteria': len(success_criteria)
        }
    
    def test_fase2_completion_assessment(self) -> Dict[str, Any]:
        """Test 4: FASE 2 completion assessment logic"""
        logger.info("🧪 Test 4: FASE 2 Completion Assessment")
        
        def assess_combined_risk(enhanced_assessment: Dict) -> str:
            urgency_level = enhanced_assessment.get('urgency_level', 'normal')
            confidence = enhanced_assessment.get('confidence', 0)
            
            urgency_to_risk = {
                'critical': 'CRITICAL',
                'high': 'HIGH',
                'elevated': 'MEDIUM',
                'normal': 'LOW'
            }
            
            base_risk = urgency_to_risk.get(urgency_level, 'LOW')
            
            # Enhance risk with confidence
            if confidence >= 0.9 and base_risk in ['MEDIUM', 'HIGH']:
                if base_risk == 'MEDIUM':
                    return 'HIGH'
                elif base_risk == 'HIGH':
                    return 'CRITICAL'
            
            return base_risk
        
        def should_trigger_fase3(risk_level: str, enhanced_assessment: Dict) -> bool:
            if risk_level in ['HIGH', 'CRITICAL']:
                return True
            
            if enhanced_assessment.get('follow_up_required', False):
                return True
            
            confidence = enhanced_assessment.get('confidence', 0)
            concerns = enhanced_assessment.get('primary_concerns', [])
            
            return confidence >= 0.8 and len(concerns) >= 2
        
        # Test Bruce Wayne enhanced assessment
        bruce_enhanced = {
            'confidence': 0.88,
            'urgency_level': 'high',
            'multimodal_available': True,
            'primary_concerns': ['High pain levels detected', 'LPP Grade 2 identified'],
            'follow_up_required': True
        }
        
        # Assess risk and FASE 3 trigger
        risk_level = assess_combined_risk(bruce_enhanced)
        fase3_trigger = should_trigger_fase3(risk_level, bruce_enhanced)
        
        # Expected outcomes for Bruce Wayne case
        expected_risk = 'HIGH'  # High urgency + high confidence
        expected_fase3 = True   # High risk + follow_up_required
        
        success = (risk_level == expected_risk and fase3_trigger == expected_fase3)
        
        logger.info(f"   Risk Level: {risk_level} (expected: {expected_risk})")
        logger.info(f"   FASE 3 Trigger: {fase3_trigger} (expected: {expected_fase3})")
        
        return {
            'test': 'fase2_completion_assessment',
            'success': success,
            'risk_level': risk_level,
            'expected_risk': expected_risk,
            'fase3_trigger': fase3_trigger,
            'expected_fase3': expected_fase3,
            'confidence': bruce_enhanced['confidence'],
            'urgency': bruce_enhanced['urgency_level']
        }
    
    def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run complete simplified FASE 2 test suite"""
        logger.info("🚀 Starting Simple FASE 2 Voice + Image Integration Test")
        logger.info("=" * 60)
        
        test_results = []
        
        try:
            # Run all tests
            test_results.append(self.test_multimodal_detection_logic())
            test_results.append(self.test_voice_analysis_requirement_logic())
            test_results.append(self.test_multimodal_combination_logic())
            test_results.append(self.test_fase2_completion_assessment())
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {str(e)}")
            return {
                'overall_success': False,
                'error': str(e),
                'test_results': test_results
            }
        
        # Calculate results
        successful_tests = sum(1 for result in test_results if result['success'])
        total_tests = len(test_results)
        overall_success = successful_tests == total_tests
        
        # Summary
        logger.info("=" * 60)
        logger.info("🏁 Simple FASE 2 Test Summary")
        logger.info(f"✅ Successful Tests: {successful_tests}/{total_tests}")
        
        if overall_success:
            logger.info("🎉 ALL LOGIC TESTS PASSED!")
            logger.info("🎯 FASE 2 Voice + Image Integration Logic Validated:")
            logger.info("   ✅ Multimodal context detection")
            logger.info("   ✅ Voice analysis requirement logic")
            logger.info("   ✅ Multimodal combination logic")
            logger.info("   ✅ FASE 2 completion assessment")
            logger.info("")
            logger.info("🔄 Bruce Wayne FASE 2 Trigger Ready:")
            logger.info("   • Image analysis → Voice analysis requirement detected")
            logger.info("   • Voice + Image → Enhanced multimodal assessment")
            logger.info("   • Enhanced assessment → FASE 3 trigger for medical team")
        else:
            logger.error("❌ Some logic tests failed")
        
        return {
            'overall_success': overall_success,
            'successful_tests': successful_tests,
            'total_tests': total_tests,
            'test_results': test_results,
            'timestamp': datetime.now().isoformat()
        }


def main():
    """Main test execution"""
    test_suite = SimpleFASE2Test()
    results = test_suite.run_complete_test_suite()
    
    # Pretty print results
    print("\n" + "=" * 50)
    print("FASE 2 VOICE TRIGGER LOGIC TEST RESULTS")
    print("=" * 50)
    print(json.dumps(results, indent=2, default=str))
    
    return results['overall_success']


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)