#!/usr/bin/env python3
"""
Vigia Medical MCP Servers
Custom MCP servers for medical-specific functionality
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from abc import ABC, abstractmethod
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
import uvicorn

from ..utils.logger import get_logger
from ..utils.encryption import encrypt_phi, decrypt_phi
from ..systems.medical_decision_engine import MedicalDecisionEngine
from ..systems.clinical_processing import ClinicalProcessor
from ..cv_pipeline.detector import LPPDetector
from ..integrations.his_fhir_gateway import HISFHIRGateway

logger = get_logger(__name__)


class MCPMedicalRequest(BaseModel):
    """Medical MCP request format"""
    tool: str = Field(..., description="Tool/operation name")
    parameters: Dict[str, Any] = Field(..., description="Tool parameters")
    medical_context: Dict[str, Any] = Field(..., description="Medical context")
    compliance_check: bool = Field(True, description="Require compliance validation")
    patient_id: Optional[str] = Field(None, description="Patient identifier")
    request_id: str = Field(default_factory=lambda: f"med_{int(time.time() * 1000)}")


class MCPMedicalResponse(BaseModel):
    """Medical MCP response format"""
    request_id: str
    tool: str
    status: str  # 'success', 'error', 'compliance_failure'
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    medical_metadata: Dict[str, Any] = Field(default_factory=dict)
    compliance_validated: bool = False
    evidence_level: Optional[str] = None
    audit_trail: Dict[str, Any] = Field(default_factory=dict)


class VigiaMLPServer(ABC):
    """
    Base class for Vigia Medical MCP servers
    Provides common medical functionality and compliance
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.compliance_level = config.get('compliance_level', 'hipaa')
        self.phi_protection = config.get('phi_protection', True)
        self.audit_enabled = config.get('audit_enabled', True)
        self.medical_engine = MedicalDecisionEngine()
        
        # FastAPI app
        self.app = FastAPI(
            title=f"Vigia {self.__class__.__name__}",
            description=f"Medical MCP server for {self.__class__.__name__}",
            version="1.0.0"
        )
        
        self._setup_routes()
        logger.info(f"{self.__class__.__name__} initialized")
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "service": self.__class__.__name__,
                "timestamp": datetime.now().isoformat(),
                "compliance_level": self.compliance_level
            }
        
        @self.app.get("/tools")
        async def list_tools():
            """List available tools"""
            return {
                "tools": self.get_available_tools(),
                "service": self.__class__.__name__,
                "compliance_level": self.compliance_level
            }
        
        @self.app.post("/medical/call", response_model=MCPMedicalResponse)
        async def call_tool(request: MCPMedicalRequest):
            """Main tool call endpoint"""
            return await self.handle_tool_call(request)
    
    @abstractmethod
    def get_available_tools(self) -> List[str]:
        """Get list of available tools"""
        pass
    
    @abstractmethod
    async def execute_tool(self, tool: str, params: Dict[str, Any], 
                          medical_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute specific tool"""
        pass
    
    async def handle_tool_call(self, request: MCPMedicalRequest) -> MCPMedicalResponse:
        """
        Handle medical tool call with compliance validation
        """
        start_time = time.time()
        
        try:
            # Validate compliance requirements
            if request.compliance_check:
                compliance_result = await self._validate_compliance(request)
                if not compliance_result['valid']:
                    return MCPMedicalResponse(
                        request_id=request.request_id,
                        tool=request.tool,
                        status='compliance_failure',
                        error=compliance_result['error'],
                        compliance_validated=False
                    )
            
            # Validate tool exists
            if request.tool not in self.get_available_tools():
                return MCPMedicalResponse(
                    request_id=request.request_id,
                    tool=request.tool,
                    status='error',
                    error=f"Tool not found: {request.tool}"
                )
            
            # Execute tool
            result = await self.execute_tool(
                request.tool,
                request.parameters,
                request.medical_context
            )
            
            # Create response
            response = MCPMedicalResponse(
                request_id=request.request_id,
                tool=request.tool,
                status='success',
                data=result,
                compliance_validated=True,
                medical_metadata={
                    'service': self.__class__.__name__,
                    'compliance_level': self.compliance_level,
                    'processing_time': time.time() - start_time,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            # Add evidence level if available
            if 'evidence_level' in result:
                response.evidence_level = result['evidence_level']
            
            # Log audit trail
            if self.audit_enabled:
                response.audit_trail = await self._create_audit_trail(request, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in tool call: {e}")
            return MCPMedicalResponse(
                request_id=request.request_id,
                tool=request.tool,
                status='error',
                error=str(e),
                medical_metadata={
                    'service': self.__class__.__name__,
                    'error_type': type(e).__name__,
                    'timestamp': datetime.now().isoformat()
                }
            )
    
    async def _validate_compliance(self, request: MCPMedicalRequest) -> Dict[str, Any]:
        """Validate medical compliance requirements"""
        try:
            # Check PHI protection
            if self.phi_protection and request.patient_id:
                if not self._is_phi_protected(request.parameters):
                    return {
                        'valid': False,
                        'error': 'PHI protection required but not implemented'
                    }
            
            # Check medical context
            if 'compliance_level' not in request.medical_context:
                return {
                    'valid': False,
                    'error': 'Medical compliance level not specified'
                }
            
            # Check audit requirements
            if self.audit_enabled and not request.medical_context.get('audit_required', True):
                return {
                    'valid': False,
                    'error': 'Audit trail required for medical operations'
                }
            
            return {'valid': True}
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Compliance validation error: {e}'
            }
    
    def _is_phi_protected(self, params: Dict[str, Any]) -> bool:
        """Check if PHI data is properly protected"""
        # Basic check - in production implement full PHI validation
        phi_fields = ['patient_name', 'ssn', 'phone', 'email', 'address']
        for field in phi_fields:
            if field in params and not isinstance(params[field], str):
                return False
        return True
    
    async def _create_audit_trail(self, request: MCPMedicalRequest, 
                                response: MCPMedicalResponse) -> Dict[str, Any]:
        """Create audit trail for medical operation"""
        return {
            'request_timestamp': datetime.now().isoformat(),
            'tool_executed': request.tool,
            'compliance_level': self.compliance_level,
            'patient_id_hashed': self._hash_patient_id(request.patient_id) if request.patient_id else None,
            'phi_accessed': bool(request.patient_id),
            'status': response.status,
            'evidence_level': response.evidence_level,
            'service': self.__class__.__name__
        }
    
    def _hash_patient_id(self, patient_id: str) -> str:
        """Hash patient ID for audit (maintaining privacy)"""
        import hashlib
        return hashlib.sha256(patient_id.encode()).hexdigest()[:16]
    
    def run(self, host: str = "0.0.0.0", port: int = 8080):
        """Run the MCP server"""
        uvicorn.run(self.app, host=host, port=port)


class LPPDetectionServer(VigiaMLPServer):
    """
    MCP server for LPP (pressure injury) detection
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.detector = LPPDetector(config.get('detector_config', {}))
        self.clinical_processor = ClinicalProcessor()
        
    def get_available_tools(self) -> List[str]:
        return [
            "detect_pressure_injury",
            "grade_lpp_severity",
            "generate_medical_report",
            "trigger_clinical_alert",
            "assess_healing_progress",
            "recommend_treatment"
        ]
    
    async def execute_tool(self, tool: str, params: Dict[str, Any], 
                          medical_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LPP detection tools"""
        
        if tool == "detect_pressure_injury":
            return await self._detect_pressure_injury(params, medical_context)
        
        elif tool == "grade_lpp_severity":
            return await self._grade_lpp_severity(params, medical_context)
        
        elif tool == "generate_medical_report":
            return await self._generate_medical_report(params, medical_context)
        
        elif tool == "trigger_clinical_alert":
            return await self._trigger_clinical_alert(params, medical_context)
        
        elif tool == "assess_healing_progress":
            return await self._assess_healing_progress(params, medical_context)
        
        elif tool == "recommend_treatment":
            return await self._recommend_treatment(params, medical_context)
        
        else:
            raise ValueError(f"Unknown tool: {tool}")
    
    async def _detect_pressure_injury(self, params: Dict[str, Any], 
                                    medical_context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect pressure injuries in medical image"""
        image_path = params.get('image_path')
        if not image_path or not Path(image_path).exists():
            raise ValueError("Valid image path required")
        
        # Run detection
        detection_result = await self.detector.detect_async(image_path)
        
        # Generate medical decision
        if detection_result['lpp_detected']:
            decision = self.medical_engine.make_clinical_decision(
                lpp_grade=detection_result['lpp_grade'],
                confidence=detection_result['confidence'],
                anatomical_location=detection_result.get('location', 'unknown')
            )
            detection_result.update(decision)
        
        return {
            'detection_result': detection_result,
            'medical_context': medical_context,
            'evidence_level': detection_result.get('evidence_level', 'B'),
            'timestamp': datetime.now().isoformat()
        }
    
    async def _grade_lpp_severity(self, params: Dict[str, Any], 
                                medical_context: Dict[str, Any]) -> Dict[str, Any]:
        """Grade LPP severity based on clinical findings"""
        findings = params.get('clinical_findings', {})
        
        # Use medical engine for grading
        grade_result = self.medical_engine.grade_lpp_severity(findings)
        
        return {
            'lpp_grade': grade_result['grade'],
            'severity': grade_result['severity'],
            'clinical_rationale': grade_result['rationale'],
            'evidence_level': grade_result['evidence_level'],
            'guidelines_reference': grade_result['guidelines_reference']
        }
    
    async def _generate_medical_report(self, params: Dict[str, Any], 
                                     medical_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive medical report"""
        patient_id = medical_context.get('patient_id')
        findings = params.get('findings', [])
        
        report = await self.clinical_processor.generate_comprehensive_report(
            patient_id=patient_id,
            findings=findings,
            medical_context=medical_context
        )
        
        return {
            'report': report,
            'report_type': 'lpp_assessment',
            'compliance_validated': True,
            'evidence_level': 'A'
        }
    
    async def _trigger_clinical_alert(self, params: Dict[str, Any], 
                                    medical_context: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger clinical alert for severe findings"""
        severity = params.get('severity', 'low')
        lpp_grade = params.get('lpp_grade', 1)
        
        if lpp_grade >= 3 or severity == 'critical':
            alert = await self.clinical_processor.trigger_alert(
                alert_type='critical_lpp',
                patient_id=medical_context.get('patient_id'),
                findings=params
            )
            
            return {
                'alert_triggered': True,
                'alert_id': alert['alert_id'],
                'urgency': 'immediate',
                'escalation_required': True
            }
        
        return {
            'alert_triggered': False,
            'reason': 'Severity below alert threshold'
        }
    
    async def _assess_healing_progress(self, params: Dict[str, Any], 
                                     medical_context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess healing progress over time"""
        current_findings = params.get('current_findings', {})
        previous_findings = params.get('previous_findings', {})
        
        progress = await self.clinical_processor.assess_healing_progress(
            current_findings, previous_findings
        )
        
        return {
            'healing_assessment': progress,
            'trend': progress['trend'],
            'recommendations': progress['recommendations'],
            'evidence_level': 'B'
        }
    
    async def _recommend_treatment(self, params: Dict[str, Any], 
                                 medical_context: Dict[str, Any]) -> Dict[str, Any]:
        """Recommend evidence-based treatment"""
        lpp_grade = params.get('lpp_grade', 1)
        location = params.get('anatomical_location', 'unknown')
        patient_factors = params.get('patient_factors', {})
        
        recommendations = self.medical_engine.get_treatment_recommendations(
            lpp_grade=lpp_grade,
            location=location,
            patient_factors=patient_factors
        )
        
        return {
            'treatment_recommendations': recommendations,
            'evidence_level': recommendations['evidence_level'],
            'guidelines_reference': recommendations['guidelines_reference'],
            'urgency': recommendations['urgency']
        }


class FHIRIntegrationServer(VigiaMLPServer):
    """
    MCP server for FHIR/HL7 healthcare integration
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.fhir_gateway = HISFHIRGateway(config.get('fhir_config', {}))
        
    def get_available_tools(self) -> List[str]:
        return [
            "create_fhir_observation",
            "send_hl7_message",
            "query_patient_data",
            "sync_with_his",
            "create_diagnostic_report",
            "update_care_plan"
        ]
    
    async def execute_tool(self, tool: str, params: Dict[str, Any], 
                          medical_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute FHIR integration tools"""
        
        if tool == "create_fhir_observation":
            return await self._create_fhir_observation(params, medical_context)
        
        elif tool == "send_hl7_message":
            return await self._send_hl7_message(params, medical_context)
        
        elif tool == "query_patient_data":
            return await self._query_patient_data(params, medical_context)
        
        elif tool == "sync_with_his":
            return await self._sync_with_his(params, medical_context)
        
        elif tool == "create_diagnostic_report":
            return await self._create_diagnostic_report(params, medical_context)
        
        elif tool == "update_care_plan":
            return await self._update_care_plan(params, medical_context)
        
        else:
            raise ValueError(f"Unknown tool: {tool}")
    
    async def _create_fhir_observation(self, params: Dict[str, Any], 
                                     medical_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create FHIR observation for LPP finding"""
        lpp_data = params.get('lpp_observation', {})
        
        observation = await self.fhir_gateway.create_lpp_observation(lpp_data)
        
        return {
            'fhir_observation': observation,
            'resource_type': 'Observation',
            'status': 'final',
            'compliance_validated': True
        }
    
    async def _send_hl7_message(self, params: Dict[str, Any], 
                              medical_context: Dict[str, Any]) -> Dict[str, Any]:
        """Send HL7 v2.5 message"""
        message_type = params.get('message_type', 'ORU^R01')
        message_data = params.get('message_data', {})
        
        result = await self.fhir_gateway.send_hl7_message(message_type, message_data)
        
        return {
            'hl7_result': result,
            'message_type': message_type,
            'status': result.get('status', 'sent')
        }
    
    async def _query_patient_data(self, params: Dict[str, Any], 
                                medical_context: Dict[str, Any]) -> Dict[str, Any]:
        """Query patient data from HIS"""
        patient_id = params.get('patient_id')
        query_type = params.get('query_type', 'demographics')
        
        data = await self.fhir_gateway.query_patient_data(patient_id, query_type)
        
        return {
            'patient_data': data,
            'query_type': query_type,
            'data_source': 'his_fhir'
        }
    
    async def _sync_with_his(self, params: Dict[str, Any], 
                           medical_context: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronize data with Hospital Information System"""
        sync_type = params.get('sync_type', 'observations')
        data = params.get('data', {})
        
        result = await self.fhir_gateway.sync_data(sync_type, data)
        
        return {
            'sync_result': result,
            'sync_type': sync_type,
            'records_synced': result.get('count', 0)
        }
    
    async def _create_diagnostic_report(self, params: Dict[str, Any], 
                                      medical_context: Dict[str, Any]) -> Dict[str, Any]:
        """Create FHIR diagnostic report"""
        report_data = params.get('report_data', {})
        
        diagnostic_report = await self.fhir_gateway.create_diagnostic_report(report_data)
        
        return {
            'diagnostic_report': diagnostic_report,
            'resource_type': 'DiagnosticReport',
            'status': 'final'
        }
    
    async def _update_care_plan(self, params: Dict[str, Any], 
                              medical_context: Dict[str, Any]) -> Dict[str, Any]:
        """Update patient care plan"""
        care_plan_id = params.get('care_plan_id')
        updates = params.get('updates', {})
        
        updated_plan = await self.fhir_gateway.update_care_plan(care_plan_id, updates)
        
        return {
            'care_plan': updated_plan,
            'resource_type': 'CarePlan',
            'status': 'active'
        }


# Factory functions
def create_lpp_detection_server(config: Dict[str, Any]) -> LPPDetectionServer:
    """Create LPP detection MCP server"""
    return LPPDetectionServer(config)


def create_fhir_integration_server(config: Dict[str, Any]) -> FHIRIntegrationServer:
    """Create FHIR integration MCP server"""
    return FHIRIntegrationServer(config)


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Vigia Medical MCP Server")
    parser.add_argument("--server", choices=["lpp", "fhir"], required=True,
                       help="Server type to run")
    parser.add_argument("--port", type=int, default=8080, help="Port to run on")
    parser.add_argument("--config", help="Config file path")
    
    args = parser.parse_args()
    
    # Load config
    config = {
        'compliance_level': 'hipaa',
        'phi_protection': True,
        'audit_enabled': True
    }
    
    if args.config:
        with open(args.config) as f:
            config.update(json.load(f))
    
    # Create and run server
    if args.server == "lpp":
        server = create_lpp_detection_server(config)
    elif args.server == "fhir":
        server = create_fhir_integration_server(config)
    
    logger.info(f"Starting {server.__class__.__name__} on port {args.port}")
    server.run(port=args.port)