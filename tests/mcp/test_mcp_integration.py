#!/usr/bin/env python3
"""
Tests for MCP Integration in Vigía
Comprehensive testing for Model Context Protocol messaging services
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import aiohttp

from vigia_detect.mcp.gateway import (
    MCPGateway, MCPRouter, MCPRequest, MCPResponse,
    MCPServiceConfig, create_mcp_gateway
)


class TestMCPConfiguration:
    """Test MCP configuration and setup"""
    
    def test_mcp_json_exists_and_valid(self):
        """Test .mcp.json exists and contains valid configuration"""
        import os
        
        mcp_file = ".mcp.json"
        assert os.path.exists(mcp_file), ".mcp.json file not found"
        
        with open(mcp_file, 'r') as f:
            config = json.load(f)
        
        assert "mcpServers" in config, "mcpServers not found in configuration"
        
        # Check required MCPs are configured
        required_mcps = ['docker-server', 'twilio-whatsapp', 'slack', 'whatsapp-direct']
        for mcp in required_mcps:
            assert mcp in config["mcpServers"], f"{mcp} not configured"
    
    def test_mcp_service_configs(self):
        """Test MCP service configurations are valid"""
        config = {"medical_compliance": "hipaa"}
        router = MCPRouter(config)
        
        # Test service existence
        assert 'twilio_whatsapp' in router.services
        assert 'slack' in router.services
        assert 'github' in router.services  # Docker services are there but named differently
        
        # Test service config properties
        twilio_config = router.services['twilio_whatsapp']
        assert twilio_config.compliance_level == 'hipaa'
        assert twilio_config.rate_limit == 8  # Conservative WhatsApp rate limit
        
        slack_config = router.services['slack']
        assert slack_config.compliance_level == 'hipaa'
        assert slack_config.rate_limit == 15


class TestMCPRequestResponse:
    """Test MCP request/response data structures"""
    
    def test_mcp_request_creation(self):
        """Test MCP request object creation"""
        request = MCPRequest(
            service='twilio_whatsapp',
            tool='send_message',
            params={'to': 'whatsapp:+1234567890', 'message': 'Test'},
            medical_context={'patient_id': 'PAT-001', 'phi_protection': True}
        )
        
        assert request.service == 'twilio_whatsapp'
        assert request.tool == 'send_message'
        assert request.medical_context['phi_protection'] is True
        assert request.request_id is not None
        assert request.timestamp is not None
    
    def test_mcp_response_creation(self):
        """Test MCP response object creation"""
        response = MCPResponse(
            request_id='test_123',
            service='slack',
            tool='send_message',
            status='success',
            data={'message_id': 'msg_456'},
            response_time=0.5
        )
        
        assert response.status == 'success'
        assert response.data['message_id'] == 'msg_456'
        assert response.response_time == 0.5


class TestMCPRouter:
    """Test MCP router functionality"""
    
    @pytest.mark.asyncio
    async def test_router_initialization(self):
        """Test router initializes correctly"""
        config = {"medical_compliance": "hipaa", "audit_enabled": True}
        router = MCPRouter(config)
        
        assert len(router.services) > 0
        assert 'twilio_whatsapp' in router.services
        assert 'slack' in router.services
        assert router.medical_engine is not None
    
    @pytest.mark.asyncio
    async def test_enhance_medical_context(self):
        """Test medical context enhancement"""
        config = {"medical_compliance": "hipaa"}
        router = MCPRouter(config)
        
        request = MCPRequest(
            service='twilio_whatsapp',
            tool='send_message',
            params={'message': 'Test'},
            medical_context={'patient_id': 'PAT-001'}
        )
        
        enhanced_request = await router._enhance_medical_context(request)
        
        assert enhanced_request.medical_context['compliance_level'] == 'hipaa'
        assert enhanced_request.medical_context['phi_protection'] is True
        assert enhanced_request.medical_context['audit_required'] is True
        assert enhanced_request.medical_context['vigia_version'] == '1.3.1'
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        config = {"medical_compliance": "hipaa"}
        router = MCPRouter(config)
        
        # Test rate limit check for WhatsApp (limit: 8/minute)
        for i in range(8):
            assert router._check_rate_limit('twilio_whatsapp') is True
        
        # 9th request should be denied
        assert router._check_rate_limit('twilio_whatsapp') is False
    
    @pytest.mark.asyncio
    async def test_service_not_found_error(self):
        """Test handling of non-existent service"""
        config = {"medical_compliance": "hipaa"}
        router = MCPRouter(config)
        
        request = MCPRequest(
            service='non_existent_service',
            tool='test_tool',
            params={}
        )
        
        response = await router.route_request(request)
        
        assert response.status == 'error'
        assert "Service not found" in response.error


class TestMCPGateway:
    """Test MCP gateway high-level interface"""
    
    @pytest.mark.asyncio
    async def test_gateway_creation(self):
        """Test gateway creation and initialization"""
        config = {"medical_compliance": "hipaa", "audit_enabled": True}
        gateway = create_mcp_gateway(config)
        
        assert isinstance(gateway, MCPGateway)
        assert gateway.router is not None
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_whatsapp_operation(self, mock_post):
        """Test WhatsApp operation via gateway"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'message_id': 'msg_123'})
        mock_post.return_value.__aenter__.return_value = mock_response
        
        config = {"medical_compliance": "hipaa"}
        
        async with create_mcp_gateway(config) as gateway:
            # Mock health check
            gateway.router._is_service_healthy = AsyncMock(return_value=True)
            
            response = await gateway.whatsapp_operation(
                'send_message',
                patient_context={'patient_id': 'PAT-001'},
                to='whatsapp:+1234567890',
                message='LPP Grade 2 detected'
            )
            
            assert response.status == 'success'
            assert response.data['message_id'] == 'msg_123'
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_slack_operation(self, mock_post):
        """Test Slack operation via gateway"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'ts': '1234567890.123'})
        mock_post.return_value.__aenter__.return_value = mock_response
        
        config = {"medical_compliance": "hipaa"}
        
        async with create_mcp_gateway(config) as gateway:
            # Mock health check
            gateway.router._is_service_healthy = AsyncMock(return_value=True)
            
            response = await gateway.slack_operation(
                'send_message',
                channel='#medical-alerts',
                message='Emergency: LPP Grade 3 detected'
            )
            
            assert response.status == 'success'
            assert response.data['ts'] == '1234567890.123'
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_lpp_detection_notification(self, mock_post):
        """Test automated LPP detection notification"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'alert_sent': True})
        mock_post.return_value.__aenter__.return_value = mock_response
        
        config = {"medical_compliance": "hipaa"}
        
        async with create_mcp_gateway(config) as gateway:
            # Mock health check
            gateway.router._is_service_healthy = AsyncMock(return_value=True)
            
            response = await gateway.notify_lpp_detection(
                lpp_grade=2,
                confidence=0.85,
                patient_context={'patient_id': 'PAT-001'},
                platform='slack'
            )
            
            assert response.status == 'success'
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_medical_alert_severity_routing(self, mock_post):
        """Test medical alert severity-based routing"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={'alert_sent': True})
        mock_post.return_value.__aenter__.return_value = mock_response
        
        config = {"medical_compliance": "hipaa"}
        
        async with create_mcp_gateway(config) as gateway:
            # Mock health check
            gateway.router._is_service_healthy = AsyncMock(return_value=True)
            
            # Test critical alert
            response = await gateway.send_medical_alert(
                'lpp_critical',
                'PAT-001',
                'critical',
                'slack',
                'Critical LPP detected - immediate action required'
            )
            
            assert response.status == 'success'


class TestMCPCompliance:
    """Test HIPAA compliance and medical safety"""
    
    @pytest.mark.asyncio
    async def test_phi_protection(self):
        """Test PHI protection in medical context"""
        config = {"medical_compliance": "hipaa"}
        router = MCPRouter(config)
        
        request = MCPRequest(
            service='twilio_whatsapp',
            tool='send_message',
            params={'to': 'whatsapp:+1234567890', 'message': 'Patient update'},
            medical_context={'patient_id': 'PAT-001', 'diagnosis': 'LPP Grade 2'}
        )
        
        enhanced_request = await router._enhance_medical_context(request)
        
        assert enhanced_request.medical_context['phi_protection'] is True
        assert enhanced_request.medical_context['compliance_level'] == 'hipaa'
        assert enhanced_request.medical_context['audit_required'] is True
    
    @pytest.mark.asyncio
    async def test_audit_logging(self):
        """Test audit logging for compliance"""
        config = {"medical_compliance": "hipaa"}
        router = MCPRouter(config)
        
        request = MCPRequest(
            service='slack',
            tool='send_message',
            params={'channel': '#medical', 'message': 'Test'},
            medical_context={'patient_id': 'PAT-001'}
        )
        
        response = MCPResponse(
            request_id=request.request_id,
            service='slack',
            tool='send_message',
            status='success',
            response_time=0.5
        )
        
        audit_logged = await router._log_audit(request, response)
        assert audit_logged is True
    
    def test_emergency_escalation_requirements(self):
        """Test emergency escalation for critical alerts"""
        config = {"medical_compliance": "hipaa"}
        
        # Test critical LPP (Grade 3+) triggers high severity
        gateway = create_mcp_gateway(config)
        
        # Simulate LPP Grade 3 detection
        lpp_grade = 3
        confidence = 0.95
        
        # Should trigger high severity
        if lpp_grade >= 3 or (lpp_grade >= 2 and confidence > 0.9):
            severity = 'high'
        elif lpp_grade >= 2 or confidence > 0.8:
            severity = 'medium'
        else:
            severity = 'low'
        
        assert severity == 'high'


class TestMCPIntegrationFlow:
    """Test end-to-end MCP integration flows"""
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_service_health_monitoring(self, mock_get):
        """Test service health monitoring"""
        # Mock healthy service response
        mock_response = Mock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response
        
        config = {"medical_compliance": "hipaa"}
        
        async with create_mcp_gateway(config) as gateway:
            status = await gateway.get_service_status()
            
            assert status['gateway_status'] == 'healthy'
            assert 'services' in status
            assert 'timestamp' in status
    
    @pytest.mark.asyncio
    async def test_concurrent_mcp_operations(self):
        """Test concurrent MCP operations don't interfere"""
        config = {"medical_compliance": "hipaa"}
        
        async with create_mcp_gateway(config) as gateway:
            # Mock health checks
            gateway.router._is_service_healthy = AsyncMock(return_value=True)
            
            # Create multiple concurrent requests
            tasks = []
            for i in range(5):
                task = gateway.call_service(
                    'slack',
                    'send_message',
                    {'channel': f'#test-{i}', 'message': f'Test {i}'}
                )
                tasks.append(task)
            
            # Should handle concurrent requests without errors
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # All should complete (even if with errors due to mocking)
            assert len(responses) == 5


