#!/usr/bin/env python3
"""
Vigia FHIR MCP Server
Custom MCP server for FHIR (Fast Healthcare Interoperability Resources) integration
Enables medical data interchange with hospital systems and EHR platforms
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

try:
    import fhir.resources.patient as fhir_patient
    import fhir.resources.observation as fhir_observation
    import fhir.resources.condition as fhir_condition
    FHIR_AVAILABLE = True
except ImportError:
    FHIR_AVAILABLE = False

from mcp.server import Server
from mcp.types import (
    Tool, Resource, ResourceTemplate, TextContent,
    ListResourcesResult, ReadResourceResult, CallToolResult
)


@dataclass
class FHIRConfig:
    """FHIR server configuration"""
    base_url: str
    client_id: str
    client_secret: str
    version: str = "R4"
    timeout: int = 30


class VigiaFHIRServer:
    """Vigia FHIR MCP Server for medical data interchange"""
    
    def __init__(self, config: FHIRConfig):
        self.config = config
        self.server = Server("vigia-fhir")
        self._setup_tools()
        self._setup_resources()
    
    def _setup_tools(self):
        """Setup FHIR MCP tools"""
        
        @self.server.call_tool()
        async def create_patient(arguments: Dict[str, Any]) -> List[TextContent]:
            """Create a new patient record in FHIR format"""
            try:
                patient_data = arguments.get("patient_data", {})
                
                # Create FHIR Patient resource
                patient = {
                    "resourceType": "Patient",
                    "id": patient_data.get("patient_id", f"vigia-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                    "identifier": [
                        {
                            "use": "official",
                            "system": "http://vigia.medical/patient-id",
                            "value": patient_data.get("patient_id", "")
                        }
                    ],
                    "name": [
                        {
                            "use": "official",
                            "family": patient_data.get("family_name", ""),
                            "given": patient_data.get("given_names", [])
                        }
                    ],
                    "gender": patient_data.get("gender", "unknown"),
                    "birthDate": patient_data.get("birth_date", ""),
                    "active": True,
                    "meta": {
                        "source": "vigia-lpp-detection-system",
                        "lastUpdated": datetime.utcnow().isoformat() + "Z"
                    }
                }
                
                # Add contact information if available
                if patient_data.get("phone") or patient_data.get("email"):
                    patient["telecom"] = []
                    if patient_data.get("phone"):
                        patient["telecom"].append({
                            "system": "phone",
                            "value": patient_data["phone"],
                            "use": "mobile"
                        })
                    if patient_data.get("email"):
                        patient["telecom"].append({
                            "system": "email", 
                            "value": patient_data["email"]
                        })
                
                return [TextContent(
                    type="text",
                    text=f"✅ FHIR Patient created successfully:\n```json\n{json.dumps(patient, indent=2)}\n```"
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error creating FHIR Patient: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def create_lpp_observation(arguments: Dict[str, Any]) -> List[TextContent]:
            """Create a pressure injury (LPP) observation in FHIR format"""
            try:
                lpp_data = arguments.get("lpp_data", {})
                patient_id = arguments.get("patient_id", "")
                
                # Create FHIR Observation for LPP detection
                observation = {
                    "resourceType": "Observation",
                    "id": f"lpp-obs-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "status": "final",
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                    "code": "imaging",
                                    "display": "Imaging"
                                }
                            ]
                        }
                    ],
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "399966005",
                                "display": "Pressure ulcer"
                            }
                        ],
                        "text": "Pressure Injury (LPP) Detection"
                    },
                    "subject": {
                        "reference": f"Patient/{patient_id}",
                        "display": f"Patient {patient_id}"
                    },
                    "effectiveDateTime": datetime.utcnow().isoformat() + "Z",
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://vigia.medical/lpp-grading",
                                "code": f"grade-{lpp_data.get('grade', 0)}",
                                "display": f"LPP Grade {lpp_data.get('grade', 0)}"
                            }
                        ]
                    },
                    "component": [
                        {
                            "code": {
                                "coding": [
                                    {
                                        "system": "http://vigia.medical/detection-confidence",
                                        "code": "confidence",
                                        "display": "Detection Confidence"
                                    }
                                ]
                            },
                            "valueQuantity": {
                                "value": lpp_data.get("confidence", 0.0),
                                "unit": "probability",
                                "system": "http://unitsofmeasure.org",
                                "code": "1"
                            }
                        },
                        {
                            "code": {
                                "coding": [
                                    {
                                        "system": "http://snomed.info/sct", 
                                        "code": "363698007",
                                        "display": "Finding site"
                                    }
                                ]
                            },
                            "valueString": lpp_data.get("anatomical_location", "Unknown")
                        }
                    ],
                    "meta": {
                        "source": "vigia-ai-detection-system",
                        "lastUpdated": datetime.utcnow().isoformat() + "Z",
                        "tag": [
                            {
                                "system": "http://vigia.medical/detection-method",
                                "code": "ai-computer-vision",
                                "display": "AI Computer Vision Detection"
                            }
                        ]
                    }
                }
                
                # Add device information if available
                if lpp_data.get("device_info"):
                    observation["device"] = {
                        "display": f"Vigia AI System - {lpp_data['device_info']}"
                    }
                
                return [TextContent(
                    type="text",
                    text=f"✅ FHIR LPP Observation created successfully:\n```json\n{json.dumps(observation, indent=2)}\n```"
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error creating FHIR LPP Observation: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def create_condition(arguments: Dict[str, Any]) -> List[TextContent]:
            """Create a medical condition in FHIR format"""
            try:
                condition_data = arguments.get("condition_data", {})
                patient_id = arguments.get("patient_id", "")
                
                # Create FHIR Condition resource
                condition = {
                    "resourceType": "Condition",
                    "id": f"lpp-condition-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "clinicalStatus": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                                "code": condition_data.get("clinical_status", "active"),
                                "display": condition_data.get("clinical_status", "active").title()
                            }
                        ]
                    },
                    "verificationStatus": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                                "code": "confirmed",
                                "display": "Confirmed"
                            }
                        ]
                    },
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                                    "code": "problem-list-item",
                                    "display": "Problem List Item"
                                }
                            ]
                        }
                    ],
                    "severity": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": self._get_severity_code(condition_data.get("grade", 1)),
                                "display": self._get_severity_display(condition_data.get("grade", 1))
                            }
                        ]
                    },
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "399966005",
                                "display": "Pressure ulcer"
                            }
                        ],
                        "text": f"Pressure Injury Grade {condition_data.get('grade', 1)}"
                    },
                    "bodySite": [
                        {
                            "coding": [
                                {
                                    "system": "http://snomed.info/sct",
                                    "code": self._get_body_site_code(condition_data.get("location", "")),
                                    "display": condition_data.get("location", "Unknown location")
                                }
                            ]
                        }
                    ],
                    "subject": {
                        "reference": f"Patient/{patient_id}",
                        "display": f"Patient {patient_id}"
                    },
                    "onsetDateTime": condition_data.get("onset_date", datetime.utcnow().isoformat() + "Z"),
                    "recordedDate": datetime.utcnow().isoformat() + "Z",
                    "meta": {
                        "source": "vigia-medical-system",
                        "lastUpdated": datetime.utcnow().isoformat() + "Z"
                    }
                }
                
                return [TextContent(
                    type="text",
                    text=f"✅ FHIR Condition created successfully:\n```json\n{json.dumps(condition, indent=2)}\n```"
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error creating FHIR Condition: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def validate_fhir_resource(arguments: Dict[str, Any]) -> List[TextContent]:
            """Validate a FHIR resource against the specification"""
            try:
                resource = arguments.get("resource", {})
                resource_type = resource.get("resourceType", "")
                
                # Basic validation
                validation_results = {
                    "valid": True,
                    "errors": [],
                    "warnings": []
                }
                
                # Check required fields
                if not resource_type:
                    validation_results["valid"] = False
                    validation_results["errors"].append("Missing required field: resourceType")
                
                if resource_type == "Patient":
                    if not resource.get("identifier"):
                        validation_results["warnings"].append("Patient should have identifier")
                
                elif resource_type == "Observation":
                    required_fields = ["status", "code", "subject"]
                    for field in required_fields:
                        if not resource.get(field):
                            validation_results["valid"] = False
                            validation_results["errors"].append(f"Missing required field: {field}")
                
                # Additional Vigia-specific validations
                if resource.get("meta", {}).get("source") and "vigia" not in resource["meta"]["source"]:
                    validation_results["warnings"].append("Resource not marked as Vigia-generated")
                
                status = "✅ Valid" if validation_results["valid"] else "❌ Invalid"
                result_text = f"{status} FHIR Resource Validation:\n"
                result_text += f"Resource Type: {resource_type}\n"
                
                if validation_results["errors"]:
                    result_text += f"\n❌ Errors:\n"
                    for error in validation_results["errors"]:
                        result_text += f"  - {error}\n"
                
                if validation_results["warnings"]:
                    result_text += f"\n⚠️ Warnings:\n"
                    for warning in validation_results["warnings"]:
                        result_text += f"  - {warning}\n"
                
                return [TextContent(
                    type="text",
                    text=result_text
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error validating FHIR resource: {str(e)}"
                )]
    
    def _setup_resources(self):
        """Setup FHIR MCP resources"""
        
        @self.server.list_resources()
        async def list_resources() -> ListResourcesResult:
            """List available FHIR resources"""
            return ListResourcesResult(
                resources=[
                    Resource(
                        uri="fhir://patient-template",
                        name="FHIR Patient Template",
                        description="Template for creating FHIR Patient resources",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="fhir://observation-template",
                        name="FHIR Observation Template",
                        description="Template for creating FHIR Observation resources for LPP detection",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="fhir://condition-template",
                        name="FHIR Condition Template", 
                        description="Template for creating FHIR Condition resources",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="fhir://vigia-profiles",
                        name="Vigia FHIR Profiles",
                        description="Custom FHIR profiles for Vigia medical system",
                        mimeType="application/json"
                    )
                ]
            )
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> ReadResourceResult:
            """Read FHIR resource templates and profiles"""
            
            if uri == "fhir://patient-template":
                template = {
                    "resourceType": "Patient",
                    "id": "{{patient_id}}",
                    "identifier": [
                        {
                            "use": "official",
                            "system": "http://vigia.medical/patient-id",
                            "value": "{{patient_id}}"
                        }
                    ],
                    "name": [
                        {
                            "use": "official",
                            "family": "{{family_name}}",
                            "given": ["{{given_name}}"]
                        }
                    ],
                    "gender": "{{gender}}",
                    "birthDate": "{{birth_date}}",
                    "active": True
                }
                
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=json.dumps(template, indent=2)
                        )
                    ]
                )
            
            elif uri == "fhir://observation-template":
                template = {
                    "resourceType": "Observation",
                    "status": "final",
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                    "code": "imaging",
                                    "display": "Imaging"
                                }
                            ]
                        }
                    ],
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "399966005",
                                "display": "Pressure ulcer"
                            }
                        ]
                    },
                    "subject": {
                        "reference": "Patient/{{patient_id}}"
                    },
                    "valueCodeableConcept": {
                        "coding": [
                            {
                                "system": "http://vigia.medical/lpp-grading",
                                "code": "grade-{{lpp_grade}}",
                                "display": "LPP Grade {{lpp_grade}}"
                            }
                        ]
                    }
                }
                
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=json.dumps(template, indent=2)
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
    
    def _get_severity_code(self, grade: int) -> str:
        """Get SNOMED CT severity code for LPP grade"""
        severity_map = {
            1: "255604002",  # Mild
            2: "6736007",    # Moderate  
            3: "24484000",   # Severe
            4: "24484000"    # Severe
        }
        return severity_map.get(grade, "255604002")
    
    def _get_severity_display(self, grade: int) -> str:
        """Get severity display text for LPP grade"""
        severity_map = {
            1: "Mild severity",
            2: "Moderate severity",
            3: "Severe",
            4: "Severe"
        }
        return severity_map.get(grade, "Mild severity")
    
    def _get_body_site_code(self, location: str) -> str:
        """Get SNOMED CT body site code for anatomical location"""
        location_map = {
            "sacrum": "54735007",
            "heel": "76853006", 
            "ankle": "70258002",
            "hip": "29836001",
            "elbow": "16953009",
            "shoulder": "16982005"
        }
        return location_map.get(location.lower(), "38266002")  # Default: entire body


async def main():
    """Main entry point for Vigia FHIR MCP Server"""
    
    # Load configuration from environment
    config = FHIRConfig(
        base_url=os.getenv("FHIR_BASE_URL", "https://hapi.fhir.org/baseR4"),
        client_id=os.getenv("FHIR_CLIENT_ID", ""),
        client_secret=os.getenv("FHIR_CLIENT_SECRET", "")
    )
    
    # Create and run the server
    fhir_server = VigiaFHIRServer(config)
    
    # Run the server
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await fhir_server.server.run(
            read_stream,
            write_stream,
            fhir_server.server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())