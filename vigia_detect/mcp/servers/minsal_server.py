#!/usr/bin/env python3
"""
Vigia MINSAL MCP Server
Custom MCP server for Chilean Ministry of Health (MINSAL) compliance and integration
Enables regulatory compliance and data reporting for Chilean healthcare system
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

from mcp.server import Server
from mcp.types import (
    Tool, Resource, ResourceTemplate, TextContent,
    ListResourcesResult, ReadResourceResult, CallToolResult
)


@dataclass
class MINSALConfig:
    """MINSAL server configuration"""
    api_key: str
    environment: str = "sandbox"  # sandbox, production
    base_url: str = "https://apis.minsal.cl"
    version: str = "v1"
    timeout: int = 30


class VigiaMINSALServer:
    """Vigia MINSAL MCP Server for Chilean healthcare compliance"""
    
    def __init__(self, config: MINSALConfig):
        self.config = config
        self.server = Server("vigia-minsal")
        self._setup_tools()
        self._setup_resources()
    
    def _setup_tools(self):
        """Setup MINSAL MCP tools"""
        
        @self.server.call_tool()
        async def validate_patient_rut(arguments: Dict[str, Any]) -> List[TextContent]:
            """Validate Chilean RUT (Rol Único Tributario)"""
            try:
                rut = arguments.get("rut", "").replace(".", "").replace("-", "")
                
                if not rut:
                    return [TextContent(
                        type="text",
                        text="❌ RUT is required"
                    )]
                
                # Basic RUT validation algorithm
                if len(rut) < 2:
                    return [TextContent(
                        type="text",
                        text="❌ Invalid RUT format"
                    )]
                
                rut_digits = rut[:-1]
                check_digit = rut[-1].upper()
                
                # Calculate check digit
                multiplier = 2
                total = 0
                
                for digit in reversed(rut_digits):
                    total += int(digit) * multiplier
                    multiplier = 3 if multiplier == 7 else multiplier + 1
                
                remainder = total % 11
                calculated_check = "K" if remainder == 1 else ("0" if remainder == 0 else str(11 - remainder))
                
                is_valid = calculated_check == check_digit
                
                return [TextContent(
                    type="text",
                    text=f"{'✅' if is_valid else '❌'} RUT {rut}: {'Valid' if is_valid else 'Invalid'}\n"
                         f"Expected check digit: {calculated_check}\n"
                         f"Provided check digit: {check_digit}"
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error validating RUT: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def create_lpp_notification(arguments: Dict[str, Any]) -> List[TextContent]:
            """Create LPP notification for MINSAL reporting"""
            try:
                notification_data = arguments.get("notification_data", {})
                
                # Create MINSAL-compliant notification
                minsal_notification = {
                    "tipoNotificacion": "LPP_DETECCION",
                    "establecimiento": {
                        "codigo": notification_data.get("hospital_code", ""),
                        "nombre": notification_data.get("hospital_name", ""),
                        "region": notification_data.get("region", ""),
                        "comuna": notification_data.get("comuna", "")
                    },
                    "paciente": {
                        "rut": notification_data.get("patient_rut", ""),
                        "edad": notification_data.get("patient_age", 0),
                        "sexo": notification_data.get("patient_gender", ""),
                        "prevision": notification_data.get("insurance_type", "FONASA")  # FONASA, ISAPRE, PARTICULAR
                    },
                    "lesion": {
                        "gradoLPP": notification_data.get("lpp_grade", 1),
                        "ubicacionAnatomica": notification_data.get("anatomical_location", ""),
                        "fechaDeteccion": notification_data.get("detection_date", datetime.now().isoformat()),
                        "metodoDeteccion": "IA_VISION_COMPUTACIONAL",
                        "confianzaDeteccion": notification_data.get("confidence", 0.0),
                        "imagenHash": notification_data.get("image_hash", "")
                    },
                    "equipoMedico": {
                        "medicoResponsable": notification_data.get("responsible_physician", ""),
                        "enfermeroACargo": notification_data.get("nurse_in_charge", ""),
                        "unidadServicio": notification_data.get("service_unit", "")
                    },
                    "cumplimientoNormativo": {
                        "protocoloMINSAL": True,
                        "guiaClinicaNacional": True,
                        "normativaHIPAA": True,
                        "ley19628": True  # Ley de Protección de Datos Personales Chile
                    },
                    "sistemaReporte": {
                        "plataforma": "VIGIA_AI_SYSTEM",
                        "version": "1.4.0",
                        "fechaReporte": datetime.now().isoformat(),
                        "tipoReporte": "AUTOMATICO"
                    }
                }
                
                return [TextContent(
                    type="text",
                    text=f"✅ MINSAL LPP Notification created successfully:\n```json\n{json.dumps(minsal_notification, indent=2, ensure_ascii=False)}\n```"
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error creating MINSAL notification: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def validate_minsal_compliance(arguments: Dict[str, Any]) -> List[TextContent]:
            """Validate compliance with MINSAL regulations"""
            try:
                lpp_data = arguments.get("lpp_data", {})
                hospital_data = arguments.get("hospital_data", {})
                
                compliance_check = {
                    "cumplimiento_general": True,
                    "requisitos_obligatorios": [],
                    "recomendaciones": [],
                    "alertas": []
                }
                
                # Check mandatory MINSAL requirements
                required_fields = [
                    ("lpp_grade", "Grado de LPP"),
                    ("detection_date", "Fecha de detección"),
                    ("anatomical_location", "Ubicación anatómica"),
                    ("responsible_physician", "Médico responsable")
                ]
                
                for field, description in required_fields:
                    if not lpp_data.get(field):
                        compliance_check["cumplimiento_general"] = False
                        compliance_check["requisitos_obligatorios"].append(f"❌ Falta: {description}")
                    else:
                        compliance_check["requisitos_obligatorios"].append(f"✅ Completo: {description}")
                
                # Check hospital registration
                if not hospital_data.get("hospital_code"):
                    compliance_check["cumplimiento_general"] = False
                    compliance_check["alertas"].append("❌ Código de establecimiento MINSAL requerido")
                
                # Check LPP grade compliance with MINSAL protocols
                lpp_grade = lpp_data.get("lpp_grade", 0)
                if lpp_grade >= 3:
                    compliance_check["alertas"].append("🚨 LPP Grado 3+ requiere notificación inmediata a MINSAL")
                    compliance_check["recomendaciones"].append("📋 Activar protocolo de escalación MINSAL")
                
                # Check AI system validation
                confidence = lpp_data.get("confidence", 0.0)
                if confidence < 0.8:
                    compliance_check["recomendaciones"].append("⚠️ Confianza < 80% - Requiere validación médica")
                
                # Privacy compliance (Ley 19.628)
                if not lpp_data.get("patient_consent"):
                    compliance_check["alertas"].append("⚠️ Verificar consentimiento informado (Ley 19.628)")
                
                status = "✅ CUMPLE" if compliance_check["cumplimiento_general"] else "❌ NO CUMPLE"
                
                result_text = f"{status} - Validación Cumplimiento MINSAL\n\n"
                
                if compliance_check["requisitos_obligatorios"]:
                    result_text += "📋 Requisitos Obligatorios:\n"
                    for req in compliance_check["requisitos_obligatorios"]:
                        result_text += f"  {req}\n"
                    result_text += "\n"
                
                if compliance_check["alertas"]:
                    result_text += "🚨 Alertas Críticas:\n"
                    for alert in compliance_check["alertas"]:
                        result_text += f"  {alert}\n"
                    result_text += "\n"
                
                if compliance_check["recomendaciones"]:
                    result_text += "💡 Recomendaciones:\n"
                    for rec in compliance_check["recomendaciones"]:
                        result_text += f"  {rec}\n"
                
                return [TextContent(
                    type="text",
                    text=result_text
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error validating MINSAL compliance: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def generate_minsal_report(arguments: Dict[str, Any]) -> List[TextContent]:
            """Generate MINSAL-compliant statistical report"""
            try:
                report_data = arguments.get("report_data", {})
                period = arguments.get("period", "monthly")  # daily, weekly, monthly, yearly
                
                # Generate statistical report format for MINSAL
                report = {
                    "reporte": {
                        "tipo": "ESTADISTICAS_LPP",
                        "periodo": period.upper(),
                        "fechaInicio": report_data.get("start_date", ""),
                        "fechaFin": report_data.get("end_date", ""),
                        "establecimiento": report_data.get("hospital_code", "")
                    },
                    "estadisticas": {
                        "totalDetecciones": report_data.get("total_detections", 0),
                        "distribucionGrados": {
                            "grado1": report_data.get("grade_1_count", 0),
                            "grado2": report_data.get("grade_2_count", 0), 
                            "grado3": report_data.get("grade_3_count", 0),
                            "grado4": report_data.get("grade_4_count", 0)
                        },
                        "distribucionUbicaciones": report_data.get("location_distribution", {}),
                        "distribucionEdades": {
                            "menores65": report_data.get("under_65_count", 0),
                            "mayores65": report_data.get("over_65_count", 0)
                        },
                        "tiposPrevision": {
                            "fonasa": report_data.get("fonasa_count", 0),
                            "isapre": report_data.get("isapre_count", 0),
                            "particular": report_data.get("private_count", 0)
                        }
                    },
                    "indicadores": {
                        "tasaIncidencia": report_data.get("incidence_rate", 0.0),
                        "tasaPrevalencia": report_data.get("prevalence_rate", 0.0),
                        "tiempoPromedioDiagnostico": report_data.get("avg_diagnosis_time", 0.0),
                        "efectividadIA": report_data.get("ai_effectiveness", 0.0)
                    },
                    "cumplimientoNormativo": {
                        "protocolosMINSAL": report_data.get("minsal_protocol_compliance", 100.0),
                        "reportesOportunos": report_data.get("timely_reports", 100.0),
                        "calidadDatos": report_data.get("data_quality", 100.0)
                    },
                    "metadatos": {
                        "fechaGeneracion": datetime.now().isoformat(),
                        "sistemaGenerador": "VIGIA_AI_SYSTEM",
                        "version": "1.4.0",
                        "contactoResponsable": report_data.get("contact_person", "")
                    }
                }
                
                return [TextContent(
                    type="text",
                    text=f"✅ MINSAL Statistical Report generated successfully:\n```json\n{json.dumps(report, indent=2, ensure_ascii=False)}\n```"
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error generating MINSAL report: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def check_hospital_registration(arguments: Dict[str, Any]) -> List[TextContent]:
            """Check if hospital is registered with MINSAL"""
            try:
                hospital_code = arguments.get("hospital_code", "")
                
                if not hospital_code:
                    return [TextContent(
                        type="text",
                        text="❌ Hospital code is required"
                    )]
                
                # Simulate hospital registration check
                # In production, this would query MINSAL's hospital registry
                mock_hospitals = {
                    "HOS001": {
                        "nombre": "Hospital Clínico Universidad de Chile",
                        "region": "Metropolitana",
                        "comuna": "Independencia",
                        "tipo": "Público",
                        "complejidad": "Alta",
                        "estado": "Activo"
                    },
                    "HOS002": {
                        "nombre": "Hospital Salvador",
                        "region": "Metropolitana", 
                        "comuna": "Providencia",
                        "tipo": "Público",
                        "complejidad": "Alta",
                        "estado": "Activo"
                    }
                }
                
                hospital_info = mock_hospitals.get(hospital_code)
                
                if hospital_info:
                    result_text = f"✅ Hospital registrado en MINSAL:\n"
                    result_text += f"Código: {hospital_code}\n"
                    result_text += f"Nombre: {hospital_info['nombre']}\n"
                    result_text += f"Región: {hospital_info['region']}\n"
                    result_text += f"Comuna: {hospital_info['comuna']}\n"
                    result_text += f"Tipo: {hospital_info['tipo']}\n"
                    result_text += f"Complejidad: {hospital_info['complejidad']}\n"
                    result_text += f"Estado: {hospital_info['estado']}\n"
                else:
                    result_text = f"❌ Hospital código {hospital_code} no encontrado en registro MINSAL\n"
                    result_text += "💡 Verificar código o contactar con MINSAL para registro"
                
                return [TextContent(
                    type="text",
                    text=result_text
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error checking hospital registration: {str(e)}"
                )]
    
    def _setup_resources(self):
        """Setup MINSAL MCP resources"""
        
        @self.server.list_resources()
        async def list_resources() -> ListResourcesResult:
            """List available MINSAL resources"""
            return ListResourcesResult(
                resources=[
                    Resource(
                        uri="minsal://notification-template",
                        name="MINSAL Notification Template",
                        description="Template for creating MINSAL-compliant LPP notifications",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="minsal://report-template",
                        name="MINSAL Report Template",
                        description="Template for creating statistical reports for MINSAL",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="minsal://compliance-checklist",
                        name="MINSAL Compliance Checklist",
                        description="Checklist for MINSAL regulatory compliance",
                        mimeType="text/markdown"
                    ),
                    Resource(
                        uri="minsal://lpp-protocols",
                        name="MINSAL LPP Protocols",
                        description="Official MINSAL protocols for pressure injury management",
                        mimeType="application/json"
                    )
                ]
            )
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> ReadResourceResult:
            """Read MINSAL resource templates and protocols"""
            
            if uri == "minsal://notification-template":
                template = {
                    "tipoNotificacion": "LPP_DETECCION",
                    "establecimiento": {
                        "codigo": "{{hospital_code}}",
                        "nombre": "{{hospital_name}}",
                        "region": "{{region}}",
                        "comuna": "{{comuna}}"
                    },
                    "paciente": {
                        "rut": "{{patient_rut}}",
                        "edad": "{{patient_age}}",
                        "sexo": "{{patient_gender}}",
                        "prevision": "{{insurance_type}}"
                    },
                    "lesion": {
                        "gradoLPP": "{{lpp_grade}}",
                        "ubicacionAnatomica": "{{anatomical_location}}",
                        "fechaDeteccion": "{{detection_date}}",
                        "metodoDeteccion": "IA_VISION_COMPUTACIONAL"
                    }
                }
                
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=json.dumps(template, indent=2, ensure_ascii=False)
                        )
                    ]
                )
            
            elif uri == "minsal://compliance-checklist":
                checklist = """# MINSAL Compliance Checklist for LPP Detection

