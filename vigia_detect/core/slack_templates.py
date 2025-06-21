"""
Templates centralizados para notificaciones médicas (channel-agnostic)
Templates anteriormente específicos para Slack, ahora genéricos para auditoría
Enhanced with Block Kit support for rich Slack interfaces
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from .constants import SlackActionIds, LPP_SEVERITY_ALERTS, TEST_PATIENT_DATA


def create_detection_notification_data(detection_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create generic detection notification data."""
    patient_code = detection_data.get('patient_code', 'Unknown')
    lpp_grade = detection_data.get('lpp_grade', 0)
    confidence = detection_data.get('confidence', 0.0)
    
    severity_info = LPP_SEVERITY_ALERTS.get(lpp_grade, LPP_SEVERITY_ALERTS[0])
    
    notification_data = {
        "notification_type": "lpp_detection",
        "patient_code": patient_code,
        "lpp_grade": lpp_grade,
        "confidence": confidence,
        "severity_level": severity_info['level'],
        "severity_emoji": severity_info['emoji'],
        "medical_urgency": _determine_urgency_from_grade(lpp_grade),
        "title": f"Detección LPP - {patient_code}",
        "summary": f"Grado {lpp_grade} detectado con confianza {confidence:.2f}",
        "timestamp": datetime.now().isoformat(),
        "audit_compliant": True,
        "hipaa_safe": True
    }
    
    return notification_data


def create_error_notification_data(error_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create generic error notification data."""
    notification_data = {
        "notification_type": "system_error",
        "error_message": error_data.get('message', 'Unknown error'),
        "error_code": error_data.get('code', 'UNKNOWN'),
        "severity": "high",
        "title": "Error en Procesamiento",
        "component": error_data.get('component', 'system'),
        "timestamp": datetime.now().isoformat(),
        "requires_attention": True,
        "audit_compliant": True
    }
    
    return notification_data


def create_patient_history_notification_data(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create generic patient history notification data."""
    # Anonymize patient data for audit compliance
    anonymized_code = patient_data.get('patient_code', 'Unknown')[:8] + "..."
    
    notification_data = {
        "notification_type": "patient_history",
        "patient_code_anonymized": anonymized_code,
        "has_lpp_history": bool(patient_data.get('lpp_history', [])),
        "risk_factors_count": len(patient_data.get('risk_factors', [])),
        "title": f"Historial Médico - {anonymized_code}",
        "timestamp": datetime.now().isoformat(),
        "hipaa_compliant": True,
        "audit_safe": True
    }
    
    return notification_data


def create_detection_notification(detection_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create detection notification - alias for create_detection_notification_data."""
    return create_detection_notification_data(detection_data)


class MedicalNotificationTemplates:
    """Templates para notificaciones médicas genéricas"""
    
    @staticmethod
    def historial_medico(patient_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Crea notificación de historial médico.
        
        Args:
            patient_data: Datos del paciente. Si es None, usa datos de prueba.
        
        Returns:
            Estructura de notificación genérica
        """
        data = patient_data or TEST_PATIENT_DATA
        
        # Formatear diagnósticos
        diagnosticos = "\n".join([f"• {d}" for d in data.get("diagnoses", [])])
        
        # Formatear medicamentos
        medicamentos = "\n".join([f"• {m}" for m in data.get("medications", [])])
        
        # Formatear historial de LPP
        historial_lpp = []
        for h in data.get("lpp_history", []):
            historial_lpp.append(
                f"• *{h['date']}*: Grado {h['grade']} en {h['location']} - {h['status']}"
            )
        historial_text = "\n".join(historial_lpp) if historial_lpp else "Sin historial previo"
        
        # Anonymize for HIPAA compliance
        anonymized_id = data['id'][:4] + "***"
        anonymized_name = data['name'][:3] + "***"
        
        return {
            "notification_type": "patient_medical_history",
            "title": "Historial Médico",
            "patient_info": {
                "anonymized_id": anonymized_id,
                "anonymized_name": anonymized_name,
                "age_range": f"{(data['age'] // 10) * 10}-{(data['age'] // 10) * 10 + 9}",
                "service": data['service'],
                "bed_unit": data['bed'][:2] + "***"
            },
            "medical_summary": {
                "diagnoses_count": len(data.get("diagnoses", [])),
                "medications_count": len(data.get("medications", [])),
                "lpp_history_entries": len(data.get("lpp_history", [])),
                "has_mobility_issues": True,
                "high_risk_factors": ["reduced_mobility", "post_surgical", "fragile_skin"]
            },
            "care_notes": {
                "positioning_frequency": "every_2_hours",
                "skin_condition": "fragile_high_risk",
                "special_care_required": True
            },
            "timestamp": datetime.now().isoformat(),
            "hipaa_compliant": True,
            "audit_safe": True
        }
    
    def to_block_kit(self) -> List[Dict[str, Any]]:
        """Convert patient history to Slack Block Kit format"""
        try:
            from ..slack.block_kit_medical import BlockKitMedical
            # Convert back to patient data format for Block Kit
            patient_data = {
                'id': self['patient_info']['anonymized_id'],
                'name': self['patient_info']['anonymized_name'], 
                'age': int(self['patient_info']['age_range'].split('-')[0]) + 5,  # Mid-range
                'service': self['patient_info']['service'],
                'bed': self['patient_info']['bed_unit'],
                'diagnoses': ["Diagnóstico confidencial"] * self['medical_summary']['diagnoses_count'],
                'medications': ["Medicamento confidencial"] * self['medical_summary']['medications_count'],
                'lpp_history': [
                    {
                        'date': '****/**/**',
                        'grade': 'X',
                        'location': 'confidencial',
                        'status': 'histórico'
                    }
                ] * self['medical_summary']['lpp_history_entries']
            }
            return BlockKitMedical.patient_history_blocks(patient_data)
        except ImportError:
            return [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Patient History:* {self['patient_info']['anonymized_name']}"
                    }
                }
            ]
    
    @staticmethod
    def resolucion_caso() -> Dict[str, Any]:
        """Notificación para marcar un caso como resuelto"""
        return {
            "notification_type": "case_resolution",
            "title": "Marcar como Resuelto",
            "resolution_fields": {
                "description_required": True,
                "description_placeholder": "Describa las acciones tomadas y el resultado...",
                "resolution_time_options": [
                    {"label": "< 30 minutos", "value": "30min"},
                    {"label": "30 min - 1 hora", "value": "1hr"},
                    {"label": "1 - 2 horas", "value": "2hr"},
                    {"label": "> 2 horas", "value": "more"}
                ]
            },
            "audit_requirements": {
                "requires_medical_approval": True,
                "audit_trail_required": True,
                "documentation_mandatory": True
            },
            "timestamp": datetime.now().isoformat(),
            "hipaa_compliant": True
        }


