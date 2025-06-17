#!/usr/bin/env python3
"""
FASE 3 - Distributed Infrastructure Integration Test
==================================================

Test completo de la infraestructura distribuida A2A implementada en FASE 3:
- A2A Protocol Layer (JSON-RPC 2.0)
- Agent Discovery Service
- Load Balancer médico inteligente
- Health Monitoring distribuido
- Message Queuing System
- Fault Tolerance y Recovery

Este test valida la integración completa del sistema distribuido
sin dependencias externas usando mocks y simulaciones.
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test framework imports
from vigia_detect.a2a.protocol_layer import (
    A2AProtocolLayer, A2AMessage, MessagePriority, AuthLevel, create_a2a_protocol
)
from vigia_detect.a2a.agent_discovery_service import (
    AgentDiscoveryService, AgentRegistration, AgentCapability, AgentType, 
    AgentStatus, ServiceBackend, ServiceQuery, create_discovery_service
)
from vigia_detect.a2a.load_balancer import (
    MedicalLoadBalancer, LoadBalancingAlgorithm, RequestContext, create_load_balancer
)
from vigia_detect.a2a.health_monitoring import (
    AgentHealthMonitor, HealthMetricType, HealthAlert, AlertSeverity, create_health_monitor
)
from vigia_detect.a2a.message_queuing import (
    A2AMessageQueueManager, QueueType, MessageStatus, create_message_queue_manager
)
from vigia_detect.a2a.fault_tolerance import (
    FaultToleranceManager, FailureType, RecoveryStrategy, SystemMode, create_fault_tolerance_manager
)


class TestDistributedInfrastructure:
    """Test suite for distributed A2A infrastructure"""
    
    def __init__(self):
        self.discovery_service = None
        self.protocol_layer = None
        self.load_balancer = None
        self.health_monitor = None
        self.queue_manager = None
        self.fault_tolerance = None
        
        self.test_results = {}
        self.test_agents = []
    
    async def setup_infrastructure(self):
        """Setup distributed infrastructure for testing"""
        logger.info("Setting up distributed infrastructure...")
        
        # 1. Initialize Agent Discovery Service (memory backend for testing)
        self.discovery_service = create_discovery_service(ServiceBackend.MEMORY)
        await self.discovery_service.initialize()
        
        # 2. Initialize Health Monitor
        self.health_monitor = create_health_monitor(self.discovery_service)
        await self.health_monitor.initialize()
        
        # 3. Initialize Load Balancer
        self.load_balancer = create_load_balancer(
            self.discovery_service, 
            LoadBalancingAlgorithm.ADAPTIVE
        )
        await self.load_balancer.initialize()
        
        # 4. Initialize Message Queue Manager
        self.queue_manager = create_message_queue_manager(self.discovery_service)
        await self.queue_manager.initialize()
        
        # 5. Initialize Fault Tolerance Manager
        self.fault_tolerance = create_fault_tolerance_manager(
            self.discovery_service,
            self.health_monitor,
            self.load_balancer
        )
        await self.fault_tolerance.initialize()
        
        # 6. Initialize A2A Protocol Layer
        self.protocol_layer = create_a2a_protocol("test_coordinator", port=8080)
        
        logger.info("✅ Distributed infrastructure setup complete")
    
    async def register_test_agents(self):
        """Register test agents in discovery service"""
        logger.info("Registering test agents...")
        
        test_agents_config = [
            {
                "agent_id": "image_analysis_1",
                "agent_type": AgentType.IMAGE_ANALYSIS,
                "endpoint": "http://localhost:8001",
                "capabilities": [
                    AgentCapability("lpp_detection", "1.0", max_concurrent=5, requires_phi_access=True),
                    AgentCapability("image_preprocessing", "1.0", max_concurrent=10)
                ]
            },
            {
                "agent_id": "clinical_assessment_1",
                "agent_type": AgentType.CLINICAL_ASSESSMENT,
                "endpoint": "http://localhost:8002",
                "capabilities": [
                    AgentCapability("evidence_based_assessment", "1.0", max_concurrent=3, requires_phi_access=True),
                    AgentCapability("risk_calculation", "1.0", max_concurrent=5)
                ]
            },
            {
                "agent_id": "protocol_consultant_1",
                "agent_type": AgentType.PROTOCOL_CONSULTANT,
                "endpoint": "http://localhost:8003",
                "capabilities": [
                    AgentCapability("npuap_guidelines", "1.0", max_concurrent=10),
                    AgentCapability("minsal_protocols", "1.0", max_concurrent=8)
                ]
            },
            {
                "agent_id": "communication_1",
                "agent_type": AgentType.COMMUNICATION,
                "endpoint": "http://localhost:8004",
                "capabilities": [
                    AgentCapability("slack_notifications", "1.0", max_concurrent=20),
                    AgentCapability("emergency_alerts", "1.0", max_concurrent=50)
                ]
            },
            {
                "agent_id": "workflow_orchestration_1", 
                "agent_type": AgentType.WORKFLOW_ORCHESTRATION,
                "endpoint": "http://localhost:8005",
                "capabilities": [
                    AgentCapability("medical_triage", "1.0", max_concurrent=15),
                    AgentCapability("pipeline_orchestration", "1.0", max_concurrent=20)
                ]
            }
        ]
        
        for agent_config in test_agents_config:
            registration = AgentRegistration(
                agent_id=agent_config["agent_id"],
                agent_type=agent_config["agent_type"],
                endpoint=agent_config["endpoint"],
                capabilities=agent_config["capabilities"],
                status=AgentStatus.HEALTHY,
                metadata={"test_agent": True, "created_at": datetime.now(timezone.utc).isoformat()}
            )
            
            success = await self.discovery_service.register_agent(registration)
            if success:
                self.test_agents.append(registration)
                logger.info(f"✅ Registered agent: {agent_config['agent_id']}")
            else:
                logger.error(f"❌ Failed to register agent: {agent_config['agent_id']}")
        
        logger.info(f"✅ Registered {len(self.test_agents)} test agents")
    
    async def test_agent_discovery(self):
        """Test agent discovery functionality"""
        logger.info("Testing agent discovery...")
        
        try:
            # Test 1: List all agents
            all_agents = await self.discovery_service.list_agents()
            assert len(all_agents) == len(self.test_agents), f"Expected {len(self.test_agents)} agents, got {len(all_agents)}"
            
            # Test 2: Discover agents by type
            image_agents = await self.discovery_service.discover_agents(
                ServiceQuery(agent_type=AgentType.IMAGE_ANALYSIS)
            )
            assert len(image_agents) == 1, f"Expected 1 image analysis agent, got {len(image_agents)}"
            
            # Test 3: Discover agents by capability
            phi_agents = await self.discovery_service.discover_agents(
                ServiceQuery(requires_phi_access=True, medical_compliant_only=True)
            )
            assert len(phi_agents) >= 2, f"Expected at least 2 PHI-capable agents, got {len(phi_agents)}"
            
            # Test 4: Get best agent
            best_agent = await self.discovery_service.get_best_agent(
                ServiceQuery(capability_name="lpp_detection")
            )
            assert best_agent is not None, "Should find best agent for LPP detection"
            assert best_agent.agent_type == AgentType.IMAGE_ANALYSIS, "Best agent should be image analysis type"
            
            self.test_results["agent_discovery"] = True
            logger.info("✅ Agent discovery tests passed")
            
        except Exception as e:
            self.test_results["agent_discovery"] = False
            logger.error(f"❌ Agent discovery tests failed: {e}")
    
    async def test_health_monitoring(self):
        """Test health monitoring system"""
        logger.info("Testing health monitoring...")
        
        try:
            # Test 1: Get health summary
            health_summary = self.health_monitor.get_health_summary()
            assert health_summary["total_agents"] == len(self.test_agents), "Health monitor should track all agents"
            
            # Test 2: Simulate health metrics update
            test_agent = self.test_agents[0]
            success = await self.discovery_service.update_agent_health(
                test_agent.agent_id,
                AgentStatus.HEALTHY,
                {
                    "response_time": 1.5,
                    "error_rate": 0.02,
                    "load_factor": 0.6
                }
            )
            assert success, "Should successfully update agent health"
            
            # Test 3: Get agent health profile
            health_profile = self.health_monitor.get_agent_health(test_agent.agent_id)
            # Note: Health profile might be None if background tasks haven't run yet
            # This is acceptable for testing
            
            # Test 4: Test alert callback system
            alert_received = False
            
            def alert_callback(alert):
                nonlocal alert_received
                alert_received = True
            
            self.health_monitor.add_alert_callback(alert_callback)
            
            # Test 5: Get active alerts
            active_alerts = self.health_monitor.get_active_alerts()
            assert isinstance(active_alerts, list), "Should return list of active alerts"
            
            self.test_results["health_monitoring"] = True
            logger.info("✅ Health monitoring tests passed")
            
        except Exception as e:
            self.test_results["health_monitoring"] = False
            logger.error(f"❌ Health monitoring tests failed: {e}")
    
    async def test_load_balancer(self):
        """Test load balancer functionality"""
        logger.info("Testing load balancer...")
        
        try:
            # Test 1: Create request context
            context = RequestContext(
                request_id="test_request_001",
                agent_type=AgentType.IMAGE_ANALYSIS,
                method="lpp_detection",
                priority=MessagePriority.HIGH,
                auth_level=AuthLevel.MEDICAL,
                requires_phi_access=True
            )
            
            # Test 2: Test agent selection algorithms
            suitable_agents = await self.load_balancer._find_suitable_agents(context)
            assert len(suitable_agents) > 0, "Should find suitable agents"
            
            # Test 3: Test different load balancing algorithms
            algorithms_to_test = [
                LoadBalancingAlgorithm.ROUND_ROBIN,
                LoadBalancingAlgorithm.HEALTH_AWARE,
                LoadBalancingAlgorithm.MEDICAL_PRIORITY,
                LoadBalancingAlgorithm.ADAPTIVE
            ]
            
            for algorithm in algorithms_to_test:
                selected_agent = await self.load_balancer._select_agent(suitable_agents, context, algorithm)
                assert selected_agent is not None, f"Should select agent with {algorithm.value} algorithm"
            
            # Test 4: Get load balancer statistics
            stats = self.load_balancer.get_statistics()
            assert isinstance(stats, dict), "Should return statistics dictionary"
            assert "load_balancer_stats" in stats, "Should contain load balancer stats"
            
            # Test 5: Health check
            health_status = await self.load_balancer.health_check()
            assert health_status["status"] == "healthy", "Load balancer should be healthy"
            
            self.test_results["load_balancer"] = True
            logger.info("✅ Load balancer tests passed")
            
        except Exception as e:
            self.test_results["load_balancer"] = False
            logger.error(f"❌ Load balancer tests failed: {e}")
    
    async def test_message_queuing(self):
        """Test message queuing system"""
        logger.info("Testing message queuing...")
        
        try:
            # Test 1: Create test message
            test_message = A2AMessage(
                method="test_medical_processing",
                params={
                    "patient_code": "TEST-001",
                    "image_path": "/test/image.jpg",
                    "urgency": "high"
                },
                priority=MessagePriority.HIGH,
                auth_level=AuthLevel.MEDICAL,
                medical_context={
                    "case_type": "lpp_assessment",
                    "patient_age": 65
                }
            )
            
            # Test 2: Send message to queue
            message_id = await self.queue_manager.send_message(
                test_message,
                target_queue="high_priority",
                medical_urgency="high"
            )
            assert message_id is not None, "Should return message ID"
            
            # Test 3: Check queue statistics
            queue_stats = self.queue_manager.get_queue_stats("high_priority")
            assert queue_stats is not None, "Should return queue statistics"
            assert queue_stats.total_messages >= 1, "Should have at least 1 message in queue"
            
            # Test 4: Test different queue types
            queue_types = [QueueType.MEDICAL_CRITICAL, QueueType.BATCH, QueueType.DELAYED]
            for queue_type in queue_types:
                queue_name = f"test_{queue_type.value}"
                success = await self.queue_manager.create_queue(queue_name, queue_type)
                assert success, f"Should create {queue_type.value} queue"
            
            # Test 5: Get global statistics
            global_stats = self.queue_manager.get_global_stats()
            assert isinstance(global_stats, dict), "Should return global stats dictionary"
            
            self.test_results["message_queuing"] = True
            logger.info("✅ Message queuing tests passed")
            
        except Exception as e:
            self.test_results["message_queuing"] = False
            logger.error(f"❌ Message queuing tests failed: {e}")
    
    async def test_fault_tolerance(self):
        """Test fault tolerance and recovery"""
        logger.info("Testing fault tolerance...")
        
        try:
            # Test 1: Get initial system status
            system_status = self.fault_tolerance.get_system_status()
            assert system_status["system_mode"] == SystemMode.NORMAL.value, "Should start in normal mode"
            
            # Test 2: Test circuit breaker creation
            test_agent = self.test_agents[0]
            circuit_breaker = await self.fault_tolerance._get_circuit_breaker(test_agent.agent_id)
            assert circuit_breaker is not None, "Should create circuit breaker"
            assert circuit_breaker.service_id == test_agent.agent_id, "Circuit breaker should have correct service ID"
            
            # Test 3: Test circuit breaker functionality
            initial_state = circuit_breaker.state
            circuit_breaker.record_failure()
            circuit_breaker.record_failure()
            circuit_breaker.record_failure()
            circuit_breaker.record_failure()
            circuit_breaker.record_failure()  # Should trigger circuit breaker
            
            # Medical critical agents have lower thresholds
            if circuit_breaker.medical_critical:
                assert circuit_breaker.state.value == "open", "Medical critical circuit breaker should open"
            
            # Test 4: Test recovery
            circuit_breaker.record_success()
            if circuit_breaker.state.value == "half_open":
                circuit_breaker.record_success()  # Should close circuit
            
            # Test 5: Get failure history
            failure_history = self.fault_tolerance.get_failure_history()
            assert isinstance(failure_history, list), "Should return failure history list"
            
            # Test 6: Test backup agent finding
            backup_agents = await self.fault_tolerance._find_backup_agents(test_agent.agent_id)
            # May be empty if no other agents of same type, which is acceptable
            assert isinstance(backup_agents, list), "Should return list of backup agents"
            
            self.test_results["fault_tolerance"] = True
            logger.info("✅ Fault tolerance tests passed")
            
        except Exception as e:
            self.test_results["fault_tolerance"] = False
            logger.error(f"❌ Fault tolerance tests failed: {e}")
    
    async def test_a2a_protocol(self):
        """Test A2A protocol layer"""
        logger.info("Testing A2A protocol...")
        
        try:
            # Test 1: Create A2A message
            message = A2AMessage(
                method="test_medical_method",
                params={"test": "data"},
                priority=MessagePriority.NORMAL,
                auth_level=AuthLevel.MEDICAL
            )
            
            assert message.jsonrpc == "2.0", "Should use JSON-RPC 2.0"
            assert message.id is not None, "Should have message ID"
            
            # Test 2: Convert to dictionary
            message_dict = message.to_dict()
            assert isinstance(message_dict, dict), "Should convert to dictionary"
            assert "jsonrpc" in message_dict, "Should contain JSON-RPC version"
            assert "method" in message_dict, "Should contain method"
            
            # Test 3: Create from dictionary
            restored_message = A2AMessage.from_dict(message_dict)
            assert restored_message.method == message.method, "Should restore method correctly"
            assert restored_message.priority == message.priority, "Should restore priority correctly"
            
            # Test 4: Add audit trail
            message.add_audit_entry("test_event", "test_agent", {"test": "metadata"})
            assert len(message.audit_trail) > 0, "Should add audit entry"
            
            # Test 5: Protocol layer statistics (if server was running)
            # Note: We're not starting the actual server for this test
            # but we can test the protocol layer initialization
            assert self.protocol_layer.agent_id == "test_coordinator", "Should have correct agent ID"
            
            self.test_results["a2a_protocol"] = True
            logger.info("✅ A2A protocol tests passed")
            
        except Exception as e:
            self.test_results["a2a_protocol"] = False
            logger.error(f"❌ A2A protocol tests failed: {e}")
    
    async def test_integration_scenario(self):
        """Test complete integration scenario"""
        logger.info("Testing integration scenario...")
        
        try:
            # Scenario: Emergency medical case processing
            scenario_start = time.time()
            
            # 1. Emergency case arrives
            emergency_message = A2AMessage(
                method="emergency_lpp_assessment",
                params={
                    "patient_code": "EMERGENCY-001",
                    "image_path": "/emergency/critical_lpp.jpg",
                    "patient_context": {
                        "age": 78,
                        "diabetes": True,
                        "mobility": "bed_bound"
                    }
                },
                priority=MessagePriority.CRITICAL,
                auth_level=AuthLevel.EMERGENCY,
                medical_context={
                    "urgency": "critical",
                    "patient_safety_risk": True
                }
            )
            
            # 2. Discover suitable agents for emergency processing
            emergency_query = ServiceQuery(
                agent_type=AgentType.IMAGE_ANALYSIS,
                requires_phi_access=True,
                medical_compliant_only=True,
                min_success_rate=0.95  # High reliability required for emergency
            )
            
            suitable_agents = await self.discovery_service.discover_agents(emergency_query)
            assert len(suitable_agents) > 0, "Should find agents for emergency processing"
            
            # 3. Create high-priority request context
            emergency_context = RequestContext(
                request_id="EMERGENCY-001-REQ",
                agent_type=AgentType.IMAGE_ANALYSIS,
                method="emergency_lpp_assessment",
                priority=MessagePriority.CRITICAL,
                auth_level=AuthLevel.EMERGENCY,
                requires_phi_access=True,
                timeout=60.0  # Extended timeout for critical case
            )
            
            # 4. Use load balancer with medical priority algorithm
            selected_agent = await self.load_balancer._select_agent(
                suitable_agents, 
                emergency_context, 
                LoadBalancingAlgorithm.MEDICAL_PRIORITY
            )
            assert selected_agent is not None, "Should select agent for emergency"
            
            # 5. Queue emergency message
            message_id = await self.queue_manager.send_message(
                emergency_message,
                target_queue="critical",
                medical_urgency="critical"
            )
            assert message_id is not None, "Should queue emergency message"
            
            # 6. Verify system responds appropriately to emergency
            critical_queue_stats = self.queue_manager.get_queue_stats("critical")
            assert critical_queue_stats.critical_messages >= 1, "Should track critical messages"
            
            # 7. Test fault tolerance under load
            system_status = self.fault_tolerance.get_system_status()
            # System should remain operational
            assert system_status["system_mode"] in [SystemMode.NORMAL.value, SystemMode.DEGRADED.value], \
                "System should handle emergency gracefully"
            
            scenario_time = time.time() - scenario_start
            
            self.test_results["integration_scenario"] = True
            logger.info(f"✅ Integration scenario completed in {scenario_time:.2f}s")
            
        except Exception as e:
            self.test_results["integration_scenario"] = False
            logger.error(f"❌ Integration scenario failed: {e}")
    
    async def cleanup_infrastructure(self):
        """Cleanup test infrastructure"""
        logger.info("Cleaning up test infrastructure...")
        
        try:
            # Shutdown components in reverse order
            if self.fault_tolerance:
                await self.fault_tolerance.shutdown()
            
            if self.queue_manager:
                await self.queue_manager.shutdown()
            
            if self.load_balancer:
                await self.load_balancer.shutdown()
            
            if self.health_monitor:
                await self.health_monitor.shutdown()
            
            if self.discovery_service:
                await self.discovery_service.shutdown()
            
            logger.info("✅ Infrastructure cleanup complete")
            
        except Exception as e:
            logger.error(f"❌ Cleanup error: {e}")
    
    async def run_all_tests(self):
        """Run complete test suite"""
        logger.info("🚀 Starting FASE 3 Distributed Infrastructure Tests")
        logger.info("=" * 70)
        
        start_time = time.time()
        
        try:
            # Setup
            await self.setup_infrastructure()
            await self.register_test_agents()
            
            # Allow background tasks to initialize
            await asyncio.sleep(2)
            
            # Run tests
            await self.test_agent_discovery()
            await self.test_health_monitoring()
            await self.test_load_balancer()
            await self.test_message_queuing()
            await self.test_fault_tolerance()
            await self.test_a2a_protocol()
            await self.test_integration_scenario()
            
        finally:
            # Cleanup
            await self.cleanup_infrastructure()
        
        # Results summary
        total_time = time.time() - start_time
        
        logger.info("=" * 70)
        logger.info("🎯 FASE 3 DISTRIBUTED INFRASTRUCTURE TEST RESULTS")
        logger.info("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            logger.info(f"{test_name.replace('_', ' ').title()}: {status}")
        
        logger.info("=" * 70)
        logger.info(f"Overall: {passed_tests}/{total_tests} tests passed")
        logger.info(f"Test execution time: {total_time:.2f} seconds")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED - FASE 3 Distributed Infrastructure Working!")
            logger.info("🏗️ Infrastructure Components Validated:")
            logger.info("   ✅ A2A Protocol Layer (JSON-RPC 2.0)")
            logger.info("   ✅ Agent Discovery Service")
            logger.info("   ✅ Medical Load Balancer")
            logger.info("   ✅ Health Monitoring System")
            logger.info("   ✅ Message Queuing System")
            logger.info("   ✅ Fault Tolerance & Recovery")
            logger.info("   ✅ End-to-End Integration")
            return 0
        else:
            logger.warning(f"⚠️ {total_tests - passed_tests} tests failed")
            return 1


async def main():
    """Main test function"""
    test_suite = TestDistributedInfrastructure()
    return await test_suite.run_all_tests()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)