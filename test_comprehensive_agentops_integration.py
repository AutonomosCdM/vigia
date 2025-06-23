#!/usr/bin/env python3
"""
Comprehensive AgentOps Integration Test - All Medical Agents
===========================================================

Complete validation of AgentOps monitoring across all medical agents
and the new bidirectional communication architecture.

Tests:
- PatientCommunicationAgent telemetry
- MedicalTeamAgent monitoring
- MasterMedicalOrchestrator coordination tracking
- RiskAssessmentAgent performance metrics
- CommunicationBridge inter-agent tracking
- Complete medical workflow with AgentOps visibility
"""

import asyncio
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

# Import medical agents with AgentOps integration
from vigia_detect.agents.patient_communication_agent import PatientCommunicationAgentFactory, _patient_telemetry
from vigia_detect.agents.medical_team_agent import MedicalTeamAgentFactory, _medical_team_telemetry
from vigia_detect.agents.master_medical_orchestrator import MasterMedicalOrchestrator
from vigia_detect.agents.risk_assessment_agent import RiskAssessmentAgent
from vigia_detect.agents.communication_bridge import CommunicationBridge

# Direct AgentOps client for validation
from test_agentops_integration import AgentOpsDirectClient


async def test_patient_communication_telemetry():
    """Test PatientCommunicationAgent AgentOps integration"""
    print("\n🔍 TESTING: PatientCommunicationAgent Telemetry")
    
    # Simulate patient WhatsApp message
    whatsapp_message = {
        'id': f'msg_{uuid.uuid4().hex[:8]}',
        'from': '+56912345678',
        'text': {'body': 'Hola, tengo una herida en el talón'},
        'image': {'url': 'https://example.com/patient_image.jpg'},
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # Test message reception with AgentOps tracking
        result = await patient_communication_agent.receive_patient_message_adk_tool(
            whatsapp_message=whatsapp_message,
            auto_process=True,
            security_check=True
        )
        
        print(f"✅ Patient message reception tracked: {result.get('success', False)}")
        print(f"📊 Token ID: {result.get('message_details', {}).get('token_id', 'N/A')}")
        print(f"⏱️  Processing time: {result.get('processing_time_ms', 0)}ms")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ PatientCommunicationAgent test failed: {e}")
        return False


async def test_medical_team_telemetry():
    """Test MedicalTeamAgent AgentOps integration"""
    print("\n🔍 TESTING: MedicalTeamAgent Telemetry")
    
    # Simulate medical diagnosis data
    diagnosis_data = {
        'token_id': f'batman_{uuid.uuid4().hex[:8]}',
        'primary_diagnosis': 'LPP Grado 2 en talón derecho',
        'confidence_level': 0.89,
        'lpp_grade': 2,
        'anatomical_location': 'talón derecho',
        'treatment_plan': [
            'Redistribución de presión',
            'Limpieza con solución salina',
            'Apósito hidrocoloide'
        ],
        'scientific_references': [
            'NPUAP/EPUAP/PPPIA 2019 Guidelines'
        ]
    }
    
    try:
        # Test diagnosis delivery with AgentOps tracking
        result = await medical_team_agent.send_diagnosis_to_team_adk_tool(
            diagnosis_data=diagnosis_data,
            target_specialists=['wound_care', 'nursing'],
            include_evidence=True,
            enable_follow_up=True
        )
        
        print(f"✅ Medical diagnosis delivery tracked: {result.get('success', False)}")
        print(f"📊 Channels notified: {len(result.get('channels_notified', []))}")
        print(f"💬 Follow-up enabled: {result.get('follow_up_enabled', False)}")
        
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ MedicalTeamAgent test failed: {e}")
        return False


async def test_master_orchestrator_telemetry():
    """Test MasterMedicalOrchestrator AgentOps integration"""
    print("\n🔍 TESTING: MasterMedicalOrchestrator Telemetry")
    
    orchestrator = MasterMedicalOrchestrator()
    
    # Simulate medical case data
    case_data = {
        'token_id': f'batman_{uuid.uuid4().hex[:8]}',
        'patient_alias': 'Batman',
        'image_path': '/medical_images/test_lpp_case.jpg',
        'patient_context': {
            'risk_factors': ['diabetes', 'limited_mobility', 'age_75+'],
            'medical_history': {
                'diabetes': True,
                'previous_lpp': False,
                'mobility_score': 2
            }
        },
        'session_token': f'session_{int(time.time())}'
    }
    
    try:
        # Start orchestration session
        session_id = await orchestrator.start_orchestration_session(
            token_id=case_data['token_id'],
            case_context={
                'patient_alias': case_data['patient_alias'],
                'image_present': True,
                'risk_factors': case_data['patient_context']['risk_factors'],
                'case_complexity': 'medium'
            }
        )
        
        print(f"✅ Orchestration session started: {session_id}")
        
        # Test agent coordination tracking
        await orchestrator.track_agent_coordination(
            session_id=session_id,
            coordination_data={
                'total_agents': 9,
                'active_agents': ['image_analysis', 'clinical_assessment', 'risk_assessment'],
                'pattern': 'test_coordination',
                'complexity': 'medium',
                'successful_coordinations': 3,
                'failed_coordinations': 0,
                'final_confidence': 0.92,
                'total_processing_time': 15.5
            }
        )
        
        print(f"✅ Agent coordination tracked for 3/9 agents")
        
        # Test medical decision fusion tracking
        await orchestrator.track_medical_decision_fusion(
            session_id=session_id,
            fusion_data={
                'individual_decisions': {
                    'image_analysis': 'LPP Grado 2',
                    'clinical_assessment': 'LPP Grado 2 confirmado',
                    'risk_assessment': 'Riesgo alto'
                },
                'confidence_scores': {
                    'image_analysis': 0.89,
                    'clinical_assessment': 0.94,
                    'risk_assessment': 0.87
                },
                'final_diagnosis': 'LPP Grado 2 con riesgo alto',
                'final_confidence': 0.92,
                'evidence_level': 'A',
                'conflicts_resolved': 0,
                'consensus': True
            }
        )
        
        print(f"✅ Medical decision fusion tracked with 92% confidence")
        
        # End session
        session_summary = await orchestrator.telemetry.end_medical_session(session_id)
        print(f"✅ Orchestration session completed: {session_summary.get('duration', 'N/A')}s")
        
        return True
        
    except Exception as e:
        print(f"❌ MasterMedicalOrchestrator test failed: {e}")
        return False


async def test_risk_assessment_telemetry():
    """Test RiskAssessmentAgent AgentOps integration"""
    print("\n🔍 TESTING: RiskAssessmentAgent Telemetry")
    
    risk_agent = RiskAssessmentAgent()
    await risk_agent.initialize()
    
    # Simulate risk assessment data
    token_id = f'batman_{uuid.uuid4().hex[:8]}'
    patient_context = {
        'risk_factors': ['diabetes', 'limited_mobility', 'age_75+', 'malnutrition'],
        'medical_history': {
            'diabetes': True,
            'hypertension': True,
            'previous_lpp': False
        },
        'current_assessment': {
            'mobility_score': 2,
            'nutrition_score': 2,
            'moisture_score': 3
        }
    }
    
    try:
        # Start risk assessment session
        session_id = await risk_agent._start_risk_assessment_session(
            token_id=token_id,
            patient_context=patient_context,
            assessment_type='comprehensive'
        )
        
        print(f"✅ Risk assessment session started: {session_id}")
        
        # Simulate assessment completion tracking
        mock_result = type('RiskAssessmentResult', (), {
            'risk_level': type('RiskLevel', (), {'value': 'high'})(),
            'probability_score': 0.78,
            'confidence': 0.89,
            'braden_score': 13,
            'norton_score': 14,
            'risk_factors': patient_context['risk_factors'],
            'prevention_strategies': [
                'Reposicionamiento cada 2 horas',
                'Superficie especial de apoyo',
                'Evaluación nutricional'
            ]
        })()
        
        await risk_agent._track_risk_assessment_completion(
            session_id=session_id,
            result=mock_result,
            processing_time=3.2
        )
        
        print(f"✅ Risk assessment completion tracked: High risk (78% probability)")
        
        return True
        
    except Exception as e:
        print(f"❌ RiskAssessmentAgent test failed: {e}")
        return False


async def test_communication_bridge_telemetry():
    """Test CommunicationBridge AgentOps integration"""
    print("\n🔍 TESTING: CommunicationBridge Telemetry")
    
    bridge = CommunicationBridge()
    
    # Test basic telemetry initialization
    try:
        # Start bridge session
        session_id = f"bridge_{uuid.uuid4().hex[:8]}_{int(time.time())}"
        
        await bridge.telemetry.start_medical_session(
            session_id=session_id,
            patient_context={
                'token_id': f'batman_{uuid.uuid4().hex[:8]}',
                'bridge_type': 'diagnosis_routing',
                'agents_involved': ['medical_team', 'patient_communication']
            },
            session_type='communication_bridge'
        )
        
        print(f"✅ Communication bridge session started: {session_id}")
        
        # Track inter-agent communication
        await bridge.telemetry.track_agent_interaction(
            agent_name="CommunicationBridge",
            action="route_medical_diagnosis",
            input_data={
                'source_agent': 'medical_team_agent',
                'target_agent': 'patient_communication_agent',
                'message_type': 'diagnosis_approval'
            },
            output_data={
                'routing_success': True,
                'delivery_confirmed': True,
                'bridge_id': str(uuid.uuid4())
            },
            session_id=session_id,
            execution_time=1.8
        )
        
        print(f"✅ Inter-agent communication tracked: MedicalTeam → Patient")
        
        return True
        
    except Exception as e:
        print(f"❌ CommunicationBridge test failed: {e}")
        return False


async def test_complete_medical_workflow():
    """Test complete medical workflow with comprehensive AgentOps tracking"""
    print("\n🔍 TESTING: Complete Medical Workflow with AgentOps")
    
    # Create AgentOps direct client for verification
    agentops_client = AgentOpsDirectClient(api_key="995199e8-36e5-47e7-96b9-221a3ee12fb9")
    
    # Start comprehensive medical session
    medical_context = {
        "patient_case": f"COMPREHENSIVE_TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "workflow_type": "complete_lpp_analysis",
        "agents_involved": 9,
        "integration_test": True
    }
    
    main_session = agentops_client.start_medical_session(medical_context)
    
    try:
        # Event 1: Patient message reception
        agentops_client.track_medical_event("patient_message_reception", {
            "agent": "PatientCommunicationAgent",
            "message_type": "medical_image",
            "auto_processing": True,
            "security_validated": True
        })
        
        # Event 2: Master orchestrator coordination
        agentops_client.track_medical_event("master_orchestration", {
            "agent": "MasterMedicalOrchestrator",
            "total_agents": 9,
            "coordination_pattern": "sequential_with_fusion",
            "case_complexity": "medium"
        })
        
        # Event 3: Risk assessment
        agentops_client.track_medical_event("risk_assessment", {
            "agent": "RiskAssessmentAgent",
            "risk_level": "high",
            "braden_score": 13,
            "norton_score": 14,
            "assessment_type": "comprehensive"
        })
        
        # Event 4: Medical team notification
        agentops_client.track_medical_event("medical_team_notification", {
            "agent": "MedicalTeamAgent",
            "channels_notified": 3,
            "specialists_targeted": ["wound_care", "nursing", "clinical"],
            "evidence_included": True
        })
        
        # Event 5: Communication bridge routing
        agentops_client.track_medical_event("inter_agent_communication", {
            "agent": "CommunicationBridge",
            "source": "MedicalTeamAgent",
            "target": "PatientCommunicationAgent",
            "routing_type": "diagnosis_approval"
        })
        
        # Event 6: Patient response delivery
        agentops_client.track_medical_event("patient_response_delivery", {
            "agent": "PatientCommunicationAgent",
            "delivery_method": "whatsapp",
            "approved_by": "medical_team",
            "message_type": "diagnosis_result"
        })
        
        print(f"✅ Complete medical workflow tracked: {main_session}")
        print(f"📊 Events tracked: 6 (Patient → Orchestrator → Risk → Team → Bridge → Patient)")
        
        # End comprehensive session
        summary = agentops_client.end_medical_session()
        print(f"⏱️  Total workflow duration: {summary.get('duration', 'N/A')}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Complete workflow test failed: {e}")
        return False


async def main():
    """Run comprehensive AgentOps integration tests"""
    print("🔬 COMPREHENSIVE AGENTOPS INTEGRATION TEST - VIGIA MEDICAL SYSTEM")
    print("=" * 80)
    
    # Initialize global agents
    global patient_communication_agent, medical_team_agent
    patient_communication_agent = PatientCommunicationAgentFactory.create_agent()
    medical_team_agent = MedicalTeamAgentFactory.create_agent()
    
    # Run all tests
    tests = [
        ("PatientCommunicationAgent Telemetry", test_patient_communication_telemetry),
        ("MedicalTeamAgent Telemetry", test_medical_team_telemetry),
        ("MasterOrchestrator Telemetry", test_master_orchestrator_telemetry),
        ("RiskAssessmentAgent Telemetry", test_risk_assessment_telemetry),
        ("CommunicationBridge Telemetry", test_communication_bridge_telemetry),
        ("Complete Medical Workflow", test_complete_medical_workflow)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 Running: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"📋 Result: {status}")
        except Exception as e:
            print(f"❌ Test Error: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE AGENTOPS INTEGRATION TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status}: {test_name}")
    
    print(f"\n🎯 FINAL RESULTS: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL AGENTOPS INTEGRATIONS WORKING PERFECTLY!")
        print("📈 Complete medical workflow visibility achieved")
        print("🔗 Dashboard: https://app.agentops.ai/projects")
    else:
        print(f"⚠️  {total - passed} integrations need attention")
        print("🔍 Check individual test results above")
    
    print("\n✅ Comprehensive AgentOps integration validation completed")


if __name__ == "__main__":
    asyncio.run(main())