## Requisitos Obligatorios ✅

### Datos del Paciente
- [ ] RUT validado
- [ ] Edad registrada
- [ ] Género registrado
- [ ] Tipo de previsión (FONASA/ISAPRE/PARTICULAR)
- [ ] Consentimiento informado (Ley 19.628)

### Datos de la Lesión
- [ ] Grado LPP según clasificación MINSAL
- [ ] Ubicación anatómica específica
- [ ] Fecha y hora de detección
- [ ] Método de detección documentado
- [ ] Nivel de confianza del sistema IA

### Datos del Establecimiento
- [ ] Código MINSAL del hospital
- [ ] Región y comuna registradas
- [ ] Médico responsable identificado
- [ ] Unidad de servicio especificada

### Cumplimiento Normativo
- [ ] Protocolo MINSAL aplicado
- [ ] Guía clínica nacional seguida
- [ ] Normativa HIPAA cumplida
- [ ] Ley 19.628 respetada

## Alertas Críticas 🚨

### LPP Grado 3+
- [ ] Notificación inmediata a MINSAL
- [ ] Protocolo de escalación activado
- [ ] Equipo médico notificado

### Confianza IA < 80%
- [ ] Validación médica requerida
- [ ] Revisión de imagen por especialista
- [ ] Documentación de validación

## Reporte Estadístico 📊

### Periodicidad
- [ ] Reportes diarios para casos críticos
- [ ] Reportes mensuales estadísticos
- [ ] Reportes anuales de cumplimiento

### Contenido Requerido
- [ ] Distribución por grados de LPP
- [ ] Distribución por ubicación anatómica
- [ ] Distribución por grupos etarios
- [ ] Distribución por tipo de previsión
- [ ] Indicadores de calidad
"""
                
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=checklist
                        )
                    ]
                )
            
            else:
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=f"Resource not found: {uri}"
                        )
                    ]
                )


async def main():
    """Main entry point for Vigia MINSAL MCP Server"""
    
    # Load configuration from environment
    config = MINSALConfig(
        api_key=os.getenv("MINSAL_API_KEY", ""),
        environment=os.getenv("MINSAL_ENVIRONMENT", "sandbox")
    )
    
    # Create and run the server
    minsal_server = VigiaMINSALServer(config)
    
    # Run the server
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await minsal_server.server.run(
            read_stream,
            write_stream,
            minsal_server.server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())