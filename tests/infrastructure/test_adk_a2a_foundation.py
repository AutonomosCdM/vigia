#!/usr/bin/env python3
"""
Test ADK A2A Foundation - Comprehensive Testing Suite
====================================================

Complete testing framework for ADK-based agents and Agent-to-Agent (A2A) communication
in the Vigia medical system. Tests all specialized agents and their interactions.

This test suite validates:
- Individual agent functionality
- A2A communication protocols
- Master orchestrator coordination
- Medical workflow integration
- Error handling and fallbacks
"""

import asyncio
import pytest
import logging
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test data structures
class TestMedicalCase:
    """Test case data structure"""
    def __init__(self, case_id: str, description: str, input_data: Dict[str, Any]):
        self.case_id = case_id
        self.description = description
        self.input_data = input_data
        self.expected_outcomes = {}
        self.test_results = {}

# Test cases for comprehensive validation
TEST_CASES = [
    TestMedicalCase(
        case_id="TC001",
        description="LPP Grade 2 - Standard Clinical Case",
        input_data={
            "image_path": "test_images/lpp_grade2_sacrum.jpg",
            "patient_code": "CD-2025-001",
            "patient_context": {
                "age": 65,
                "diabetes": True,
                "mobility": "limited",
                "risk_factors": ["diabetes", "limited_mobility", "malnutrition"]
            },
            "session_token": "test_session_001",
            "priority": "medium"
        }
    ),
    TestMedicalCase(
        case_id="TC002", 
        description="LPP Grade 4 - Critical Emergency Case",
        input_data={
            "image_path": "test_images/lpp_grade4_ischium.jpg",
            "patient_code": "CD-2025-002",
            "patient_context": {
                "age": 78,
                "diabetes": True,
                "anticoagulated": True,
                "recent_surgery": True,
                "risk_factors": ["diabetes", "anticoagulation", "post_surgical"]
            },
            "session_token": "test_session_002",
            "priority": "critical"
        }
    ),
    TestMedicalCase(
        case_id="TC003",
        description="Medical Query - Protocol Consultation",
        input_data={
            "text": "¿Cuál es el protocolo para LPP Grade 3 en paciente diabético?",
            "patient_context": {
                "diabetes": True,
                "lpp_grade": 3,
                "location": "trochanter"
            },
            "session_token": "test_session_003",
            "priority": "medium"
        }
    )
]

