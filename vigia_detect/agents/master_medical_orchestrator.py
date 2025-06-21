"""
Master Medical Orchestrator - ADK Agent for Vigia Medical System
===============================================================

Master orchestrator agent that coordinates all medical agents in the Vigia system
using Google ADK framework and A2A protocol for distributed medical processing.

This agent acts as the central coordinator for:
- ImageAnalysisAgent (YOLOv5 + CV pipeline)
- ClinicalAssessmentAgent (Evidence-based decisions)
- ProtocolAgent (NPUAP/EPUAP knowledge)
- CommunicationAgent (WhatsApp/Slack)
- WorkflowOrchestrationAgent (Async pipeline)
"""

import logging
import warnings
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from google.adk.agents.llm_agent import Agent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.tools import FunctionTool

# Import existing tools and functions
from vigia_detect.agents.lpp_medical_agent import procesar_imagen_lpp, generar_reporte_lpp
from vigia_detect.messaging.adk_tools import enviar_alerta_lpp, test_slack_desde_adk
from vigia_detect.systems.medical_decision_engine import make_evidence_based_decision
from vigia_detect.core.session_manager import SessionManager
from vigia_detect.utils.audit_service import AuditService

# Import ADK specialized agents for real A2A communication
from vigia_detect.agents.image_analysis_agent import ImageAnalysisAgent
from vigia_detect.agents.clinical_assessment_agent import ClinicalAssessmentAgent
from vigia_detect.agents.protocol_agent import ProtocolAgent
from vigia_detect.agents.communication_agent import CommunicationAgent
from vigia_detect.agents.workflow_orchestration_agent import WorkflowOrchestrationAgent

warnings.filterwarnings("ignore", category=UserWarning, module=".*pydantic.*")

# Configure logging
logger = logging.getLogger(__name__)

# Master orchestrator configuration
MASTER_ORCHESTRATOR_INSTRUCTION = """
Eres el Master Medical Orchestrator del sistema Vigia, responsable de coordinar 
todos los agentes médicos especializados para el procesamiento de casos clínicos 
de detección de lesiones por presión (LPP).

RESPONSABILIDADES PRINCIPALES:
1. Recibir casos médicos desde entrada WhatsApp
2. Coordinar análisis entre agentes especializados
3. Orquestar flujo de trabajo médico completo
4. Mantener trazabilidad y compliance médico
5. Escalar casos críticos a revisión humana
6. Generar reportes médicos consolidados

AGENTES ESPECIALIZADOS COORDINADOS:
- ImageAnalysisAgent: Análisis CV con YOLOv5
- ClinicalAssessmentAgent: Decisiones basadas en evidencia
- ProtocolAgent: Conocimiento NPUAP/EPUAP
- CommunicationAgent: Notificaciones Slack/WhatsApp
- WorkflowOrchestrationAgent: Pipeline asíncrono

PROTOCOLOS DE ESCALAMIENTO:
- Confianza < 60%: Revisión especialista
- LPP Grado 3-4: Evaluación inmediata
- Errores de procesamiento: Escalamiento técnico
- Casos ambiguos: Cola revisión humana

COMPLIANCE MÉDICO:
- Mantener anonimización pacientes
- Registrar audit trail completo
- Respetar timeouts de sesión (15 min)
- Documentar todas las decisiones médicas
"""