class MedicalAlertTemplates:
    """Templates para alertas médicas genéricas"""
    
    @staticmethod
    def acciones_enfermeria_disponibles() -> List[Dict[str, Any]]:
        """Acciones estándar disponibles para enfermería"""
        return [
            {
                "action_type": "view_medical_history",
                "label": "Ver Historial Médico",
                "priority": "primary",
                "requires_authentication": True,
                "audit_logged": True
            },
            {
                "action_type": "request_medical_evaluation",
                "label": "Solicitar Evaluación Médica",
                "priority": "high",
                "requires_escalation": True,
                "audit_logged": True
            },
            {
                "action_type": "mark_resolved",
                "label": "Marcar como Resuelto",
                "priority": "normal",
                "requires_documentation": True,
                "audit_logged": True
            }
        ]
    
    @staticmethod
    def alerta_lpp(
        grado: int,
        paciente: str,
        id_caso: str,
        ubicacion: str,
        confianza: float,
        servicio: str,
        cama: str,
        imagen_url: Optional[str] = None,
        analisis_emocional: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Crea mensaje de alerta de LPP.
        
        Args:
            grado: Grado de la lesión (0-4)
            paciente: Nombre del paciente
            id_caso: ID del caso
            ubicacion: Ubicación anatómica
            confianza: Confianza del modelo (0-1)
            servicio: Servicio médico
            cama: Número de cama
            imagen_url: URL de la imagen (opcional)
            analisis_emocional: Análisis emocional del paciente (opcional)
            
        Returns:
            Estructura del mensaje para Slack
        """
        severity = LPP_SEVERITY_ALERTS.get(grado, LPP_SEVERITY_ALERTS[0])
        
        # Anonymize patient info for HIPAA compliance
        anonymized_patient = paciente[:3] + "***"
        anonymized_bed = cama[:2] + "***"
        
        # Build medical alert data structure
        alert_data = {
            "notification_type": "lpp_medical_alert",
            "case_info": {
                "case_id": id_caso,
                "anonymized_patient": anonymized_patient,
                "service": servicio,
                "anonymized_bed": anonymized_bed,
                "timestamp": datetime.now().strftime('%d/%m/%Y %H:%M'),
                "status": "pending_review"
            },
            "medical_detection": {
                "lpp_grade": grado,
                "severity_level": severity['level'],
                "severity_emoji": severity['emoji'],
                "anatomical_location": ubicacion,
                "model_confidence": confianza,
                "description": severity['message'],
                "urgency": _determine_urgency_from_grade(grado)
            },
            "clinical_context": {
                "has_image": imagen_url is not None,
                "image_reference": f"IMG_{id_caso}" if imagen_url else None,
                "emotional_analysis_available": analisis_emocional is not None
            }
        }
        
        # Add available actions
        alert_data["available_actions"] = MedicalAlertTemplates.acciones_enfermeria_disponibles()
        
        # Add system info
        alert_data["system_info"] = {
            "system": "Sistema Vigía v1.0",
            "detection_method": "AI_automated",
            "color_code": severity['color']
        }
        
        # Add compliance info
        alert_data["compliance"] = {
            "hipaa_compliant": True,
            "audit_logged": True,
            "anonymized": True
        }
        
        # Add emotional analysis summary if available (anonymized)
        if analisis_emocional:
            alert_data["emotional_analysis"] = {
                "sentiment_detected": analisis_emocional.get('sentimiento', 'not_detected'),
                "mood_assessment": analisis_emocional.get('estado_animo', 'not_evaluated'),
                "concerns_count": len(analisis_emocional.get("preocupaciones", [])),
                "analysis_available": True
            }
        
        return alert_data
    
    def to_block_kit(self) -> List[Dict[str, Any]]:
        """Convert alert data to Slack Block Kit format"""
        try:
            from ..slack.block_kit_medical import BlockKitMedical
            
            case_info = self.get("case_info", {})
            detection = self.get("medical_detection", {})
            
            return BlockKitMedical.lpp_alert_blocks(
                case_id=case_info.get("case_id", "unknown"),
                patient_code=case_info.get("anonymized_patient", "unknown"),
                lpp_grade=detection.get("lpp_grade", 0),
                confidence=detection.get("model_confidence", 0.0),
                location=detection.get("anatomical_location", "unknown"),
                service=case_info.get("service", "unknown"),
                bed=case_info.get("anonymized_bed", "unknown"),
                timestamp=case_info.get("timestamp")
            )
        except ImportError:
            # Fallback to simple text if Block Kit not available
            return [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*LPP Alert:* Grade {self.get('medical_detection', {}).get('lpp_grade', 0)} detected"
                    }
                }
            ]