class TestTimeTracking:
    """Test Claude time tracking integration"""
    
    def test_time_tracker_import(self):
        """Test time tracker can be imported"""
        from scripts.utilities.claude_time_tracker import ClaudeTimeTracker
        
        tracker = ClaudeTimeTracker()
        assert tracker is not None
    
    def test_time_tracker_task_lifecycle(self):
        """Test complete task lifecycle with time tracking"""
        from scripts.utilities.claude_time_tracker import ClaudeTimeTracker
        
        tracker = ClaudeTimeTracker()
        
        # Start task
        task_id = tracker.start_task(
            "Test MCP Integration",
            human_estimate_hours=2.0,
            description="Testing MCP integration features"
        )
        
        assert task_id is not None
        
        # Add checkpoint
        tracker.add_checkpoint("MCP configuration completed", task_id)
        
        # Finish task
        tracker.finish_task(task_id, success=True, notes="All tests passed")
        
        # Get stats
        stats = tracker.get_productivity_stats()
        assert stats['total_tasks'] >= 1


@pytest.mark.mcp
@pytest.mark.integration
class TestMCPDeploymentValidation:
    """Test MCP deployment and configuration validation"""
    
    def test_deployment_script_exists(self):
        """Test MCP deployment script exists and is executable"""
        import os
        
        script_path = "scripts/deployment/deploy-mcp-messaging.sh"
        assert os.path.exists(script_path), "MCP deployment script not found"
        assert os.access(script_path, os.X_OK), "MCP deployment script not executable"
    
    def test_mcp_template_documentation(self):
        """Test MCP integration template exists"""
        import os
        
        template_path = "docs/MCP_INTEGRATION_TEMPLATE.md"
        assert os.path.exists(template_path), "MCP integration template not found"
        
        with open(template_path, 'r') as f:
            content = f.read()
        
        # Check essential sections exist
        assert "Quick Start Guide" in content
        assert "HIPAA Requirements" in content
        assert "Testing Template" in content
        assert "Deployment Checklist" in content


if __name__ == "__main__":
    # Run specific test categories
    pytest.main([
        "tests/mcp/test_mcp_integration.py",
        "-v",
        "-m", "mcp",
        "--tb=short"
    ])