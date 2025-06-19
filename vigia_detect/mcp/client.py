#!/usr/bin/env python3
"""
Vigia MCP Client
High-level client for interacting with MCP services
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import aiohttp

from .gateway import MCPGateway, MCPRequest, MCPResponse, create_mcp_gateway
from ..utils.shared_utilities import VigiaLogger

logger = VigiaLogger.get_logger(__name__)


class MCPClient:
    """
    High-level client for MCP operations
    Provides simplified interface for common MCP tasks
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.gateway_config = config.get('gateway', {})
        self.gateway = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.gateway = create_mcp_gateway(self.gateway_config)
        await self.gateway.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.gateway:
            await self.gateway.__aexit__(exc_type, exc_val, exc_tb)
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        if not self.gateway:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        return await self.gateway.get_service_status()
    
    # GitHub Operations
    async def github_list_repos(self, org: str) -> Dict[str, Any]:
        """List GitHub repositories"""
        response = await self.gateway.github_operation('list_repositories', org=org)
        return self._extract_response_data(response)
    
    async def github_create_issue(self, repo: str, title: str, body: str, 
                                 labels: List[str] = None) -> Dict[str, Any]:
        """Create GitHub issue"""
        response = await self.gateway.github_operation(
            'create_issue',
            repo=repo,
            title=title,
            body=body,
            labels=labels or []
        )
        return self._extract_response_data(response)
    
    async def github_update_pr_status(self, repo: str, pr_number: int, 
                                    status: str) -> Dict[str, Any]:
        """Update pull request status"""
        response = await self.gateway.github_operation(
            'update_pr_status',
            repo=repo,
            pr_number=pr_number,
            status=status
        )
        return self._extract_response_data(response)
    
    # Stripe Operations
    async def stripe_create_charge(self, amount: int, currency: str, 
                                  customer_id: str, description: str) -> Dict[str, Any]:
        """Create Stripe charge"""
        response = await self.gateway.stripe_operation(
            'create_charge',
            amount=amount,
            currency=currency,
            customer=customer_id,
            description=description
        )
        return self._extract_response_data(response)
    
    async def stripe_create_subscription(self, customer_id: str, 
                                       price_id: str) -> Dict[str, Any]:
        """Create Stripe subscription"""
        response = await self.gateway.stripe_operation(
            'create_subscription',
            customer=customer_id,
            price=price_id
        )
        return self._extract_response_data(response)
    
    async def stripe_get_payment_methods(self, customer_id: str) -> Dict[str, Any]:
        """Get customer payment methods"""
        response = await self.gateway.stripe_operation(
            'list_payment_methods',
            customer=customer_id
        )
        return self._extract_response_data(response)
    
    # Redis Operations
    async def redis_set(self, key: str, value: Any, ttl: Optional[int] = None) -> Dict[str, Any]:
        """Set Redis key-value"""
        response = await self.gateway.redis_operation(
            'set',
            key=key,
            value=json.dumps(value) if not isinstance(value, str) else value,
            ttl=ttl
        )
        return self._extract_response_data(response)
    
    async def redis_get(self, key: str) -> Dict[str, Any]:
        """Get Redis value"""
        response = await self.gateway.redis_operation('get', key=key)
        data = self._extract_response_data(response)
        
        # Try to parse JSON
        if 'value' in data and data['value']:
            try:
                data['value'] = json.loads(data['value'])
            except (json.JSONDecodeError, TypeError):
                pass  # Keep as string
        
        return data
    
    async def redis_delete(self, key: str) -> Dict[str, Any]:
        """Delete Redis key"""
        response = await self.gateway.redis_operation('delete', key=key)
        return self._extract_response_data(response)
    
    async def redis_search(self, pattern: str) -> Dict[str, Any]:
        """Search Redis keys by pattern"""
        response = await self.gateway.redis_operation('search', pattern=pattern)
        return self._extract_response_data(response)
    
    # MongoDB Operations  
    async def mongodb_insert(self, collection: str, document: Dict[str, Any]) -> Dict[str, Any]:
        """Insert document into MongoDB"""
        response = await self.gateway.call_service(
            'mongodb',
            'insert_document',
            {'collection': collection, 'document': document}
        )
        return self._extract_response_data(response)
    
    async def mongodb_find(self, collection: str, query: Dict[str, Any] = None) -> Dict[str, Any]:
        """Find documents in MongoDB"""
        response = await self.gateway.call_service(
            'mongodb',
            'find_documents',
            {'collection': collection, 'query': query or {}}
        )
        return self._extract_response_data(response)
    
    async def mongodb_update(self, collection: str, query: Dict[str, Any], 
                           update: Dict[str, Any]) -> Dict[str, Any]:
        """Update documents in MongoDB"""
        response = await self.gateway.call_service(
            'mongodb',
            'update_documents',
            {'collection': collection, 'query': query, 'update': update}
        )
        return self._extract_response_data(response)
    
    def _extract_response_data(self, response: MCPResponse) -> Dict[str, Any]:
        """Extract data from MCP response"""
        if response.status == 'success':
            return response.data or {}
        else:
            raise Exception(f"MCP operation failed: {response.error}")


