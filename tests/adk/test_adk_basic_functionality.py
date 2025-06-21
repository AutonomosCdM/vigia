#!/usr/bin/env python3
"""
Simple ADK Integration Test - FASE 2 Quick Validation
====================================================

Test simplificado para validar que el Master Medical Orchestrator
puede usar los agentes ADK especializados sin dependencias externas.

Solo testea la estructura básica sin Redis/Supabase.
"""

import asyncio
import logging
from datetime import datetime
import sys
from pathlib import Path
import pytest
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_basic_import():
    """Test basic imports work"""
    try:
        logger.info("Testing basic imports...")
        
        # Test individual agent imports
        from vigia_detect.agents.base_agent import BaseAgent, AgentMessage, AgentResponse
        logger.info("✅ BaseAgent imported successfully")
        
        # Try to import the master orchestrator
        from vigia_detect.agents.master_medical_orchestrator import MasterMedicalOrchestrator
        logger.info("✅ MasterMedicalOrchestrator imported successfully")
        
    except Exception as e:
        logger.error(f"❌ Import failed: {str(e)}")
        pytest.fail(f"Import failed: {str(e)}")


@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator can be initialized"""
    try:
        logger.info("Testing orchestrator initialization...")
        
        from vigia_detect.agents.master_medical_orchestrator import MasterMedicalOrchestrator
        
        # Initialize orchestrator
        orchestrator = MasterMedicalOrchestrator()
        logger.info("✅ Orchestrator initialized")
        
        # Test basic properties
        assert orchestrator.orchestrator_id is not None
        assert isinstance(orchestrator.registered_agents, dict)
        logger.info("✅ Orchestrator basic properties validated")
        
    except Exception as e:
        logger.error(f"❌ Orchestrator initialization failed: {str(e)}")
        pytest.fail(f"Orchestrator initialization failed: {str(e)}")


@pytest.mark.asyncio
async def test_mock_case_processing():
    """Test mock medical case processing"""
    try:
        logger.info("Testing mock case processing...")
        
        from vigia_detect.agents.master_medical_orchestrator import MasterMedicalOrchestrator
        
        # Initialize orchestrator
        orchestrator = MasterMedicalOrchestrator()
        
        # Create test case data
        test_case_data = {
            'session_token': 'test_simple_session',
            'patient_code': 'TEST-SIMPLE-001',
            'image_path': '/test/mock_image.jpg',
            'patient_context': {
                'age': 65,
                'diabetes': False,
                'mobility': 'normal'
            },
            'metadata': {
                'source': 'simple_test',
                'timestamp': datetime.now().isoformat()
            }
        }
        
        # Process medical case (should use fallbacks since A2A agents not initialized)
        logger.info("Processing test case with fallback mechanisms...")
        result = await orchestrator.process_medical_case(test_case_data)
        
        # Validate result structure
        assert isinstance(result, dict)
        assert 'case_id' in result
        assert 'patient_code' in result
        assert result['patient_code'] == 'TEST-SIMPLE-001'
        
        logger.info(f"✅ Case processing result: {result.get('overall_success', 'unknown')}")
        
        # Check that fallback agents were used
        agent_summary = result.get('agent_processing_summary', {})
        for agent_type, agent_info in agent_summary.items():
            agent_used = agent_info.get('agent_used', 'unknown')
            logger.info(f"   {agent_type}: {agent_used}")
        
    except Exception as e:
        logger.error(f"❌ Mock case processing failed: {str(e)}")
        logger.exception("Full stacktrace:")
        pytest.fail(f"Mock case processing failed: {str(e)}")


@pytest.mark.asyncio
async def test_orchestrator_stats():
    """Test orchestrator statistics"""
    try:
        logger.info("Testing orchestrator statistics...")
        
        from vigia_detect.agents.master_medical_orchestrator import MasterMedicalOrchestrator
        
        # Initialize orchestrator
        orchestrator = MasterMedicalOrchestrator()
        
        # Get stats
        stats = orchestrator.get_orchestrator_stats()
        
        # Validate stats structure
        assert isinstance(stats, dict)
        assert 'orchestrator_id' in stats
        assert 'stats' in stats
        assert 'registered_agents' in stats
        
        logger.info(f"✅ Stats retrieved: {stats['stats']}")
        logger.info(f"   Registered agents: {stats['registered_agents']}")
        
    except Exception as e:
        logger.error(f"❌ Stats test failed: {str(e)}")
        pytest.fail(f"Stats test failed: {str(e)}")


async def run_simple_test_suite():
    """Run complete simple test suite"""
    logger.info("🚀 Starting Simple ADK Integration Test Suite")
    logger.info("=" * 60)
    
    test_results = {}
    
    # Test 1: Basic imports
    try:
        await test_basic_import()
        test_results['imports'] = True
    except Exception:
        test_results['imports'] = False
    
    # Test 2: Orchestrator initialization
    try:
        await test_orchestrator_initialization()
        test_results['initialization'] = True
    except Exception:
        test_results['initialization'] = False
    
    # Test 3: Mock case processing
    try:
        await test_mock_case_processing()
        test_results['case_processing'] = True
    except Exception:
        test_results['case_processing'] = False
    
    # Test 4: Orchestrator stats
    try:
        await test_orchestrator_stats()
        test_results['stats'] = True
    except Exception:
        test_results['stats'] = False
    
    # Summary
    logger.info("=" * 60)
    logger.info("🎯 SIMPLE ADK INTEGRATION TEST RESULTS")
    logger.info("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name.title()}: {status}")
    
    logger.info("=" * 60)
    logger.info(f"Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 ALL TESTS PASSED - FASE 2 Basic Integration Working!")
        return 0
    else:
        logger.warning(f"⚠️ {total_tests - passed_tests} tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_simple_test_suite())
    sys.exit(exit_code)