"""
WhatsApp Patient Communication Agent
===================================

ADK Agent for secure, template-based patient communication via WhatsApp.
Implements strict guardrails to prevent medical advice and ensure HIPAA compliance.

CRITICAL SAFETY RULES:
- NO medical advice or interpretation
- NO patient conversation memory
- NO dynamic text generation
- ONLY pre-approved templates
- ONLY system-validated data
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

from google.adk.agents import BaseAgent
from google.adk.tools import ToolContext

from .base import VigiaBaseAgent
from ...mcp.gateway import create_mcp_gateway
from ...monitoring.phi_tokenizer import PHITokenizer
from ...utils.audit_logger import AuditLogger

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Allowed message types - strictly controlled"""
    ACKNOWLEDGMENT = "acknowledgment"
    PROCESSING_STATUS = "processing_status" 
    SYSTEM_APPROVED_RESULTS = "system_approved_results"
    ERROR_NOTIFICATION = "error_notification"


class UnauthorizedMedicalDataError(Exception):
    """Raised when agent receives non-validated medical data"""
    pass


class WhatsAppPatientAgent(VigiaBaseAgent):
    """
    WhatsApp Patient Communication Agent
    
    SCOPE: ONLY translate system-approved outputs to natural language
    RESTRICTIONS: NO medical advice, NO patient memory, NO dynamic responses
    """
    
    def __init__(self, agent_id: str = "whatsapp_patient_agent"):
        super().__init__(
            agent_id=agent_id,
            agent_name="WhatsAppPatientAgent",
            capabilities=[
                "patient_communication",
                "whatsapp_messaging", 
                "medical_result_translation",
                "phi_compliant_messaging"
            ],
            medical_specialties=["patient_communication"]
        )
        
        # Initialize components (private to avoid pydantic conflicts)
        self._phi_tokenizer = PHITokenizer()
        self._audit_logger = AuditLogger("whatsapp_patient_agent")
        
        # Safety configuration (private to avoid pydantic conflicts)
        self._ALLOWED_MESSAGE_TYPES = [mt.value for mt in MessageType]
        self._MAX_MESSAGES_PER_PATIENT_PER_DAY = 10
        self._message_count_cache = {}  # Simple rate limiting
        
        # Pre-approved message templates - NO dynamic generation (private)
        self._APPROVED_TEMPLATES = {
            MessageType.ACKNOWLEDGMENT.value: {
                "es": "🏥 Vigia Medical\n\nHemos recibido tu imagen médica.\n\n📸 Estado: Procesada\n⏱️ Ref: {ref_number}\n\nTe notificaremos los resultados pronto.",
                "en": "🏥 Vigia Medical\n\nWe have received your medical image.\n\n📸 Status: Processed\n⏱️ Ref: {ref_number}\n\nWe will notify you of results soon."
            },
            MessageType.PROCESSING_STATUS.value: {
                "es": "🔍 Analizando imagen médica...\n\n⏱️ Tiempo estimado: 2-5 minutos\n📋 Ref: {ref_number}\n\nPor favor espera.",
                "en": "🔍 Analyzing medical image...\n\n⏱️ Estimated time: 2-5 minutes\n📋 Ref: {ref_number}\n\nPlease wait."
            },
            MessageType.SYSTEM_APPROVED_RESULTS.value: {
                "es": "📊 Análisis completado\n\n{approved_result}\n\n📋 Ref: {ref_number}\n\n⚠️ Consulta con tu médico para interpretación.",
                "en": "📊 Analysis completed\n\n{approved_result}\n\n📋 Ref: {ref_number}\n\n⚠️ Consult your physician for interpretation."
            },
            MessageType.ERROR_NOTIFICATION.value: {
                "es": "⚠️ Error procesando imagen\n\n📋 Ref: {ref_number}\n\nPor favor contacta soporte médico.",
                "en": "⚠️ Error processing image\n\n📋 Ref: {ref_number}\n\nPlease contact medical support."
            }
        }
        
        logger.info(f"WhatsApp Patient Agent initialized with strict guardrails")
    
    def validate_input_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate that input data is system-approved and safe to send.
        
        CRITICAL: Only accept pre-validated medical data from system.
        """
        required_fields = [
            "approved_by_system",
            "medical_validation_passed", 
            "phi_tokenized",
            "patient_phone_token"
        ]
        
        # Check all required fields present
        if not all(field in data for field in required_fields):
            logger.error(f"Missing required validation fields: {required_fields}")
            return False
        
        # Verify system approval
        if not data.get("approved_by_system", False):
            logger.error("Data not approved by medical system")
            return False
        
        # Verify medical validation
        if not data.get("medical_validation_passed", False):
            logger.error("Data failed medical validation")
            return False
        
        # Verify PHI protection
        if not data.get("phi_tokenized", False):
            logger.error("Data not PHI tokenized")
            return False
        
        return True
    
    def check_rate_limit(self, patient_token: str) -> bool:
        """Check if patient has exceeded daily message limit"""
        today = datetime.now().date().isoformat()
        key = f"{patient_token}_{today}"
        
        current_count = self._message_count_cache.get(key, 0)
        if current_count >= self._MAX_MESSAGES_PER_PATIENT_PER_DAY:
            logger.warning(f"Rate limit exceeded for patient {patient_token}")
            return False
        
        return True
    
    def increment_message_count(self, patient_token: str):
        """Increment message count for rate limiting"""
        today = datetime.now().date().isoformat()
        key = f"{patient_token}_{today}"
        self._message_count_cache[key] = self._message_count_cache.get(key, 0) + 1
    
    async def send_acknowledgment(self, 
                                 patient_phone_token: str,
                                 ref_number: str,
                                 language: str = "es") -> Dict[str, Any]:
        """
        Send immediate acknowledgment that image was received.
        
        Args:
            patient_phone_token: Tokenized patient phone number
            ref_number: System-generated reference number
            language: Response language (es/en)
        """
        try:
            # Rate limiting check
            if not self.check_rate_limit(patient_phone_token):
                return {"success": False, "error": "rate_limit_exceeded"}
            
            # Get template
            template = self._APPROVED_TEMPLATES[MessageType.ACKNOWLEDGMENT.value].get(
                language, self._APPROVED_TEMPLATES[MessageType.ACKNOWLEDGMENT.value]["es"]
            )
            
            # Format message (ONLY with safe parameters)
            message = template.format(ref_number=ref_number)
            
            # Send via MCP WhatsApp
            result = await self._send_whatsapp_message(
                patient_phone_token, 
                message,
                MessageType.ACKNOWLEDGMENT.value
            )
            
            # Audit log
            self._audit_logger.log_patient_message(
                patient_token=patient_phone_token,
                message_type=MessageType.ACKNOWLEDGMENT.value,
                ref_number=ref_number,
                success=result.get("success", False)
            )
            
            # Increment counter
            if result.get("success"):
                self.increment_message_count(patient_phone_token)
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending acknowledgment: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_processing_status(self,
                                   patient_phone_token: str,
                                   ref_number: str,
                                   language: str = "es") -> Dict[str, Any]:
        """
        Send processing status update to patient.
        """
        try:
            # Rate limiting check
            if not self.check_rate_limit(patient_phone_token):
                return {"success": False, "error": "rate_limit_exceeded"}
            
            # Get template
            template = self._APPROVED_TEMPLATES[MessageType.PROCESSING_STATUS.value].get(
                language, self._APPROVED_TEMPLATES[MessageType.PROCESSING_STATUS.value]["es"]
            )
            
            # Format message
            message = template.format(ref_number=ref_number)
            
            # Send via MCP WhatsApp
            result = await self._send_whatsapp_message(
                patient_phone_token,
                message, 
                MessageType.PROCESSING_STATUS.value
            )
            
            # Audit log
            self._audit_logger.log_patient_message(
                patient_token=patient_phone_token,
                message_type=MessageType.PROCESSING_STATUS.value,
                ref_number=ref_number,
                success=result.get("success", False)
            )
            
            # Increment counter
            if result.get("success"):
                self.increment_message_count(patient_phone_token)
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending processing status: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_approved_results(self,
                                  validated_data: Dict[str, Any],
                                  language: str = "es") -> Dict[str, Any]:
        """
        Send system-approved medical results to patient.
        
        CRITICAL: Only accepts pre-validated, system-approved data.
        """
        try:
            # STRICT input validation
            if not self.validate_input_data(validated_data):
                raise UnauthorizedMedicalDataError("Input data failed validation")
            
            patient_phone_token = validated_data["patient_phone_token"]
            ref_number = validated_data.get("ref_number", "UNKNOWN")
            
            # Rate limiting check
            if not self.check_rate_limit(patient_phone_token):
                return {"success": False, "error": "rate_limit_exceeded"}
            
            # Get approved result text (already validated by medical system)
            approved_result = validated_data.get("approved_result_text", "Resultado no disponible")
            
            # Get template
            template = self._APPROVED_TEMPLATES[MessageType.SYSTEM_APPROVED_RESULTS.value].get(
                language, self._APPROVED_TEMPLATES[MessageType.SYSTEM_APPROVED_RESULTS.value]["es"]
            )
            
            # Format message with approved data only
            message = template.format(
                approved_result=approved_result,
                ref_number=ref_number
            )
            
            # Send via MCP WhatsApp
            result = await self._send_whatsapp_message(
                patient_phone_token,
                message,
                MessageType.SYSTEM_APPROVED_RESULTS.value
            )
            
            # Audit log with full validated data
            self._audit_logger.log_patient_message(
                patient_token=patient_phone_token,
                message_type=MessageType.SYSTEM_APPROVED_RESULTS.value,
                ref_number=ref_number,
                approved_data=validated_data,
                success=result.get("success", False)
            )
            
            # Increment counter
            if result.get("success"):
                self.increment_message_count(patient_phone_token)
            
            return result
            
        except UnauthorizedMedicalDataError as e:
            logger.error(f"Unauthorized medical data rejected: {e}")
            return {"success": False, "error": "unauthorized_medical_data"}
        except Exception as e:
            logger.error(f"Error sending approved results: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_error_notification(self,
                                    patient_phone_token: str,
                                    ref_number: str,
                                    language: str = "es") -> Dict[str, Any]:
        """
        Send error notification to patient when processing fails.
        """
        try:
            # Rate limiting check
            if not self.check_rate_limit(patient_phone_token):
                return {"success": False, "error": "rate_limit_exceeded"}
            
            # Get template
            template = self._APPROVED_TEMPLATES[MessageType.ERROR_NOTIFICATION.value].get(
                language, self._APPROVED_TEMPLATES[MessageType.ERROR_NOTIFICATION.value]["es"]
            )
            
            # Format message
            message = template.format(ref_number=ref_number)
            
            # Send via MCP WhatsApp
            result = await self._send_whatsapp_message(
                patient_phone_token,
                message,
                MessageType.ERROR_NOTIFICATION.value
            )
            
            # Audit log
            self._audit_logger.log_patient_message(
                patient_token=patient_phone_token,
                message_type=MessageType.ERROR_NOTIFICATION.value,
                ref_number=ref_number,
                success=result.get("success", False)
            )
            
            # Increment counter
            if result.get("success"):
                self.increment_message_count(patient_phone_token)
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_whatsapp_message(self,
                                   patient_phone_token: str,
                                   message: str,
                                   message_type: str) -> Dict[str, Any]:
        """
        Send message via Twilio MCP WhatsApp integration.
        
        SECURITY: Uses tokenized phone numbers only.
        """
        try:
            # Create MCP gateway with medical compliance
            async with create_mcp_gateway({'medical_compliance': 'hipaa'}) as gateway:
                
                # Convert token back to phone number (securely)
                # NOTE: For demo purposes, using simulated phone resolution
                # In production, this would use secure key-based resolution
                actual_phone = "+56961797823"  # Bruce Wayne's number for demo
                
                # Send WhatsApp message via Twilio MCP
                response = await gateway.whatsapp_operation(
                    'send_message',
                    to=f'whatsapp:{actual_phone}',
                    from_='whatsapp:+14155238886',  # Twilio sandbox number
                    body=message,
                    metadata={
                        'patient_token': patient_phone_token,
                        'message_type': message_type,
                        'timestamp': datetime.utcnow().isoformat(),
                        'agent_id': self.agent_id,
                        'phi_protected': True
                    }
                )
                
                logger.info(f"WhatsApp message sent to {patient_phone_token}: {message_type}")
                return {"success": True, "message_id": response.get("message_id")}
                
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return {"success": False, "error": str(e)}
    
    def handle_incoming_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming patient messages - STRICT POLICY: NO RESPONSES TO QUESTIONS
        
        SAFETY: Always redirect medical questions to healthcare provider.
        """
        patient_phone_token = message_data.get("from_token")
        message_body = message_data.get("body", "").lower()
        
        # Log incoming message
        self._audit_logger.log_incoming_patient_message(
            patient_token=patient_phone_token,
            message_body=message_body
        )
        
        # POLICY: NO medical question answering
        medical_keywords = [
            "dolor", "pain", "duele", "hurt", "que hago", "what do", 
            "medicina", "medicine", "tratamiento", "treatment",
            "doctor", "medico", "grave", "serious", "urgente", "urgent"
        ]
        
        if any(keyword in message_body for keyword in medical_keywords):
            logger.warning(f"Medical question detected from {patient_phone_token}: {message_body}")
            return {
                "response": "Por favor consulta con tu médico tratante para cualquier pregunta médica.",
                "redirect_to_healthcare": True,
                "logged": True
            }
        
        # Default response: redirect all questions
        return {
            "response": "Para consultas médicas, contacta directamente con tu equipo de salud.",
            "redirect_to_healthcare": True, 
            "logged": True
        }
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and statistics"""
        total_messages_today = sum(
            count for key, count in self._message_count_cache.items()
            if datetime.now().date().isoformat() in key
        )
        
        return {
            "agent_id": self.agent_id,
            "status": "operational",
            "guardrails_active": True,
            "total_messages_today": total_messages_today,
            "rate_limit_per_patient": self._MAX_MESSAGES_PER_PATIENT_PER_DAY,
            "allowed_message_types": self._ALLOWED_MESSAGE_TYPES,
            "medical_advice_enabled": False,  # Always False
            "conversation_memory": False,     # Always False
            "phi_tokenization": True         # Always True
        }


# Factory function for easy instantiation
def create_whatsapp_patient_agent(agent_id: str = None) -> WhatsAppPatientAgent:
    """Create WhatsApp Patient Agent instance with proper configuration"""
    return WhatsAppPatientAgent(agent_id or f"whatsapp_patient_{uuid.uuid4().hex[:8]}")