class MCPMedicalClient:
    """
    Medical-specific MCP client
    Provides high-level interface for medical operations
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.gateway_config = config.get('gateway', {})
        self.gateway = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.gateway = create_mcp_gateway(self.gateway_config)
        await self.gateway.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.gateway:
            await self.gateway.__aexit__(exc_type, exc_val, exc_tb)
    
    # LPP Detection Operations
    async def detect_pressure_injury(self, image_path: str, patient_id: str, 
                                   additional_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Detect pressure injuries in medical image"""
        medical_context = {
            'patient_id': patient_id,
            'compliance_level': 'hipaa',
            'audit_required': True,
            'operation_type': 'lpp_detection'
        }
        
        if additional_context:
            medical_context.update(additional_context)
        
        response = await self.gateway.lpp_detection(image_path, medical_context)
        return self._extract_medical_response(response)
    
    async def grade_lpp_severity(self, clinical_findings: Dict[str, Any], 
                               patient_id: str) -> Dict[str, Any]:
        """Grade LPP severity based on clinical findings"""
        response = await self.gateway.call_service(
            'lpp_detection',
            'grade_lpp_severity',
            {'clinical_findings': clinical_findings},
            medical_context={'patient_id': patient_id, 'compliance_level': 'hipaa'}
        )
        return self._extract_medical_response(response)
    
    async def generate_medical_report(self, findings: List[Dict[str, Any]], 
                                    patient_id: str) -> Dict[str, Any]:
        """Generate comprehensive medical report"""
        response = await self.gateway.call_service(
            'lpp_detection',
            'generate_medical_report',
            {'findings': findings},
            medical_context={'patient_id': patient_id, 'compliance_level': 'hipaa'}
        )
        return self._extract_medical_response(response)
    
    async def trigger_clinical_alert(self, severity: str, lpp_grade: int, 
                                   patient_id: str, additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Trigger clinical alert for severe findings"""
        params = {
            'severity': severity,
            'lpp_grade': lpp_grade
        }
        if additional_data:
            params.update(additional_data)
        
        response = await self.gateway.call_service(
            'lpp_detection',
            'trigger_clinical_alert',
            params,
            medical_context={'patient_id': patient_id, 'compliance_level': 'hipaa'}
        )
        return self._extract_medical_response(response)
    
    async def assess_healing_progress(self, current_findings: Dict[str, Any], 
                                    previous_findings: Dict[str, Any], 
                                    patient_id: str) -> Dict[str, Any]:
        """Assess healing progress over time"""
        response = await self.gateway.call_service(
            'lpp_detection',
            'assess_healing_progress',
            {
                'current_findings': current_findings,
                'previous_findings': previous_findings
            },
            medical_context={'patient_id': patient_id, 'compliance_level': 'hipaa'}
        )
        return self._extract_medical_response(response)
    
    async def recommend_treatment(self, lpp_grade: int, anatomical_location: str, 
                                patient_factors: Dict[str, Any], patient_id: str) -> Dict[str, Any]:
        """Get evidence-based treatment recommendations"""
        response = await self.gateway.call_service(
            'lpp_detection',
            'recommend_treatment',
            {
                'lpp_grade': lpp_grade,
                'anatomical_location': anatomical_location,
                'patient_factors': patient_factors
            },
            medical_context={'patient_id': patient_id, 'compliance_level': 'hipaa'}
        )
        return self._extract_medical_response(response)
    
    # FHIR Integration Operations
    async def create_fhir_observation(self, lpp_observation: Dict[str, Any], 
                                    patient_id: str) -> Dict[str, Any]:
        """Create FHIR observation for LPP finding"""
        response = await self.gateway.fhir_integration(
            'create_fhir_observation',
            {'lpp_observation': lpp_observation}
        )
        return self._extract_medical_response(response)
    
    async def send_hl7_message(self, message_type: str, message_data: Dict[str, Any], 
                             patient_id: str) -> Dict[str, Any]:
        """Send HL7 v2.5 message"""
        response = await self.gateway.fhir_integration(
            'send_hl7_message',
            {'message_type': message_type, 'message_data': message_data}
        )
        return self._extract_medical_response(response)
    
    async def query_patient_data(self, patient_id: str, query_type: str = 'demographics') -> Dict[str, Any]:
        """Query patient data from HIS"""
        response = await self.gateway.fhir_integration(
            'query_patient_data',
            {'patient_id': patient_id, 'query_type': query_type}
        )
        return self._extract_medical_response(response)
    
    async def sync_with_his(self, sync_type: str, data: Dict[str, Any], 
                          patient_id: str) -> Dict[str, Any]:
        """Synchronize data with Hospital Information System"""
        response = await self.gateway.fhir_integration(
            'sync_with_his',
            {'sync_type': sync_type, 'data': data}
        )
        return self._extract_medical_response(response)
    
    async def create_diagnostic_report(self, report_data: Dict[str, Any], 
                                     patient_id: str) -> Dict[str, Any]:
        """Create FHIR diagnostic report"""
        response = await self.gateway.fhir_integration(
            'create_diagnostic_report',
            {'report_data': report_data}
        )
        return self._extract_medical_response(response)
    
    async def update_care_plan(self, care_plan_id: str, updates: Dict[str, Any], 
                             patient_id: str) -> Dict[str, Any]:
        """Update patient care plan"""
        response = await self.gateway.fhir_integration(
            'update_care_plan',
            {'care_plan_id': care_plan_id, 'updates': updates}
        )
        return self._extract_medical_response(response)
    
    def _extract_medical_response(self, response: MCPResponse) -> Dict[str, Any]:
        """Extract data from medical MCP response"""
        if response.status == 'success':
            result = response.data or {}
            
            # Add medical metadata
            result['_medical_metadata'] = {
                'compliance_validated': response.compliance_validated,
                'evidence_level': getattr(response, 'evidence_level', None),
                'audit_logged': response.audit_logged,
                'response_time': response.response_time
            }
            
            return result
        else:
            raise Exception(f"Medical MCP operation failed: {response.error}")


# Factory functions
def create_mcp_client(config: Dict[str, Any]) -> MCPClient:
    """Create standard MCP client"""
    return MCPClient(config)


def create_medical_client(config: Dict[str, Any]) -> MCPMedicalClient:
    """Create medical MCP client"""
    return MCPMedicalClient(config)


# Example usage
if __name__ == "__main__":
    async def main():
        # Standard MCP client example
        config = {
            'gateway': {
                'medical_compliance': 'hipaa',
                'audit_enabled': True
            }
        }
        
        async with create_mcp_client(config) as client:
            # GitHub operations
            status = await client.get_system_status()
            print(f"System status: {status}")
            
            # Redis operations
            await client.redis_set('test_key', {'data': 'test_value'}, ttl=300)
            result = await client.redis_get('test_key')
            print(f"Redis result: {result}")
        
        # Medical MCP client example
        async with create_medical_client(config) as medical_client:
            # LPP detection
            try:
                detection_result = await medical_client.detect_pressure_injury(
                    '/path/to/medical/image.jpg',
                    'PAT123',
                    {'department': 'ICU', 'attending_physician': 'Dr. Smith'}
                )
                print(f"LPP detection: {detection_result}")
                
                # Treatment recommendations
                treatment = await medical_client.recommend_treatment(
                    lpp_grade=3,
                    anatomical_location='sacrum',
                    patient_factors={'age': 75, 'diabetes': True},
                    patient_id='PAT123'
                )
                print(f"Treatment recommendations: {treatment}")
                
            except Exception as e:
                print(f"Medical operation failed: {e}")
    
    asyncio.run(main())