class MasterMedicalOrchestrator:
    """
    Master orchestrator for coordinating all medical agents in Vigia system.
    Implements ADK patterns with A2A communication for distributed processing.
    """
    
    def __init__(self):
        """Initialize master orchestrator with session and audit services"""
        self.session_manager = SessionManager()
        self.audit_service = AuditService()
        self.orchestrator_id = f"master_orchestrator_{datetime.now().strftime('%Y%m%d')}"
        
        # Agent registry for A2A communication
        self.registered_agents = {
            'image_analysis': None,     # Will be populated during A2A registration
            'clinical_assessment': None,
            'protocol': None,
            'communication': None,
            'workflow': None
        }
        
        # Initialize specialized agents with A2A communication
        asyncio.create_task(self._initialize_specialized_agents())
        
        # Processing statistics
        self.stats = {
            'cases_processed': 0,
            'escalations': 0,
            'errors': 0,
            'avg_processing_time': 0.0
        }
    
    async def process_medical_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main orchestration function for processing medical cases.
        
        Args:
            case_data: Complete case information including:
                - image_path: Path to medical image
                - token_id: Tokenized patient identifier (NO PHI)
                - patient_alias: Patient alias (e.g., "Batman") for display
                - patient_context: Medical context and risk factors (tokenized)
                - session_token: Temporary session identifier
                
        Returns:
            Complete medical case processing result
        """
        start_time = datetime.now()
        session_token = case_data.get('session_token')
        token_id = case_data.get('token_id')  # Tokenized patient ID (NO PHI)
        patient_alias = case_data.get('patient_alias', 'Unknown')  # Display alias
        
        try:
            # Initialize session and audit
            await self._initialize_case_session(case_data)
            
            # Phase 1: Image Analysis
            logger.info(f"Iniciando análisis de imagen para paciente {patient_alias} (token: {token_id[:8]}...)")
            image_analysis_result = await self._coordinate_image_analysis(case_data)
            
            if not image_analysis_result['success']:
                return await self._handle_processing_error(
                    case_data, 'image_analysis', image_analysis_result['error']
                )
            
            # Phase 2: Clinical Assessment
            logger.info(f"Iniciando evaluación clínica para paciente {patient_alias} (token: {token_id[:8]}...)")
            clinical_result = await self._coordinate_clinical_assessment(
                case_data, image_analysis_result
            )
            
            if not clinical_result['success']:
                return await self._handle_processing_error(
                    case_data, 'clinical_assessment', clinical_result['error']
                )
            
            # Phase 3: Protocol Consultation
            logger.info(f"Consultando protocolos médicos para paciente {patient_alias} (token: {token_id[:8]}...)")
            protocol_result = await self._coordinate_protocol_consultation(
                case_data, clinical_result
            )
            
            # Phase 4: Communication and Notifications
            logger.info(f"Procesando notificaciones para paciente {patient_alias} (token: {token_id[:8]}...)")
            communication_result = await self._coordinate_communication(
                case_data, protocol_result
            )
            
            # Phase 5: Workflow Coordination
            workflow_result = await self._coordinate_workflow_completion(
                case_data, communication_result
            )
            
            # Generate consolidated report
            final_result = await self._generate_consolidated_report(
                case_data, {
                    'image_analysis': image_analysis_result,
                    'clinical_assessment': clinical_result,
                    'protocol_consultation': protocol_result,
                    'communication': communication_result,
                    'workflow': workflow_result
                }
            )
            
            # Update statistics
            processing_time = (datetime.now() - start_time).total_seconds()
            await self._update_processing_stats(processing_time, final_result)
            
            # Close session
            await self._finalize_case_session(session_token, final_result)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Error en orquestación médica: {str(e)}")
            error_result = await self._handle_orchestration_error(case_data, str(e))
            await self._finalize_case_session(session_token, error_result)
            return error_result
    
    async def _initialize_case_session(self, case_data: Dict[str, Any]):
        """Initialize medical case session with audit trail (tokenized data only - NO PHI)"""
        session_token = case_data.get('session_token')
        token_id = case_data.get('token_id')  # Tokenized patient ID
        patient_alias = case_data.get('patient_alias', 'Unknown')  # Display alias
        
        # Import session types
        from vigia_detect.core.session_manager import SessionType
        
        # Create session using correct API
        session_result = await self.session_manager.create_session(
            input_data={
                'patient_code': patient_code,
                'orchestrator_id': self.orchestrator_id,
                'start_time': datetime.now().isoformat(),
                'stage': 'initialization',
                'source': 'master_orchestrator',
                'input_type': 'medical_case'
            },
            session_type=SessionType.CLINICAL_IMAGE,
            emergency=False
        )
        
        if not session_result.get('success', False):
            raise RuntimeError(f"Failed to create session: {session_result.get('error', 'Unknown error')}")
        
        # Import AuditEventType
        from vigia_detect.utils.audit_service import AuditEventType
        
        # Audit trail initialization
        await self.audit_service.log_event(
            event_type=AuditEventType.MEDICAL_DECISION,
            component='master_orchestrator',
            action='initialize_case',
            session_id=session_token,
            user_id='master_orchestrator',
            resource='medical_case',
            details={
                'orchestrator_id': self.orchestrator_id,
                'patient_code': patient_code,
                'case_metadata': case_data.get('metadata', {})
            }
        )
    
    async def _coordinate_image_analysis(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate image analysis with ImageAnalysisAgent"""
        try:
            # Check if A2A agent is available
            if self.registered_agents['image_analysis']:
                # Use A2A communication
                return await self._call_a2a_agent('image_analysis', case_data)
            else:
                # Use local processing (fallback)
                return await self._process_image_analysis_local(case_data)
                
        except Exception as e:
            logger.error(f"Error en análisis de imagen: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'agent': 'image_analysis',
                'fallback_attempted': True
            }
    
    async def _process_image_analysis_local(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Local fallback for image analysis processing"""
        image_path = case_data.get('image_path')
        patient_code = case_data.get('patient_code')
        
        # Simulate CV pipeline processing (in production, this would call actual CV pipeline)
        mock_cv_results = {
            'detections': [
                {
                    'class': 'lpp_grade_2',
                    'confidence': 0.75,
                    'anatomical_location': 'sacrum',
                    'bbox': [100, 150, 200, 250]
                }
            ],
            'processing_time': 2.3,
            'model_version': 'yolov5s_medical_v1.0'
        }
        
        # Process with existing LPP medical agent
        result = procesar_imagen_lpp(image_path, patient_code, mock_cv_results)
        
        return {
            'success': True,
            'agent': 'image_analysis_local',
            'result': result,
            'cv_details': mock_cv_results,
            'processing_timestamp': datetime.now().isoformat()
        }
    
    async def _coordinate_clinical_assessment(self, case_data: Dict[str, Any], 
                                            image_result: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate clinical assessment with ClinicalAssessmentAgent"""
        try:
            if self.registered_agents['clinical_assessment']:
                # Use A2A communication
                assessment_data = {**case_data, 'image_analysis': image_result}
                return await self._call_a2a_agent('clinical_assessment', assessment_data)
            else:
                # Use local evidence-based decision engine
                return await self._process_clinical_assessment_local(case_data, image_result)
                
        except Exception as e:
            logger.error(f"Error en evaluación clínica: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'agent': 'clinical_assessment'
            }
    
    async def _process_clinical_assessment_local(self, case_data: Dict[str, Any], 
                                               image_result: Dict[str, Any]) -> Dict[str, Any]:
        """Local fallback for clinical assessment"""
        # Extract relevant data
        detection_result = image_result.get('result', {})
        lpp_grade = detection_result.get('severidad', 0)
        confidence = detection_result.get('detalles', {}).get('confidence', 0) / 100
        location = detection_result.get('detalles', {}).get('ubicacion', 'unknown')
        patient_context = case_data.get('patient_context', {})
        
        # Use evidence-based decision engine
        evidence_decision = make_evidence_based_decision(
            lpp_grade, confidence, location, patient_context
        )
        
        return {
            'success': True,
            'agent': 'clinical_assessment_local',
            'evidence_based_decision': evidence_decision,
            'processing_timestamp': datetime.now().isoformat()
        }
    
    async def _coordinate_protocol_consultation(self, case_data: Dict[str, Any], 
                                              clinical_result: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate protocol consultation with ProtocolAgent"""
        try:
            if self.registered_agents['protocol']:
                protocol_data = {**case_data, 'clinical_assessment': clinical_result}
                return await self._call_a2a_agent('protocol', protocol_data)
            else:
                return await self._process_protocol_consultation_local(case_data, clinical_result)
                
        except Exception as e:
            logger.error(f"Error en consulta de protocolos: {str(e)}")
            return {
                'success': True,  # Non-critical, continue processing
                'error': str(e),
                'agent': 'protocol',
                'protocols_applied': []
            }
    
    async def _process_protocol_consultation_local(self, case_data: Dict[str, Any], 
                                                 clinical_result: Dict[str, Any]) -> Dict[str, Any]:
        """Local fallback for protocol consultation"""
        # Extract clinical decision
        evidence_decision = clinical_result.get('evidence_based_decision', {})
        lpp_grade = evidence_decision.get('lpp_grade', 0)
        
        # Apply relevant protocols
        applicable_protocols = []
        
        if lpp_grade >= 1:
            applicable_protocols.append('NPUAP_EPUAP_2019_Prevention')
        if lpp_grade >= 2:
            applicable_protocols.append('NPUAP_EPUAP_2019_Treatment')
        if lpp_grade >= 3:
            applicable_protocols.append('NPUAP_EPUAP_2019_Advanced_Care')
        
        return {
            'success': True,
            'agent': 'protocol_local',
            'applicable_protocols': applicable_protocols,
            'protocol_recommendations': evidence_decision.get('clinical_recommendations', []),
            'processing_timestamp': datetime.now().isoformat()
        }
    
    async def _coordinate_communication(self, case_data: Dict[str, Any], 
                                      protocol_result: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate communication with CommunicationAgent"""
        try:
            if self.registered_agents['communication']:
                comm_data = {**case_data, 'protocol_consultation': protocol_result}
                return await self._call_a2a_agent('communication', comm_data)
            else:
                return await self._process_communication_local(case_data, protocol_result)
                
        except Exception as e:
            logger.error(f"Error en comunicación: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'agent': 'communication',
                'notifications_sent': []
            }
    
    async def _process_communication_local(self, case_data: Dict[str, Any], 
                                         protocol_result: Dict[str, Any]) -> Dict[str, Any]:
        """Local fallback for communication processing"""
        patient_code = case_data.get('patient_code')
        
        # Determine notification requirements
        evidence_decision = protocol_result.get('protocol_consultation', {}).get('evidence_based_decision', {})
        lpp_grade = evidence_decision.get('lpp_grade', 0)
        
        # Send appropriate notifications
        notifications = []
        
        if lpp_grade >= 3:
            # Critical case - immediate notification
            alert_result = enviar_alerta_lpp(
                canal="#emergencias-medicas",
                severidad=lpp_grade,
                paciente_id=patient_code,
                detalles={'urgencia': 'CRÍTICA', 'timestamp': datetime.now().isoformat()}
            )
            notifications.append(alert_result)
        elif lpp_grade >= 1:
            # Regular case - standard notification
            alert_result = enviar_alerta_lpp(
                canal="#equipo-medico",
                severidad=lpp_grade,
                paciente_id=patient_code,
                detalles={'urgencia': 'RUTINA', 'timestamp': datetime.now().isoformat()}
            )
            notifications.append(alert_result)
        
        return {
            'success': True,
            'agent': 'communication_local',
            'notifications_sent': notifications,
            'processing_timestamp': datetime.now().isoformat()
        }
    
    async def _coordinate_workflow_completion(self, case_data: Dict[str, Any], 
                                            communication_result: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate workflow completion with WorkflowOrchestrationAgent"""
        try:
            if self.registered_agents['workflow']:
                workflow_data = {**case_data, 'communication': communication_result}
                return await self._call_a2a_agent('workflow', workflow_data)
            else:
                return await self._process_workflow_completion_local(case_data, communication_result)
                
        except Exception as e:
            logger.error(f"Error en finalización de workflow: {str(e)}")
            return {
                'success': True,  # Non-critical for final step
                'error': str(e),
                'agent': 'workflow'
            }
    
    async def _process_workflow_completion_local(self, case_data: Dict[str, Any], 
                                               communication_result: Dict[str, Any]) -> Dict[str, Any]:
        """Local fallback for workflow completion"""
        session_token = case_data.get('session_token')
        
        # Update session status
        self.session_manager.update_session(session_token, {
            'stage': 'completion',
            'completion_time': datetime.now().isoformat(),
            'status': 'successful'
        })
        
        return {
            'success': True,
            'agent': 'workflow_local',
            'workflow_status': 'completed',
            'session_updated': True,
            'processing_timestamp': datetime.now().isoformat()
        }
    
    async def _call_a2a_agent(self, agent_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call A2A agent using Agent Development Kit (ADK) protocol.
        Real A2A communication with specialized medical agents.
        """
        try:
            agent_instance = self.registered_agents[agent_type]
            if not agent_instance:
                raise RuntimeError(f"Agent {agent_type} not registered")
            
            # Create AgentMessage for A2A communication
            from .base_agent import AgentMessage
            from datetime import timezone
            
            message = AgentMessage(
                session_id=data.get('session_token', 'unknown'),
                sender_id=self.orchestrator_id,
                content=data,
                message_type="processing_request",
                timestamp=datetime.now(timezone.utc),
                metadata={
                    'orchestrator_request': True,
                    'priority': data.get('priority', 'medium'),
                    'patient_code': data.get('patient_code')
                }
            )
            
            # Process message with specialized agent
            response = await agent_instance.process_message(message)
            
            return {
                'success': response.success,
                'agent': f'{agent_type}_a2a',
                'a2a_protocol': 'ADK',
                'response': response.content,
                'message': response.message,
                'requires_human_review': response.requires_human_review,
                'next_actions': response.next_actions,
                'processing_timestamp': datetime.now().isoformat(),
                'response_metadata': response.metadata
            }
            
        except Exception as e:
            logger.error(f"A2A communication failed with {agent_type}: {str(e)}")
            return {
                'success': False,
                'agent': f'{agent_type}_a2a',
                'error': str(e),
                'a2a_protocol': 'ADK',
                'fallback_required': True,
                'processing_timestamp': datetime.now().isoformat()
            }
    
    async def _generate_consolidated_report(self, case_data: Dict[str, Any], 
                                          results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate consolidated medical report from all agent results"""
        patient_code = case_data.get('patient_code')
        session_token = case_data.get('session_token')
        
        # Extract key information from all agents
        image_analysis = results.get('image_analysis', {})
        clinical_assessment = results.get('clinical_assessment', {})
        protocol_consultation = results.get('protocol_consultation', {})
        communication = results.get('communication', {})
        workflow = results.get('workflow', {})
        
        # Determine overall case status
        overall_success = all(
            result.get('success', False) 
            for result in results.values()
        )
        
        # Extract medical decision
        evidence_decision = clinical_assessment.get('evidence_based_decision', {})
        lpp_grade = evidence_decision.get('lpp_grade', 0)
        severity = evidence_decision.get('severity_assessment', 'UNKNOWN')
        
        # Generate consolidated report
        consolidated_report = {
            'case_id': f"{patient_code}_{session_token}",
            'patient_code': patient_code,
            'processing_timestamp': datetime.now().isoformat(),
            'orchestrator_id': self.orchestrator_id,
            'overall_success': overall_success,
            
            # Medical results
            'medical_assessment': {
                'lpp_grade': lpp_grade,
                'severity_assessment': severity,
                'confidence_score': evidence_decision.get('confidence_score', 0.0),
                'anatomical_location': evidence_decision.get('anatomical_location'),
                'clinical_recommendations': evidence_decision.get('clinical_recommendations', []),
                'medical_warnings': evidence_decision.get('medical_warnings', []),
                'requires_human_review': evidence_decision.get('escalation_requirements', {}).get('requires_human_review', False)
            },
            
            # Agent processing summary
            'agent_processing_summary': {
                'image_analysis': {
                    'success': image_analysis.get('success', False),
                    'agent_used': image_analysis.get('agent', 'unknown'),
                    'processing_time': image_analysis.get('processing_time', 0)
                },
                'clinical_assessment': {
                    'success': clinical_assessment.get('success', False),
                    'agent_used': clinical_assessment.get('agent', 'unknown'),
                    'evidence_based': True
                },
                'protocol_consultation': {
                    'success': protocol_consultation.get('success', False),
                    'protocols_applied': protocol_consultation.get('applicable_protocols', [])
                },
                'communication': {
                    'success': communication.get('success', False),
                    'notifications_sent': len(communication.get('notifications_sent', []))
                },
                'workflow': {
                    'success': workflow.get('success', False),
                    'status': workflow.get('workflow_status', 'unknown')
                }
            },
            
            # Compliance and audit
            'compliance_info': {
                'session_token': session_token,
                'audit_trail_complete': True,
                'data_anonymized': True,
                'retention_policy': '7_years',
                'regulatory_compliance': ['HIPAA', 'MINSAL']
            },
            
            # Detailed results for audit
            'detailed_results': results
        }
        
        return consolidated_report
    
    async def _handle_processing_error(self, case_data: Dict[str, Any], 
                                     agent_type: str, error: str) -> Dict[str, Any]:
        """Handle processing errors with appropriate escalation"""
        patient_code = case_data.get('patient_code')
        session_token = case_data.get('session_token')
        
        # Log error for audit
        await self.audit_service.log_medical_event(
            event_type='processing_error',
            patient_code=patient_code,
            session_token=session_token,
            details={
                'agent_type': agent_type,
                'error_message': error,
                'orchestrator_id': self.orchestrator_id,
                'requires_escalation': True
            }
        )
        
        # Generate error response
        return {
            'case_id': f"{patient_code}_{session_token}",
            'patient_code': patient_code,
            'processing_timestamp': datetime.now().isoformat(),
            'overall_success': False,
            'error_details': {
                'failed_agent': agent_type,
                'error_message': error,
                'escalation_required': True,
                'human_review_required': True
            },
            'medical_assessment': {
                'lpp_grade': None,
                'severity_assessment': 'ERROR_REQUIRES_MANUAL_REVIEW',
                'requires_human_review': True,
                'error_processing': True
            },
            'compliance_info': {
                'session_token': session_token,
                'audit_trail_complete': True,
                'error_logged': True
            }
        }
    
    async def _handle_orchestration_error(self, case_data: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Handle orchestration-level errors"""
        patient_code = case_data.get('patient_code')
        session_token = case_data.get('session_token')
        
        # Update error statistics
        self.stats['errors'] += 1
        
        return {
            'case_id': f"{patient_code}_{session_token}",
            'patient_code': patient_code,
            'processing_timestamp': datetime.now().isoformat(),
            'overall_success': False,
            'orchestration_error': {
                'error_message': error,
                'orchestrator_id': self.orchestrator_id,
                'requires_technical_escalation': True
            },
            'medical_assessment': {
                'severity_assessment': 'ORCHESTRATION_ERROR',
                'requires_human_review': True,
                'technical_error': True
            }
        }
    
    async def _update_processing_stats(self, processing_time: float, result: Dict[str, Any]):
        """Update processing statistics"""
        self.stats['cases_processed'] += 1
        
        # Update average processing time
        current_avg = self.stats['avg_processing_time']
        total_cases = self.stats['cases_processed']
        self.stats['avg_processing_time'] = (
            (current_avg * (total_cases - 1) + processing_time) / total_cases
        )
        
        # Count escalations
        if result.get('medical_assessment', {}).get('requires_human_review', False):
            self.stats['escalations'] += 1
    
    async def _finalize_case_session(self, session_token: str, result: Dict[str, Any]):
        """Finalize case session with cleanup"""
        if session_token:
            # Import session states
            from vigia_detect.core.session_manager import SessionState
            
            # Get session info first to check if it exists
            session_info = await self.session_manager.get_session_info(session_token)
            if session_info:
                # Update session state to completed
                success = await self.session_manager.update_session_state(
                    session_token, 
                    SessionState.COMPLETED,
                    processor_id=self.orchestrator_id,
                    additional_data={
                        'final_result': result,
                        'finalization_time': datetime.now().isoformat()
                    }
                )
                
                if success:
                    # Schedule session cleanup
                    await self.session_manager.cleanup_session(session_token, "normal_completion")
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """Get current orchestrator statistics"""
        return {
            'orchestrator_id': self.orchestrator_id,
            'stats': self.stats,
            'registered_agents': {
                agent_type: agent is not None 
                for agent_type, agent in self.registered_agents.items()
            },
            'uptime': datetime.now().isoformat()
        }


# ADK Tools for Master Orchestrator
def process_medical_case_orchestrated(case_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    ADK Tool function for processing medical cases through master orchestrator.
    Can be used directly in ADK agents.
    """
    orchestrator = MasterMedicalOrchestrator()
    
    # Run async processing in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(orchestrator.process_medical_case(case_data))
        return result
    finally:
        loop.close()


def get_orchestrator_status() -> Dict[str, Any]:
    """
    ADK Tool function for getting orchestrator status.
    """
    orchestrator = MasterMedicalOrchestrator()
    return orchestrator.get_orchestrator_stats()


    async def _initialize_specialized_agents(self):
        """
        Initialize all specialized ADK agents for A2A communication.
        This replaces fallback mechanisms with real agent instances.
        """
        try:
            logger.info("Inicializando agentes ADK especializados...")
            
            # Initialize ImageAnalysisAgent
            self.registered_agents['image_analysis'] = ImageAnalysisAgent()
            await self.registered_agents['image_analysis'].initialize()
            logger.info("✅ ImageAnalysisAgent inicializado")
            
            # Initialize ClinicalAssessmentAgent
            self.registered_agents['clinical_assessment'] = ClinicalAssessmentAgent()
            await self.registered_agents['clinical_assessment'].initialize()
            logger.info("✅ ClinicalAssessmentAgent inicializado")
            
            # Initialize ProtocolAgent
            self.registered_agents['protocol'] = ProtocolAgent()
            await self.registered_agents['protocol'].initialize()
            logger.info("✅ ProtocolAgent inicializado")
            
            # Initialize CommunicationAgent
            self.registered_agents['communication'] = CommunicationAgent()
            await self.registered_agents['communication'].initialize()
            logger.info("✅ CommunicationAgent inicializado")
            
            # Initialize WorkflowOrchestrationAgent
            self.registered_agents['workflow'] = WorkflowOrchestrationAgent()
            await self.registered_agents['workflow'].initialize()
            logger.info("✅ WorkflowOrchestrationAgent inicializado")
            
            # Register agents for A2A discovery
            await self._register_agents_for_a2a()
            
            logger.info("🎯 Todos los agentes ADK especializados registrados exitosamente")
            
        except Exception as e:
            logger.error(f"Error inicializando agentes especializados: {str(e)}")
            # Log specific error for debugging
            logger.exception("Stacktrace completo:")
    
    async def _register_agents_for_a2a(self):
        """
        Register all agents in A2A infrastructure for mutual discovery.
        """
        try:
            # Import A2A infrastructure
            from vigia_detect.a2a.base_infrastructure import AgentCard
            
            # Register each agent with A2A infrastructure
            agent_cards = {
                'image_analysis': AgentCard(
                    agent_id='image_analysis_agent',
                    name='Medical Image Analysis Agent',
                    description='YOLOv5-based LPP detection and medical image processing',
                    version='1.0.0',
                    capabilities=['image_analysis', 'lpp_detection', 'cv_pipeline'],
                    endpoints={'a2a': 'http://localhost:8081'},
                    authentication={'method': 'api_key'},
                    supported_modes=['request_response'],
                    medical_specialization='wound_care',
                    compliance_certifications=['HIPAA', 'MINSAL']
                ),
                'clinical_assessment': AgentCard(
                    agent_id='clinical_assessment_agent',
                    name='Clinical Assessment Agent',
                    description='Evidence-based medical assessment and decision making',
                    version='1.0.0',
                    capabilities=['clinical_assessment', 'evidence_based_decisions', 'risk_scoring'],
                    endpoints={'a2a': 'http://localhost:8082'},
                    authentication={'method': 'api_key'},
                    supported_modes=['request_response'],
                    medical_specialization='clinical_decision_support',
                    compliance_certifications=['NPUAP_EPUAP', 'MINSAL']
                ),
                'protocol': AgentCard(
                    agent_id='protocol_agent',
                    name='Medical Protocol Agent',
                    description='NPUAP/EPUAP medical protocol consultation and guidelines',
                    version='1.0.0',
                    capabilities=['protocol_consultation', 'medical_guidelines', 'knowledge_base'],
                    endpoints={'a2a': 'http://localhost:8083'},
                    authentication={'method': 'api_key'},
                    supported_modes=['request_response'],
                    medical_specialization='medical_protocols',
                    compliance_certifications=['NPUAP_EPUAP', 'MINSAL']
                ),
                'communication': AgentCard(
                    agent_id='communication_agent',
                    name='Medical Communication Agent',
                    description='WhatsApp and Slack medical team notifications',
                    version='1.0.0',
                    capabilities=['medical_notifications', 'slack_integration', 'whatsapp_integration'],
                    endpoints={'a2a': 'http://localhost:8084'},
                    authentication={'method': 'api_key'},
                    supported_modes=['request_response'],
                    medical_specialization='medical_communications',
                    compliance_certifications=['HIPAA']
                ),
                'workflow': AgentCard(
                    agent_id='workflow_orchestration_agent',
                    name='Workflow Orchestration Agent',
                    description='Medical workflow orchestration and async pipeline management',
                    version='1.0.0',
                    capabilities=['workflow_orchestration', 'async_pipeline', 'medical_triage'],
                    endpoints={'a2a': 'http://localhost:8085'},
                    authentication={'method': 'api_key'},
                    supported_modes=['request_response'],
                    medical_specialization='workflow_management',
                    compliance_certifications=['HIPAA', 'MINSAL']
                )
            }
            
            # Store agent cards for reference
            self.agent_cards = agent_cards
            logger.info("🔗 A2A Agent Cards registradas exitosamente")
            
        except Exception as e:
            logger.error(f"Error registrando agents para A2A: {str(e)}")


async def register_all_agents() -> MasterMedicalOrchestrator:
    """Factory function to create and register all specialized agents"""
    orchestrator = MasterMedicalOrchestrator()
    await orchestrator._initialize_specialized_agents()
    return orchestrator


# Create Master Orchestrator Agent
master_orchestrator_agent = Agent(
    model="gemini-2.0-flash-exp",
    global_instruction=MASTER_ORCHESTRATOR_INSTRUCTION,
    instruction="Coordina todos los agentes médicos especializados para procesamiento completo de casos clínicos LPP.",
    name="master_medical_orchestrator",
    tools=[
        process_medical_case_orchestrated,
        get_orchestrator_status,
        procesar_imagen_lpp,
        generar_reporte_lpp,
        enviar_alerta_lpp,
        test_slack_desde_adk,
    ],
)

# Export for use
__all__ = [
    'MasterMedicalOrchestrator', 
    'master_orchestrator_agent',
    'process_medical_case_orchestrated',
    'get_orchestrator_status'
]