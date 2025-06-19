#!/usr/bin/env python3
"""
Vigia MCP Gateway
Unified router for Docker Hub MCP services + Custom Medical MCP servers
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import aiohttp
from urllib.parse import urljoin

from ..utils.shared_utilities import VigiaLogger
from ..systems.medical_decision_engine import MedicalDecisionEngine
from ..slack.block_kit_medical import BlockKitMedical, BlockKitInteractions

logger = VigiaLogger.get_logger(__name__)


@dataclass
class MCPServiceConfig:
    """Configuration for MCP service"""
    name: str
    endpoint: str
    service_type: str  # 'hub' or 'custom'
    compliance_level: str
    timeout: int = 30
    max_retries: int = 3
    rate_limit: int = 10
    enabled: bool = True


@dataclass
class MCPRequest:
    """Standardized MCP request format"""
    service: str
    tool: str
    params: Dict[str, Any]
    medical_context: Optional[Dict[str, Any]] = None
    request_id: str = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.request_id is None:
            self.request_id = f"mcp_{int(time.time() * 1000)}"
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass 
class MCPResponse:
    """Standardized MCP response format"""
    request_id: str
    service: str
    tool: str
    status: str  # 'success', 'error', 'timeout'
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    response_time: float = 0.0
    compliance_validated: bool = False
    audit_logged: bool = False


class MCPRouter:
    """
    Central router for MCP services
    Handles routing between Docker Hub MCP and Custom Medical MCP servers
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.medical_engine = MedicalDecisionEngine()
        
        # Service configurations
        self.services = self._setup_services()
        
        # Rate limiting
        self.rate_limits = {}
        
        # Health status
        self.service_health = {}
        
        # Session for HTTP requests
        self.session = None
        
        logger.info(f"MCP Router initialized with {len(self.services)} services")
    
    def _setup_services(self) -> Dict[str, MCPServiceConfig]:
        """Setup service configurations"""
        services = {}
        
        # Docker Hub MCP Services
        hub_services = {
            'github': MCPServiceConfig(
                name='mcp-github',
                endpoint='http://mcp-github:8080',
                service_type='hub',
                compliance_level='hipaa',
                timeout=30,
                rate_limit=10
            ),
            'supabase': MCPServiceConfig(
                name='mcp-supabase',
                endpoint='http://mcp-supabase:8080',
                service_type='hub',
                compliance_level='hipaa',
                timeout=30,
                rate_limit=25
            ),
            'postgres': MCPServiceConfig(
                name='mcp-postgres',
                endpoint='http://mcp-postgres:8080',
                service_type='hub',
                compliance_level='hipaa',
                timeout=30,
                rate_limit=30
            ),
            'google_cloud': MCPServiceConfig(
                name='mcp-google-cloud',
                endpoint='http://mcp-google-cloud:8080',
                service_type='hub',
                compliance_level='hipaa',
                timeout=30,
                rate_limit=20
            ),
            'sendgrid': MCPServiceConfig(
                name='mcp-sendgrid',
                endpoint='http://mcp-sendgrid:8080',
                service_type='hub',
                compliance_level='hipaa',
                timeout=30,
                rate_limit=10
            ),
            'aws': MCPServiceConfig(
                name='mcp-aws',
                endpoint='http://mcp-aws:8080',
                service_type='hub',
                compliance_level='hipaa',
                timeout=30,
                rate_limit=25
            ),
            'sentry': MCPServiceConfig(
                name='mcp-sentry',
                endpoint='http://mcp-sentry:8080',
                service_type='hub',
                compliance_level='standard',
                timeout=30,
                rate_limit=15
            ),
            'stripe': MCPServiceConfig(
                name='mcp-stripe', 
                endpoint='http://mcp-stripe:8080',
                service_type='hub',
                compliance_level='pci-dss',
                timeout=30,
                rate_limit=5
            ),
            'redis': MCPServiceConfig(
                name='mcp-redis',
                endpoint='http://mcp-redis:8080', 
                service_type='hub',
                compliance_level='hipaa',
                timeout=15,
                rate_limit=50
            ),
            'mongodb': MCPServiceConfig(
                name='mcp-mongodb',
                endpoint='http://mcp-mongodb:8080',
                service_type='hub', 
                compliance_level='hipaa',
                timeout=30,
                rate_limit=20
            ),
            'twilio_whatsapp': MCPServiceConfig(
                name='mcp-twilio-whatsapp',
                endpoint='http://mcp-twilio-whatsapp:8080',
                service_type='hub',
                compliance_level='hipaa',
                timeout=45,
                rate_limit=8  # Conservative rate limit for WhatsApp
            ),
            'whatsapp_direct': MCPServiceConfig(
                name='mcp-whatsapp-direct',
                endpoint='http://mcp-whatsapp-direct:8080',
                service_type='hub',
                compliance_level='hipaa',
                timeout=60,
                rate_limit=5  # Very conservative for direct WhatsApp Web
            ),
            'slack': MCPServiceConfig(
                name='mcp-slack',
                endpoint='http://mcp-slack:8080',
                service_type='hub',
                compliance_level='hipaa',
                timeout=30,
                rate_limit=15
            )
        }
        
        # Custom Medical MCP Services
        medical_services = {
            'lpp_detection': MCPServiceConfig(
                name='vigia-lpp-detector',
                endpoint='http://vigia-lpp-detector:8080',
                service_type='custom',
                compliance_level='hipaa',
                timeout=60,
                rate_limit=10
            ),
            'vigia_fhir': MCPServiceConfig(
                name='vigia-fhir-server',
                endpoint='http://vigia-fhir-server:8080',
                service_type='custom',
                compliance_level='hipaa',
                timeout=45,
                rate_limit=20
            ),
            'vigia_minsal': MCPServiceConfig(
                name='vigia-minsal-server',
                endpoint='http://vigia-minsal-server:8080',
                service_type='custom',
                compliance_level='hipaa',
                timeout=30,
                rate_limit=15
            ),
            'vigia_redis': MCPServiceConfig(
                name='vigia-redis-server',
                endpoint='http://vigia-redis-server:8080',
                service_type='custom',
                compliance_level='hipaa',
                timeout=20,
                rate_limit=50
            ),
            'vigia_medical_protocol': MCPServiceConfig(
                name='vigia-medical-protocol-server',
                endpoint='http://vigia-medical-protocol-server:8080',
                service_type='custom',
                compliance_level='hipaa',
                timeout=30,
                rate_limit=30
            ),
            'medical_knowledge': MCPServiceConfig(
                name='vigia-medical-knowledge',
                endpoint='http://vigia-medical-knowledge:8080',
                service_type='custom',
                compliance_level='hipaa',
                timeout=30,
                rate_limit=20
            )
        }
        
        services.update(hub_services)
        services.update(medical_services)
        
        return services
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60)
        )
        await self._health_check_all_services()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def route_request(self, request: MCPRequest) -> MCPResponse:
        """
        Route MCP request to appropriate service
        """
        start_time = time.time()
        
        try:
            # Validate service exists
            if request.service not in self.services:
                return MCPResponse(
                    request_id=request.request_id,
                    service=request.service,
                    tool=request.tool,
                    status='error',
                    error=f"Service not found: {request.service}",
                    response_time=time.time() - start_time
                )
            
            service_config = self.services[request.service]
            
            # Check service health
            if not await self._is_service_healthy(request.service):
                return MCPResponse(
                    request_id=request.request_id,
                    service=request.service,
                    tool=request.tool,
                    status='error',
                    error=f"Service unhealthy: {request.service}",
                    response_time=time.time() - start_time
                )
            
            # Check rate limiting
            if not self._check_rate_limit(request.service):
                return MCPResponse(
                    request_id=request.request_id,
                    service=request.service,
                    tool=request.tool,
                    status='error',
                    error="Rate limit exceeded",
                    response_time=time.time() - start_time
                )
            
            # Add medical context
            enhanced_request = await self._enhance_medical_context(request)
            
            # Route based on service type
            if service_config.service_type == 'hub':
                response = await self._call_hub_service(enhanced_request, service_config)
            else:
                response = await self._call_medical_service(enhanced_request, service_config)
            
            # Add compliance validation
            response.compliance_validated = await self._validate_compliance(response, service_config)
            
            # Log for audit
            response.audit_logged = await self._log_audit(enhanced_request, response)
            
            response.response_time = time.time() - start_time
            return response
            
        except Exception as e:
            logger.error(f"Error routing MCP request: {e}")
            return MCPResponse(
                request_id=request.request_id,
                service=request.service,
                tool=request.tool,
                status='error',
                error=str(e),
                response_time=time.time() - start_time
            )
    
    async def _enhance_medical_context(self, request: MCPRequest) -> MCPRequest:
        """Add medical context to request"""
        medical_context = request.medical_context or {}
        
        # Add standard medical context
        medical_context.update({
            'compliance_level': 'hipaa',
            'phi_protection': True,
            'audit_required': True,
            'timestamp': request.timestamp.isoformat(),
            'vigia_version': '1.3.1'
        })
        
        # Add service-specific context
        service_config = self.services[request.service]
        medical_context['service_compliance'] = service_config.compliance_level
        
        request.medical_context = medical_context
        return request
    
    async def _call_hub_service(self, request: MCPRequest, config: MCPServiceConfig) -> MCPResponse:
        """Call Docker Hub MCP service"""
        try:
            # Prepare payload for hub service
            payload = {
                'tool': request.tool,
                'parameters': request.params,
                'context': request.medical_context
            }
            
            # Make HTTP request
            async with self.session.post(
                f"{config.endpoint}/tools/call",
                json=payload,
                timeout=config.timeout
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return MCPResponse(
                        request_id=request.request_id,
                        service=request.service,
                        tool=request.tool,
                        status='success',
                        data=data
                    )
                else:
                    error_text = await response.text()
                    return MCPResponse(
                        request_id=request.request_id,
                        service=request.service,
                        tool=request.tool,
                        status='error',
                        error=f"HTTP {response.status}: {error_text}"
                    )
                    
        except asyncio.TimeoutError:
            return MCPResponse(
                request_id=request.request_id,
                service=request.service,
                tool=request.tool,
                status='timeout',
                error="Service timeout"
            )
        except Exception as e:
            return MCPResponse(
                request_id=request.request_id,
                service=request.service,
                tool=request.tool,
                status='error',
                error=str(e)
            )
    
    async def _call_medical_service(self, request: MCPRequest, config: MCPServiceConfig) -> MCPResponse:
        """Call custom medical MCP service"""
        try:
            # Prepare payload for medical service
            payload = {
                'tool': request.tool,
                'parameters': request.params,
                'medical_context': request.medical_context,
                'compliance_check': True
            }
            
            # Make HTTP request
            async with self.session.post(
                f"{config.endpoint}/medical/call",
                json=payload,
                timeout=config.timeout
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return MCPResponse(
                        request_id=request.request_id,
                        service=request.service,
                        tool=request.tool,
                        status='success',
                        data=data
                    )
                else:
                    error_text = await response.text()
                    return MCPResponse(
                        request_id=request.request_id,
                        service=request.service,
                        tool=request.tool,
                        status='error',
                        error=f"HTTP {response.status}: {error_text}"
                    )
                    
        except asyncio.TimeoutError:
            return MCPResponse(
                request_id=request.request_id,
                service=request.service,
                tool=request.tool,
                status='timeout',
                error="Service timeout"
            )
        except Exception as e:
            return MCPResponse(
                request_id=request.request_id,
                service=request.service,
                tool=request.tool,
                status='error',
                error=str(e)
            )
    
    async def _health_check_all_services(self):
        """Health check all configured services"""
        for service_name in self.services:
            healthy = await self._is_service_healthy(service_name)
            self.service_health[service_name] = healthy
            logger.info(f"Service {service_name}: {'healthy' if healthy else 'unhealthy'}")
    
    async def _is_service_healthy(self, service_name: str) -> bool:
        """Check if service is healthy"""
        if service_name not in self.services:
            return False
            
        config = self.services[service_name]
        
        try:
            async with self.session.get(
                f"{config.endpoint}/health",
                timeout=5
            ) as response:
                return response.status == 200
        except:
            return False
    
    def _check_rate_limit(self, service_name: str) -> bool:
        """Check rate limit for service"""
        now = time.time()
        service_config = self.services[service_name]
        
        if service_name not in self.rate_limits:
            self.rate_limits[service_name] = []
        
        # Clean old entries (last minute)
        self.rate_limits[service_name] = [
            timestamp for timestamp in self.rate_limits[service_name]
            if now - timestamp < 60
        ]
        
        # Check if under limit
        if len(self.rate_limits[service_name]) < service_config.rate_limit:
            self.rate_limits[service_name].append(now)
            return True
        
        return False
    
    async def _validate_compliance(self, response: MCPResponse, config: MCPServiceConfig) -> bool:
        """Validate compliance requirements"""
        # For now, basic validation
        # In production, implement full compliance validation
        return response.status == 'success'
    
    async def _log_audit(self, request: MCPRequest, response: MCPResponse) -> bool:
        """Log request/response for audit"""
        try:
            audit_entry = {
                'timestamp': datetime.now().isoformat(),
                'request_id': request.request_id,
                'service': request.service,
                'tool': request.tool,
                'status': response.status,
                'response_time': response.response_time,
                'compliance_level': request.medical_context.get('compliance_level'),
                'phi_accessed': 'patient_id' in str(request.params)
            }
            
            # In production, send to audit service
            logger.info(f"Audit: {audit_entry}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log audit: {e}")
            return False


class MCPGateway:
    """
    Main MCP Gateway for Vigia
    Provides high-level interface for MCP operations
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.router = MCPRouter(config)
        
    async def __aenter__(self):
        await self.router.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.router.__aexit__(exc_type, exc_val, exc_tb)
    
    async def call_service(self, service: str, tool: str, params: Dict[str, Any], 
                          medical_context: Optional[Dict[str, Any]] = None) -> MCPResponse:
        """
        High-level service call interface
        """
        request = MCPRequest(
            service=service,
            tool=tool,
            params=params,
            medical_context=medical_context
        )
        
        return await self.router.route_request(request)
    
    async def github_operation(self, operation: str, **kwargs) -> MCPResponse:
        """GitHub-specific operations"""
        return await self.call_service('github', operation, kwargs)
    
    async def stripe_operation(self, operation: str, **kwargs) -> MCPResponse:
        """Stripe-specific operations"""
        return await self.call_service('stripe', operation, kwargs)
    
    async def redis_operation(self, operation: str, **kwargs) -> MCPResponse:
        """Redis-specific operations"""
        return await self.call_service('redis', operation, kwargs)
    
    async def slack_operation(self, operation: str, **kwargs) -> MCPResponse:
        """Slack-specific operations with Block Kit support"""
        return await self.call_service('slack', operation, kwargs)
    
    async def send_slack_block_kit(self, channel: str, blocks: List[Dict[str, Any]], 
                                  text: str = None, **kwargs) -> MCPResponse:
        """Send Block Kit message to Slack"""
        params = {
            'channel': channel,
            'blocks': blocks,
            **kwargs
        }
        if text:
            params['text'] = text
            
        return await self.slack_operation('chat_postMessage', **params)
    
    async def send_lpp_alert_slack(self, case_id: str, patient_code: str, lpp_grade: int,
                                  confidence: float, location: str, service: str, bed: str,
                                  channel: str = '#medical-alerts') -> MCPResponse:
        """Send LPP alert using Block Kit format"""
        blocks = BlockKitMedical.lpp_alert_blocks(
            case_id=case_id,
            patient_code=patient_code,
            lpp_grade=lpp_grade,
            confidence=confidence,
            location=location,
            service=service,
            bed=bed
        )
        
        return await self.send_slack_block_kit(
            channel=channel,
            blocks=blocks,
            text=f"LPP Grade {lpp_grade} Alert - Case {case_id}"
        )
    
    async def send_patient_history_slack(self, patient_data: Dict[str, Any],
                                        channel: str = '#medical-team') -> MCPResponse:
        """Send patient history using Block Kit format"""
        blocks = BlockKitMedical.patient_history_blocks(patient_data)
        
        return await self.send_slack_block_kit(
            channel=channel,
            blocks=blocks,
            text=f"Patient History - {patient_data.get('name', 'Unknown')[:3]}***"
        )
    
    async def handle_slack_interaction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Slack interactive components (buttons, modals, etc.)"""
        if payload.get('type') == 'block_actions':
            # Handle button clicks
            actions = payload.get('actions', [])
            if actions:
                action = actions[0]
                action_id = action.get('action_id')
                value = action.get('value')
                user_id = payload.get('user', {}).get('id')
                
                return BlockKitInteractions.handle_action(action_id, value, user_id)
                
        elif payload.get('type') == 'view_submission':
            # Handle modal submissions
            return BlockKitInteractions.handle_modal_submission(payload.get('view', {}))
        
        return {"response_type": "ephemeral", "text": "Acción no reconocida"}
    
    async def lpp_detection(self, image_path: str, patient_context: Dict[str, Any]) -> MCPResponse:
        """LPP detection via custom medical service"""
        return await self.call_service(
            'lpp_detection',
            'detect_pressure_injury',
            {'image_path': image_path},
            medical_context=patient_context
        )
    
    async def fhir_integration(self, operation: str, fhir_data: Dict[str, Any]) -> MCPResponse:
        """FHIR integration via custom medical service"""
        return await self.call_service(
            'fhir_gateway',
            operation,
            fhir_data
        )
    
    async def whatsapp_operation(self, operation: str, patient_context: Optional[Dict[str, Any]] = None, **kwargs) -> MCPResponse:
        """WhatsApp operations via Twilio integration"""
        medical_context = patient_context or {}
        medical_context.update({
            'platform': 'whatsapp',
            'phi_protection': True,
            'message_encryption': True
        })
        
        return await self.call_service(
            'twilio_whatsapp',
            operation,
            kwargs,
            medical_context=medical_context
        )
    
    async def whatsapp_direct_operation(self, operation: str, patient_context: Optional[Dict[str, Any]] = None, **kwargs) -> MCPResponse:
        """Direct WhatsApp Web operations"""
        medical_context = patient_context or {}
        medical_context.update({
            'platform': 'whatsapp_direct',
            'phi_protection': True,
            'local_processing': True,
            'audit_required': True
        })
        
        return await self.call_service(
            'whatsapp_direct',
            operation,
            kwargs,
            medical_context=medical_context
        )
    
    async def slack_operation(self, operation: str, medical_context: Optional[Dict[str, Any]] = None, **kwargs) -> MCPResponse:
        """Slack operations for medical team communication"""
        medical_context = medical_context or {}
        medical_context.update({
            'platform': 'slack',
            'team_communication': True,
            'phi_protection': True,
            'escalation_capable': True
        })
        
        return await self.call_service(
            'slack',
            operation,
            kwargs,
            medical_context=medical_context
        )
    
    async def send_medical_alert(self, alert_type: str, patient_id: str, severity: str, 
                                platform: str = 'slack', message: str = None) -> MCPResponse:
        """Send medical alerts via messaging platforms"""
        alert_data = {
            'alert_type': alert_type,
            'patient_id': patient_id,
            'severity': severity,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'requires_acknowledgment': severity in ['high', 'critical']
        }
        
        medical_context = {
            'alert_system': True,
            'phi_protection': True,
            'audit_required': True,
            'emergency_escalation': severity == 'critical'
        }
        
        if platform == 'slack':
            return await self.slack_operation('send_alert', medical_context, **alert_data)
        elif platform == 'whatsapp':
            return await self.whatsapp_operation('send_alert', medical_context, **alert_data)
        else:
            raise ValueError(f"Unsupported platform for medical alerts: {platform}")
    
    async def notify_lpp_detection(self, lpp_grade: int, confidence: float, patient_context: Dict[str, Any],
                                  image_path: str = None, platform: str = 'slack') -> MCPResponse:
        """Notify medical team of LPP detection"""
        # Determine severity based on LPP grade and confidence
        if lpp_grade >= 3 or (lpp_grade >= 2 and confidence > 0.9):
            severity = 'high'
        elif lpp_grade >= 2 or confidence > 0.8:
            severity = 'medium'
        else:
            severity = 'low'
        
        message = f"LPP Grade {lpp_grade} detected (conf: {confidence:.2f})"
        if patient_context.get('patient_id'):
            message += f" for patient {patient_context['patient_id']}"
        
        notification_data = {
            'lpp_grade': lpp_grade,
            'confidence': confidence,
            'severity': severity,
            'message': message,
            'image_path': image_path,
            'patient_context': patient_context,
            'requires_review': lpp_grade >= 2 or confidence < 0.7
        }
        
        return await self.send_medical_alert(
            'lpp_detection',
            patient_context.get('patient_id', 'unknown'),
            severity,
            platform,
            message
        )
    
    # === NEW MCP INTEGRATION METHODS ===
    
    async def supabase_operation(self, operation: str, medical_context: Optional[Dict[str, Any]] = None, **kwargs) -> MCPResponse:
        """Supabase database operations for medical data"""
        medical_context = medical_context or {}
        medical_context.update({
            'platform': 'supabase',
            'data_storage': True,
            'phi_protection': True,
            'backup_enabled': True
        })
        
        return await self.call_service(
            'supabase',
            operation,
            kwargs,
            medical_context=medical_context
        )
    
    async def postgres_operation(self, operation: str, medical_context: Optional[Dict[str, Any]] = None, **kwargs) -> MCPResponse:
        """PostgreSQL database operations"""
        medical_context = medical_context or {}
        medical_context.update({
            'platform': 'postgres',
            'database_type': 'primary',
            'transaction_support': True,
            'acid_compliance': True
        })
        
        return await self.call_service(
            'postgres',
            operation,
            kwargs,
            medical_context=medical_context
        )
    
    async def google_cloud_operation(self, operation: str, medical_context: Optional[Dict[str, Any]] = None, **kwargs) -> MCPResponse:
        """Google Cloud Platform operations (Vertex AI, Storage, BigQuery)"""
        medical_context = medical_context or {}
        medical_context.update({
            'platform': 'google_cloud',
            'ai_processing': True,
            'hipaa_compliance': True,
            'vertex_ai_enabled': True
        })
        
        return await self.call_service(
            'google_cloud',
            operation,
            kwargs,
            medical_context=medical_context
        )
    
    async def sendgrid_operation(self, operation: str, medical_context: Optional[Dict[str, Any]] = None, **kwargs) -> MCPResponse:
        """SendGrid email operations for medical notifications"""
        medical_context = medical_context or {}
        medical_context.update({
            'platform': 'sendgrid',
            'notification_type': 'email',
            'phi_protection': True,
            'delivery_tracking': True
        })
        
        return await self.call_service(
            'sendgrid',
            operation,
            kwargs,
            medical_context=medical_context
        )
    
    async def aws_operation(self, operation: str, medical_context: Optional[Dict[str, Any]] = None, **kwargs) -> MCPResponse:
        """AWS cloud services operations"""
        medical_context = medical_context or {}
        medical_context.update({
            'platform': 'aws',
            'cloud_infrastructure': True,
            'hipaa_eligible': True,
            'scalable': True
        })
        
        return await self.call_service(
            'aws',
            operation,
            kwargs,
            medical_context=medical_context
        )
    
    async def sentry_operation(self, operation: str, medical_context: Optional[Dict[str, Any]] = None, **kwargs) -> MCPResponse:
        """Sentry error tracking and monitoring"""
        medical_context = medical_context or {}
        medical_context.update({
            'platform': 'sentry',
            'monitoring_type': 'error_tracking',
            'performance_monitoring': True,
            'alert_system': True
        })
        
        return await self.call_service(
            'sentry',
            operation,
            kwargs,
            medical_context=medical_context
        )
    
    # === CUSTOM VIGIA MCP SERVICES ===
    
    async def fhir_operation(self, operation: str, medical_context: Optional[Dict[str, Any]] = None, **kwargs) -> MCPResponse:
        """FHIR operations for medical data interchange"""
        medical_context = medical_context or {}
        medical_context.update({
            'platform': 'vigia_fhir',
            'interoperability': True,
            'hl7_standard': True,
            'medical_data_exchange': True
        })
        
        return await self.call_service(
            'vigia_fhir',
            operation,
            kwargs,
            medical_context=medical_context
        )
    
    async def minsal_operation(self, operation: str, medical_context: Optional[Dict[str, Any]] = None, **kwargs) -> MCPResponse:
        """MINSAL Chilean healthcare compliance operations"""
        medical_context = medical_context or {}
        medical_context.update({
            'platform': 'vigia_minsal',
            'regulatory_compliance': True,
            'chile_specific': True,
            'mandatory_reporting': True
        })
        
        return await self.call_service(
            'vigia_minsal',
            operation,
            kwargs,
            medical_context=medical_context
        )
    
    async def redis_cache_operation(self, operation: str, medical_context: Optional[Dict[str, Any]] = None, **kwargs) -> MCPResponse:
        """Redis caching operations for medical data"""
        medical_context = medical_context or {}
        medical_context.update({
            'platform': 'vigia_redis',
            'cache_type': 'medical_data',
            'high_performance': True,
            'vector_search': True
        })
        
        return await self.call_service(
            'vigia_redis',
            operation,
            kwargs,
            medical_context=medical_context
        )
    
    async def medical_protocol_operation(self, operation: str, medical_context: Optional[Dict[str, Any]] = None, **kwargs) -> MCPResponse:
        """Medical protocol operations for clinical guidelines"""
        medical_context = medical_context or {}
        medical_context.update({
            'platform': 'vigia_medical_protocol',
            'clinical_guidelines': True,
            'evidence_based': True,
            'protocol_search': True
        })
        
        return await self.call_service(
            'vigia_medical_protocol',
            operation,
            kwargs,
            medical_context=medical_context
        )
    
    # === CONVENIENCE METHODS FOR COMPLEX WORKFLOWS ===
    
    async def send_email_alert(self, recipient: str, subject: str, message: str, severity: str = "medium", patient_context: Optional[Dict[str, Any]] = None) -> MCPResponse:
        """Send medical alert via email"""
        return await self.sendgrid_operation(
            'send_email',
            medical_context=patient_context,
            to=recipient,
            subject=f"[{severity.upper()}] {subject}",
            html_content=message,
            medical_alert=True
        )
    
    async def cache_patient_data(self, patient_id: str, patient_data: Dict[str, Any], ttl_hours: int = 24) -> MCPResponse:
        """Cache patient data in Redis"""
        return await self.redis_cache_operation(
            'cache_patient_data',
            medical_context={'patient_id': patient_id},
            patient_id=patient_id,
            patient_data=patient_data,
            ttl_hours=ttl_hours
        )
    
    async def search_medical_protocols(self, query: str, lpp_grade: Optional[int] = None) -> MCPResponse:
        """Search for medical protocols"""
        search_params = {'query': query}
        if lpp_grade:
            search_params['severity'] = f'grade_{lpp_grade}'
        
        return await self.medical_protocol_operation(
            'search_protocols',
            search_params
        )
    
    async def validate_minsal_compliance(self, lpp_data: Dict[str, Any], hospital_data: Dict[str, Any]) -> MCPResponse:
        """Validate MINSAL compliance for Chilean healthcare"""
        return await self.minsal_operation(
            'validate_minsal_compliance',
            medical_context={'country': 'chile'},
            lpp_data=lpp_data,
            hospital_data=hospital_data
        )
    
    async def create_fhir_patient(self, patient_data: Dict[str, Any]) -> MCPResponse:
        """Create FHIR Patient resource"""
        return await self.fhir_operation(
            'create_patient',
            medical_context={'resource_type': 'Patient'},
            patient_data=patient_data
        )
    
    async def log_medical_error(self, error_data: Dict[str, Any], severity: str = "error") -> MCPResponse:
        """Log medical system error to Sentry"""
        return await self.sentry_operation(
            'capture_exception',
            medical_context={'system': 'vigia_medical'},
            error_data=error_data,
            level=severity,
            tags={'medical_system': True}
        )
    
    async def get_service_status(self) -> Dict[str, Any]:
        """Get status of all MCP services"""
        await self.router._health_check_all_services()
        
        status = {
            'gateway_status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {}
        }
        
        for service_name, config in self.router.services.items():
            status['services'][service_name] = {
                'name': config.name,
                'type': config.service_type,
                'compliance': config.compliance_level,
                'healthy': self.router.service_health.get(service_name, False),
                'endpoint': config.endpoint
            }
        
        return status


# Factory function
def create_mcp_gateway(config: Dict[str, Any]) -> MCPGateway:
    """
    Factory function to create MCP gateway
    """
    return MCPGateway(config)


# Example usage
if __name__ == "__main__":
    async def main():
        config = {
            'medical_compliance': 'hipaa',
            'audit_enabled': True
        }
        
        async with create_mcp_gateway(config) as gateway:
            # Test service status
            status = await gateway.get_service_status()
            print(f"Gateway status: {status}")
            
            # Test GitHub operation
            github_response = await gateway.github_operation(
                'list_repositories',
                org='vigia-medical'
            )
            print(f"GitHub response: {github_response}")
            
            # Test LPP detection
            lpp_response = await gateway.lpp_detection(
                '/path/to/medical/image.jpg',
                {'patient_id': 'PAT123', 'compliance_level': 'hipaa'}
            )
            print(f"LPP detection response: {lpp_response}")
    
    asyncio.run(main())