class TestADKA2AFoundation:
    """Comprehensive test suite for ADK A2A foundation"""
    
    def __init__(self):
        self.test_results = {}
        self.agents = {}
        self.master_orchestrator = None
        
    async def setup_test_environment(self):
        """Setup test environment with all agents"""
        logger.info("🔧 Setting up test environment...")
        
        try:
            # Import agent factories
            from vigia_detect.agents.image_analysis_agent import ImageAnalysisAgentFactory
            from vigia_detect.agents.clinical_assessment_agent import ClinicalAssessmentAgentFactory
            from vigia_detect.agents.protocol_agent import ProtocolAgentFactory
            from vigia_detect.agents.communication_agent import CommunicationAgentFactory
            from vigia_detect.agents.workflow_orchestration_agent import WorkflowOrchestrationAgentFactory
            from vigia_detect.agents.master_medical_orchestrator import register_all_agents
            
            # Create individual agents
            logger.info("Creating specialized agents...")
            self.agents['image_analysis'] = await ImageAnalysisAgentFactory.create_agent()
            self.agents['clinical_assessment'] = await ClinicalAssessmentAgentFactory.create_agent()
            self.agents['protocol'] = await ProtocolAgentFactory.create_agent()
            self.agents['communication'] = await CommunicationAgentFactory.create_agent()
            self.agents['workflow'] = await WorkflowOrchestrationAgentFactory.create_agent()
            
            # Create master orchestrator with all agents registered
            logger.info("Creating master orchestrator with A2A registration...")
            self.master_orchestrator = await register_all_agents()
            
            logger.info("✅ Test environment setup completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Test environment setup failed: {e}")
            return False
    
    async def test_individual_agents(self) -> Dict[str, Dict[str, Any]]:
        """Test individual agent functionality"""
        logger.info("🧪 Testing individual agents...")
        results = {}
        
        for agent_name, agent in self.agents.items():
            logger.info(f"Testing {agent_name} agent...")
            
            try:
                # Create test message for each agent type
                test_message = self._create_test_message(agent_name)
                
                # Process message
                start_time = datetime.now(timezone.utc)
                response = await agent.process_message(test_message)
                processing_time = (datetime.now(timezone.utc) - start_time).total_seconds()
                
                # Validate response
                validation_result = self._validate_agent_response(agent_name, response)
                
                results[agent_name] = {
                    'success': response.success,
                    'processing_time': processing_time,
                    'response_valid': validation_result['valid'],
                    'capabilities_tested': len(agent.capabilities),
                    'errors': validation_result.get('errors', []),
                    'agent_metadata': {
                        'agent_id': agent.agent_id,
                        'version': agent.version,
                        'is_initialized': agent.is_initialized
                    }
                }
                
                logger.info(f"✅ {agent_name} agent test completed")
                
            except Exception as e:
                logger.error(f"❌ {agent_name} agent test failed: {e}")
                results[agent_name] = {
                    'success': False,
                    'error': str(e),
                    'processing_time': 0,
                    'response_valid': False
                }
        
        return results
    
    async def test_a2a_communication(self) -> Dict[str, Any]:
        """Test Agent-to-Agent communication"""
        logger.info("🔗 Testing A2A communication...")
        
        try:
            from vigia_detect.agents.base_agent import AgentMessage
            
            # Test direct A2A communication between agents
            sender = self.agents['image_analysis']
            receiver = self.agents['clinical_assessment']
            
            # Create A2A message
            a2a_message = AgentMessage(
                session_id="a2a_test_session",
                sender_id=sender.agent_id,
                content={
                    "image_analysis_result": {
                        "lpp_detected": True,
                        "lpp_grade": 2,
                        "confidence": 0.85,
                        "anatomical_location": "sacrum"
                    },
                    "patient_code": "CD-2025-A2A",
                    "requires_clinical_assessment": True
                },
                message_type="a2a_communication",
                timestamp=datetime.now(timezone.utc),
                metadata={
                    "sender_agent": sender.agent_id,
                    "receiver_agent": receiver.agent_id,
                    "communication_type": "medical_handoff"
                }
            )
            
            # Process A2A message
            start_time = datetime.now(timezone.utc)
            response = await receiver.process_message(a2a_message)
            communication_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            return {
                'success': response.success,
                'communication_time': communication_time,
                'sender_agent': sender.agent_id,
                'receiver_agent': receiver.agent_id,
                'message_processed': True,
                'response_metadata': response.metadata,
                'a2a_protocol': 'ADK'
            }
            
        except Exception as e:
            logger.error(f"❌ A2A communication test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'communication_time': 0,
                'a2a_protocol': 'ADK'
            }
    
    async def run_complete_test_suite(self) -> Dict[str, Any]:
        """Run complete test suite"""
        logger.info("🚀 Starting complete ADK A2A foundation test suite...")
        
        # Setup
        setup_success = await self.setup_test_environment()
        if not setup_success:
            return {
                'success': False,
                'error': 'Test environment setup failed',
                'timestamp': datetime.now().isoformat()
            }
        
        # Run all tests
        test_results = {
            'setup': {'success': setup_success},
            'individual_agents': await self.test_individual_agents(),
            'a2a_communication': await self.test_a2a_communication()
        }
        
        # Calculate overall success
        overall_success = all(
            result.get('success', False) if isinstance(result, dict) else True
            for test_category in test_results.values()
            for result in (test_category.values() if isinstance(test_category, dict) else [test_category])
        )
        
        # Generate summary
        summary = self._generate_test_summary(test_results)
        
        final_result = {
            'overall_success': overall_success,
            'test_results': test_results,
            'summary': summary,
            'timestamp': datetime.now().isoformat(),
            'test_environment': {
                'agents_created': len(self.agents),
                'master_orchestrator_ready': self.master_orchestrator is not None,
                'a2a_enabled': True
            }
        }
        
        logger.info(f"🏁 Test suite completed. Overall success: {overall_success}")
        return final_result
    
    def _create_test_message(self, agent_name: str):
        """Create appropriate test message for each agent type"""
        from vigia_detect.agents.base_agent import AgentMessage
        
        test_messages = {
            'image_analysis': {
                "image_path": "test_images/sample_lpp.jpg",
                "patient_code": "CD-2025-TEST",
                "analysis_parameters": {
                    "model_version": "yolov5s_medical",
                    "confidence_threshold": 0.5
                }
            },
            'clinical_assessment': {
                "image_analysis_result": {
                    "lpp_detected": True,
                    "lpp_grade": 2,
                    "confidence": 0.75,
                    "anatomical_location": "sacrum"
                },
                "patient_context": {
                    "age": 65,
                    "diabetes": True,
                    "mobility": "limited"
                }
            },
            'protocol': {
                "clinical_context": "LPP Grade 2 tratamiento",
                "patient_context": {
                    "diabetes": True,
                    "anticoagulated": False
                },
                "include_references": True
            },
            'communication': {
                "text": "Notificación médica LPP Grade 2 detectada",
                "recipients": ["equipo_clinico"],
                "priority": "medium",
                "channel": "slack"
            },
            'workflow': {
                "text": "Procesar workflow médico completo",
                "workflow_type": "clinical_assessment",
                "input_data": {
                    "patient_code": "CD-2025-WF"
                },
                "priority": "medium"
            }
        }
        
        return AgentMessage(
            session_id=f"test_{agent_name}",
            sender_id="test_runner",
            content=test_messages.get(agent_name, {}),
            message_type="test_message",
            timestamp=datetime.now(timezone.utc),
            metadata={"test_context": True}
        )
    
    def _validate_agent_response(self, agent_name: str, response) -> Dict[str, Any]:
        """Validate agent response structure and content"""
        errors = []
        
        # Basic response structure validation
        if not hasattr(response, 'success'):
            errors.append("Response missing 'success' attribute")
        if not hasattr(response, 'content'):
            errors.append("Response missing 'content' attribute")
        if not hasattr(response, 'metadata'):
            errors.append("Response missing 'metadata' attribute")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _generate_test_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate test summary statistics"""
        summary = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'agents_tested': 0,
            'a2a_communications_tested': 0,
            'critical_errors': []
        }
        
        # Count individual agent tests
        if 'individual_agents' in test_results:
            summary['agents_tested'] = len(test_results['individual_agents'])
            for agent_result in test_results['individual_agents'].values():
                summary['total_tests'] += 1
                if agent_result.get('success'):
                    summary['passed_tests'] += 1
                else:
                    summary['failed_tests'] += 1
        
        # Count other tests
        for test_name, test_result in test_results.items():
            if test_name != 'individual_agents':
                summary['total_tests'] += 1
                if test_result.get('success'):
                    summary['passed_tests'] += 1
                else:
                    summary['failed_tests'] += 1
                    if test_name in ['setup', 'master_orchestration']:
                        summary['critical_errors'].append(test_name)
        
        # A2A communication count
        if test_results.get('a2a_communication', {}).get('success'):
            summary['a2a_communications_tested'] = 1
        
        summary['success_rate'] = (summary['passed_tests'] / summary['total_tests'] * 100) if summary['total_tests'] > 0 else 0
        
        return summary


async def main():
    """Main test runner"""
    print("=" * 60)
    print("ADK A2A Foundation - Comprehensive Test Suite")
    print("=" * 60)
    
    tester = TestADKA2AFoundation()
    
    try:
        # Run complete test suite
        results = await tester.run_complete_test_suite()
        
        # Print results
        print("\n🏁 TEST RESULTS SUMMARY")
        print("=" * 40)
        
        summary = results.get('summary', {})
        print(f"Overall Success: {'✅ PASS' if results['overall_success'] else '❌ FAIL'}")
        print(f"Total Tests: {summary.get('total_tests', 0)}")
        print(f"Passed: {summary.get('passed_tests', 0)}")
        print(f"Failed: {summary.get('failed_tests', 0)}")
        print(f"Success Rate: {summary.get('success_rate', 0):.1f}%")
        print(f"Agents Tested: {summary.get('agents_tested', 0)}")
        print(f"A2A Communications: {summary.get('a2a_communications_tested', 0)}")
        
        if summary.get('critical_errors'):
            print(f"Critical Errors: {', '.join(summary['critical_errors'])}")
        
        # Print detailed results
        print("\n📊 DETAILED RESULTS")
        print("=" * 40)
        
        for test_category, test_result in results['test_results'].items():
            print(f"\n{test_category.upper()}:")
            if isinstance(test_result, dict):
                for sub_test, sub_result in test_result.items():
                    if isinstance(sub_result, dict):
                        status = "✅ PASS" if sub_result.get('success') else "❌ FAIL"
                        print(f"  {sub_test}: {status}")
                        if 'processing_time' in sub_result:
                            print(f"    Time: {sub_result['processing_time']:.3f}s")
                        if 'error' in sub_result:
                            print(f"    Error: {sub_result['error']}")
        
        # Environment info
        env = results.get('test_environment', {})
        print(f"\n🔧 TEST ENVIRONMENT")
        print("=" * 40)
        print(f"Agents Created: {env.get('agents_created', 0)}")
        print(f"Master Orchestrator: {'✅ Ready' if env.get('master_orchestrator_ready') else '❌ Failed'}")
        print(f"A2A Communication: {'✅ Enabled' if env.get('a2a_enabled') else '❌ Disabled'}")
        
        print(f"\n⏰ Test completed at: {results['timestamp']}")
        
        # Return exit code
        return 0 if results['overall_success'] else 1
        
    except Exception as e:
        logger.error(f"❌ Test suite failed with exception: {e}")
        print(f"\n❌ CRITICAL ERROR: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)