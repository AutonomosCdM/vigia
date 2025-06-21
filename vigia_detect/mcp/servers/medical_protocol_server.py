#!/usr/bin/env python3
"""
Vigia Medical Protocol MCP Server
Custom MCP server for medical protocol management and clinical guidelines
Enables AI-powered protocol search, recommendation, and compliance checking
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import hashlib

from mcp.server import Server
from mcp.types import (
    Tool, Resource, ResourceTemplate, TextContent,
    ListResourcesResult, ReadResourceResult, CallToolResult
)


@dataclass
class ProtocolConfig:
    """Medical protocol server configuration"""
    protocol_db_path: str
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    max_protocols: int = 1000
    cache_ttl: int = 3600  # 1 hour


class VigiaMedicalProtocolServer:
    """Vigia Medical Protocol MCP Server for clinical guidelines"""
    
    def __init__(self, config: ProtocolConfig):
        self.config = config
        self.server = Server("vigia-medical-protocol")
        self.protocols_db = self._load_protocols()
        self._setup_tools()
        self._setup_resources()
    
    def _load_protocols(self) -> Dict[str, Any]:
        """Load medical protocols database"""
        # In production, this would load from a real database
        # For now, we'll use predefined protocols
        return {
            "lpp_prevention_protocol_v2023": {
                "id": "lpp_prevention_protocol_v2023",
                "name": "Pressure Injury Prevention Protocol 2023",
                "category": "prevention",
                "severity": "all_grades",
                "evidence_level": "A",
                "source": "NPUAP/EPUAP/PPPIA 2019",
                "last_updated": "2023-01-15",
                "content": {
                    "overview": "Comprehensive evidence-based protocol for pressure injury prevention",
                    "key_interventions": [
                        "Risk assessment using validated tools (Braden Scale)",
                        "Repositioning every 2 hours for high-risk patients",
                        "Use of pressure-redistributing support surfaces",
                        "Skin inspection twice daily",
                        "Nutritional optimization",
                        "Moisture management"
                    ],
                    "contraindications": [
                        "Unstable spinal fractures (limit repositioning)",
                        "Recent surgical procedures affecting positioning"
                    ],
                    "monitoring": {
                        "frequency": "Every 8 hours",
                        "parameters": ["Skin integrity", "Braden Scale score", "Nutritional status"]
                    }
                },
                "ai_keywords": ["prevention", "pressure injury", "ulcer", "skin", "risk assessment", "braden"],
                "npuap_reference": "NPUAP-2019-Prevention-Recommendations"
            },
            "lpp_grade_1_treatment_protocol": {
                "id": "lpp_grade_1_treatment_protocol",
                "name": "Grade 1 Pressure Injury Treatment Protocol",
                "category": "treatment",
                "severity": "grade_1",
                "evidence_level": "A",
                "source": "NPUAP/EPUAP/PPPIA 2019",
                "last_updated": "2023-01-15",
                "content": {
                    "overview": "Evidence-based treatment for Grade 1 pressure injuries",
                    "immediate_actions": [
                        "Remove or redistribute pressure immediately",
                        "Assess and document wound characteristics",
                        "Initiate prevention protocol",
                        "Patient/family education"
                    ],
                    "treatment_plan": [
                        "Continue pressure relief measures",
                        "Gentle skin cleansing with pH-balanced products",
                        "Apply skin protectant/barrier cream",
                        "Monitor for progression to Grade 2"
                    ],
                    "expected_outcome": "Resolution within 3-7 days with proper care",
                    "escalation_criteria": [
                        "No improvement within 48 hours",
                        "Progression to Grade 2 or higher",
                        "Signs of infection"
                    ]
                },
                "ai_keywords": ["grade 1", "treatment", "non-blanchable", "erythema", "intact skin"],
                "npuap_reference": "NPUAP-2019-Treatment-Grade-1"
            },
            "lpp_grade_2_treatment_protocol": {
                "id": "lpp_grade_2_treatment_protocol", 
                "name": "Grade 2 Pressure Injury Treatment Protocol",
                "category": "treatment",
                "severity": "grade_2",
                "evidence_level": "A",
                "source": "NPUAP/EPUAP/PPPIA 2019",
                "last_updated": "2023-01-15",
                "content": {
                    "overview": "Evidence-based treatment for Grade 2 pressure injuries with partial-thickness skin loss",
                    "immediate_actions": [
                        "Remove pressure source immediately",
                        "Assess wound bed and surrounding skin",
                        "Photograph for documentation",
                        "Implement pressure redistribution strategy"
                    ],
                    "wound_care": [
                        "Gentle cleansing with saline or wound cleanser",
                        "Debridement of loose necrotic tissue (if present)",
                        "Apply appropriate dressing (hydrocolloid, foam, hydrogel)",
                        "Protect periwound skin"
                    ],
                    "dressing_schedule": "Change every 3-7 days or as needed",
                    "healing_time": "2-6 weeks with optimal care",
                    "complications_watch": [
                        "Signs of infection",
                        "Wound expansion",
                        "Progression to Grade 3"
                    ]
                },
                "ai_keywords": ["grade 2", "partial thickness", "blister", "shallow", "dermis", "dressing"],
                "npuap_reference": "NPUAP-2019-Treatment-Grade-2"
            },
            "lpp_grade_3_emergency_protocol": {
                "id": "lpp_grade_3_emergency_protocol",
                "name": "Grade 3 Pressure Injury Emergency Protocol",
                "category": "emergency",
                "severity": "grade_3",
                "evidence_level": "A",
                "source": "NPUAP/EPUAP/PPPIA 2019",
                "last_updated": "2023-01-15",
                "content": {
                    "overview": "URGENT: Full-thickness skin loss requiring immediate specialist intervention",
                    "immediate_actions": [
                        "IMMEDIATELY notify wound care specialist",
                        "Remove ALL pressure from affected area",
                        "Assess for signs of infection/sepsis",
                        "Pain assessment and management",
                        "Nutritional consultation"
                    ],
                    "emergency_assessment": [
                        "Wound size, depth, and tissue type",
                        "Presence of undermining or tunneling",
                        "Signs of infection (fever, elevated WBC, drainage)",
                        "Patient hemodynamic status"
                    ],
                    "specialist_consultation": [
                        "Wound care specialist within 24 hours",
                        "Plastic surgery if complex reconstruction needed",
                        "Infectious disease if signs of infection"
                    ],
                    "escalation_timeline": "STAT notification, specialist within 24h"
                },
                "ai_keywords": ["grade 3", "full thickness", "subcutaneous", "emergency", "specialist", "urgent"],
                "npuap_reference": "NPUAP-2019-Treatment-Grade-3"
            },
            "minsal_lpp_reporting_protocol": {
                "id": "minsal_lpp_reporting_protocol",
                "name": "MINSAL LPP Reporting Protocol (Chile)",
                "category": "regulatory",
                "severity": "all_grades",
                "evidence_level": "B",
                "source": "MINSAL Chile 2022",
                "last_updated": "2023-01-15",
                "content": {
                    "overview": "Chilean Ministry of Health mandatory reporting requirements for pressure injuries",
                    "reporting_requirements": [
                        "All Grade 2+ pressure injuries must be reported",
                        "Report within 24 hours of detection",
                        "Include patient demographics (with privacy protection)",
                        "Document prevention measures in place"
                    ],
                    "required_data": [
                        "Patient RUT (encrypted for privacy)",
                        "Grade and location of pressure injury",
                        "Date/time of detection",
                        "Preventive measures implemented",
                        "Hospital/clinic identification code"
                    ],
                    "submission_process": [
                        "Complete MINSAL Form 007-LPP",
                        "Submit via MINSAL digital platform",
                        "Maintain local copy for 7 years",
                        "Follow up reports for Grade 3+ cases"
                    ],
                    "compliance_timeline": "24 hours for initial report, weekly updates for Grade 3+"
                },
                "ai_keywords": ["minsal", "reporting", "chile", "regulatory", "compliance", "mandatory"],
                "minsal_reference": "MINSAL-2022-LPP-Reporting-Guidelines"
            }
        }
    
    def _setup_tools(self):
        """Setup Medical Protocol MCP tools"""
        
        @self.server.call_tool()
        async def search_protocols(arguments: Dict[str, Any]) -> List[TextContent]:
            """Search medical protocols by keywords or criteria"""
            try:
                query = arguments.get("query", "").lower()
                category = arguments.get("category", "")  # prevention, treatment, emergency, regulatory
                severity = arguments.get("severity", "")  # grade_1, grade_2, grade_3, grade_4
                evidence_level = arguments.get("evidence_level", "")  # A, B, C
                
                if not query and not category and not severity:
                    return [TextContent(
                        type="text",
                        text="❌ Please provide at least one search criteria (query, category, severity, or evidence_level)"
                    )]
                
                matching_protocols = []
                
                for protocol_id, protocol in self.protocols_db.items():
                    matches = True
                    
                    # Check query against keywords and content
                    if query:
                        query_match = (
                            query in protocol.get("name", "").lower() or
                            query in protocol.get("category", "").lower() or
                            any(query in keyword for keyword in protocol.get("ai_keywords", []))
                        )
                        if not query_match:
                            matches = False
                    
                    # Check category
                    if category and protocol.get("category", "") != category:
                        matches = False
                    
                    # Check severity
                    if severity and protocol.get("severity", "") != severity and protocol.get("severity", "") != "all_grades":
                        matches = False
                    
                    # Check evidence level
                    if evidence_level and protocol.get("evidence_level", "") != evidence_level:
                        matches = False
                    
                    if matches:
                        matching_protocols.append(protocol)
                
                if matching_protocols:
                    result_text = f"✅ Found {len(matching_protocols)} matching protocols:\n\n"
                    
                    for i, protocol in enumerate(matching_protocols, 1):
                        result_text += f"{i}. **{protocol['name']}**\n"
                        result_text += f"   ID: {protocol['id']}\n"
                        result_text += f"   Category: {protocol['category']}\n"
                        result_text += f"   Severity: {protocol['severity']}\n"
                        result_text += f"   Evidence Level: {protocol['evidence_level']}\n"
                        result_text += f"   Source: {protocol['source']}\n"
                        result_text += f"   Updated: {protocol['last_updated']}\n\n"
                else:
                    result_text = f"❌ No protocols found matching criteria:\n"
                    result_text += f"Query: {query}\n"
                    result_text += f"Category: {category}\n"
                    result_text += f"Severity: {severity}\n"
                    result_text += f"Evidence Level: {evidence_level}"
                
                return [TextContent(
                    type="text",
                    text=result_text
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error searching protocols: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def get_protocol_details(arguments: Dict[str, Any]) -> List[TextContent]:
            """Get detailed information for a specific protocol"""
            try:
                protocol_id = arguments.get("protocol_id", "")
                
                if not protocol_id:
                    return [TextContent(
                        type="text",
                        text="❌ Protocol ID is required"
                    )]
                
                protocol = self.protocols_db.get(protocol_id)
                
                if not protocol:
                    available_ids = list(self.protocols_db.keys())
                    return [TextContent(
                        type="text",
                        text=f"❌ Protocol '{protocol_id}' not found.\n\nAvailable protocols:\n" + 
                             "\n".join(f"- {pid}" for pid in available_ids)
                    )]
                
                # Format detailed protocol information
                result_text = f"📋 **{protocol['name']}**\n\n"
                result_text += f"**Protocol ID**: {protocol['id']}\n"
                result_text += f"**Category**: {protocol['category']}\n"
                result_text += f"**Severity Level**: {protocol['severity']}\n"
                result_text += f"**Evidence Level**: {protocol['evidence_level']}\n"
                result_text += f"**Source**: {protocol['source']}\n"
                result_text += f"**Last Updated**: {protocol['last_updated']}\n\n"
                
                # Protocol content
                content = protocol.get("content", {})
                if content.get("overview"):
                    result_text += f"**Overview**:\n{content['overview']}\n\n"
                
                if content.get("immediate_actions"):
                    result_text += f"**Immediate Actions**:\n"
                    for action in content["immediate_actions"]:
                        result_text += f"• {action}\n"
                    result_text += "\n"
                
                if content.get("key_interventions"):
                    result_text += f"**Key Interventions**:\n"
                    for intervention in content["key_interventions"]:
                        result_text += f"• {intervention}\n"
                    result_text += "\n"
                
                if content.get("treatment_plan"):
                    result_text += f"**Treatment Plan**:\n"
                    for step in content["treatment_plan"]:
                        result_text += f"• {step}\n"
                    result_text += "\n"
                
                if content.get("escalation_criteria"):
                    result_text += f"**Escalation Criteria**:\n"
                    for criteria in content["escalation_criteria"]:
                        result_text += f"• {criteria}\n"
                    result_text += "\n"
                
                if content.get("contraindications"):
                    result_text += f"**Contraindications**:\n"
                    for contraindication in content["contraindications"]:
                        result_text += f"• {contraindication}\n"
                    result_text += "\n"
                
                # References
                if protocol.get("npuap_reference"):
                    result_text += f"**NPUAP Reference**: {protocol['npuap_reference']}\n"
                if protocol.get("minsal_reference"):
                    result_text += f"**MINSAL Reference**: {protocol['minsal_reference']}\n"
                
                return [TextContent(
                    type="text",
                    text=result_text
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error getting protocol details: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def recommend_protocol(arguments: Dict[str, Any]) -> List[TextContent]:
            """Recommend appropriate protocol based on LPP detection data"""
            try:
                lpp_data = arguments.get("lpp_data", {})
                patient_context = arguments.get("patient_context", {})
                
                lpp_grade = lpp_data.get("grade", 0)
                confidence = lpp_data.get("confidence", 0.0)
                location = lpp_data.get("anatomical_location", "")
                
                if lpp_grade == 0:
                    return [TextContent(
                        type="text",
                        text="❌ LPP grade is required for protocol recommendation"
                    )]
                
                recommendations = []
                
                # Primary protocol recommendation based on grade
                if lpp_grade == 1:
                    primary_protocol = "lpp_grade_1_treatment_protocol"
                    urgency = "🟡 Moderate Priority"
                elif lpp_grade == 2:
                    primary_protocol = "lpp_grade_2_treatment_protocol"
                    urgency = "🟠 High Priority"
                elif lpp_grade >= 3:
                    primary_protocol = "lpp_grade_3_emergency_protocol"
                    urgency = "🔴 EMERGENCY - Immediate Action Required"
                else:
                    primary_protocol = "lpp_prevention_protocol_v2023"
                    urgency = "🟢 Prevention Focus"
                
                recommendations.append({
                    "protocol_id": primary_protocol,
                    "reason": f"Primary treatment protocol for Grade {lpp_grade} LPP",
                    "priority": "Primary",
                    "urgency": urgency
                })
                
                # Additional recommendations
                
                # Always recommend prevention protocol to prevent new lesions
                if primary_protocol != "lpp_prevention_protocol_v2023":
                    recommendations.append({
                        "protocol_id": "lpp_prevention_protocol_v2023",
                        "reason": "Prevent additional pressure injuries",
                        "priority": "Secondary",
                        "urgency": "🟢 Ongoing"
                    })
                
                # MINSAL reporting if applicable
                if patient_context.get("country") == "chile" or patient_context.get("regulatory_domain") == "minsal":
                    if lpp_grade >= 2:  # MINSAL requires reporting for Grade 2+
                        recommendations.append({
                            "protocol_id": "minsal_lpp_reporting_protocol",
                            "reason": "Mandatory MINSAL reporting for Grade 2+ pressure injuries",
                            "priority": "Regulatory",
                            "urgency": "🟡 Within 24 hours"
                        })
                
                # Low confidence recommendation
                if confidence < 0.8:
                    recommendations.append({
                        "protocol_id": "clinical_validation_protocol",
                        "reason": f"Low AI confidence ({confidence:.2f}) requires medical validation",
                        "priority": "Validation",
                        "urgency": "🟡 Before treatment"
                    })
                
                # Format recommendations
                result_text = f"🎯 **Protocol Recommendations for Grade {lpp_grade} LPP**\n\n"
                result_text += f"**Detection Confidence**: {confidence:.2f}\n"
                result_text += f"**Location**: {location or 'Not specified'}\n\n"
                
                for i, rec in enumerate(recommendations, 1):
                    result_text += f"**{i}. {rec['priority']} Protocol**\n"
                    result_text += f"   {rec['urgency']}\n"
                    result_text += f"   Protocol: {rec['protocol_id']}\n"
                    result_text += f"   Reason: {rec['reason']}\n\n"
                
                # Special alerts for high-grade injuries
                if lpp_grade >= 3:
                    result_text += "🚨 **CRITICAL ALERTS**:\n"
                    result_text += "• Notify wound care specialist immediately\n"
                    result_text += "• Remove ALL pressure from affected area\n"
                    result_text += "• Assess for signs of infection\n"
                    result_text += "• Document thoroughly for legal/regulatory compliance\n\n"
                
                result_text += "💡 Use `get_protocol_details` tool with protocol_id to view full protocol content."
                
                return [TextContent(
                    type="text",
                    text=result_text
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error recommending protocol: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def validate_protocol_compliance(arguments: Dict[str, Any]) -> List[TextContent]:
            """Validate compliance with selected medical protocol"""
            try:
                protocol_id = arguments.get("protocol_id", "")
                implemented_actions = arguments.get("implemented_actions", [])
                patient_data = arguments.get("patient_data", {})
                
                if not protocol_id:
                    return [TextContent(
                        type="text",
                        text="❌ Protocol ID is required"
                    )]
                
                protocol = self.protocols_db.get(protocol_id)
                if not protocol:
                    return [TextContent(
                        type="text",
                        text=f"❌ Protocol '{protocol_id}' not found"
                    )]
                
                compliance_check = {
                    "protocol_name": protocol["name"],
                    "compliant": True,
                    "completed_actions": [],
                    "missing_actions": [],
                    "compliance_score": 0.0,
                    "recommendations": []
                }
                
                # Get required actions from protocol
                content = protocol.get("content", {})
                required_actions = []
                
                if content.get("immediate_actions"):
                    required_actions.extend(content["immediate_actions"])
                if content.get("key_interventions"):
                    required_actions.extend(content["key_interventions"])
                if content.get("treatment_plan"):
                    required_actions.extend(content["treatment_plan"])
                
                # Check compliance
                for action in required_actions:
                    action_key = action.lower().replace(" ", "_")
                    if action_key in [a.lower().replace(" ", "_") for a in implemented_actions]:
                        compliance_check["completed_actions"].append(action)
                    else:
                        compliance_check["missing_actions"].append(action)
                        compliance_check["compliant"] = False
                
                # Calculate compliance score
                total_actions = len(required_actions)
                completed_actions = len(compliance_check["completed_actions"])
                if total_actions > 0:
                    compliance_check["compliance_score"] = completed_actions / total_actions
                
                # Generate recommendations
                if compliance_check["missing_actions"]:
                    compliance_check["recommendations"].append(
                        "Complete all missing required actions to achieve full protocol compliance"
                    )
                
                if compliance_check["compliance_score"] < 0.8:
                    compliance_check["recommendations"].append(
                        "Compliance score below 80% - review protocol implementation"
                    )
                
                # Format result
                status = "✅ COMPLIANT" if compliance_check["compliant"] else "❌ NON-COMPLIANT"
                score_color = "🟢" if compliance_check["compliance_score"] >= 0.8 else "🟡" if compliance_check["compliance_score"] >= 0.6 else "🔴"
                
                result_text = f"{status} - Protocol Compliance Check\n\n"
                result_text += f"**Protocol**: {compliance_check['protocol_name']}\n"
                result_text += f"**Compliance Score**: {score_color} {compliance_check['compliance_score']:.1%}\n\n"
                
                if compliance_check["completed_actions"]:
                    result_text += "✅ **Completed Actions**:\n"
                    for action in compliance_check["completed_actions"]:
                        result_text += f"• {action}\n"
                    result_text += "\n"
                
                if compliance_check["missing_actions"]:
                    result_text += "❌ **Missing Actions**:\n"
                    for action in compliance_check["missing_actions"]:
                        result_text += f"• {action}\n"
                    result_text += "\n"
                
                if compliance_check["recommendations"]:
                    result_text += "💡 **Recommendations**:\n"
                    for rec in compliance_check["recommendations"]:
                        result_text += f"• {rec}\n"
                
                return [TextContent(
                    type="text",
                    text=result_text
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error validating protocol compliance: {str(e)}"
                )]
    
    def _setup_resources(self):
        """Setup Medical Protocol MCP resources"""
        
        @self.server.list_resources()
        async def list_resources() -> ListResourcesResult:
            """List available medical protocol resources"""
            return ListResourcesResult(
                resources=[
                    Resource(
                        uri="protocols://available-protocols",
                        name="Available Medical Protocols",
                        description="List of all available medical protocols in the database",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="protocols://evidence-levels",
                        name="Evidence Level Guidelines",
                        description="Explanation of evidence levels (A, B, C) used in protocols",
                        mimeType="text/markdown"
                    ),
                    Resource(
                        uri="protocols://protocol-categories",
                        name="Protocol Categories",
                        description="Categories of medical protocols (prevention, treatment, emergency, regulatory)",
                        mimeType="text/markdown"
                    ),
                    Resource(
                        uri="protocols://npuap-guidelines",
                        name="NPUAP 2019 Guidelines",
                        description="Summary of NPUAP/EPUAP/PPPIA 2019 pressure injury guidelines",
                        mimeType="text/markdown"
                    )
                ]
            )
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> ReadResourceResult:
            """Read medical protocol resource documentation"""
            
            if uri == "protocols://available-protocols":
                protocol_list = []
                for protocol_id, protocol in self.protocols_db.items():
                    protocol_list.append({
                        "id": protocol_id,
                        "name": protocol["name"],
                        "category": protocol["category"],
                        "severity": protocol["severity"],
                        "evidence_level": protocol["evidence_level"],
                        "last_updated": protocol["last_updated"]
                    })
                
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=json.dumps(protocol_list, indent=2)
                        )
                    ]
                )
            
            elif uri == "protocols://evidence-levels":
                evidence_doc = """# Evidence Levels for Medical Protocols

## Level A - Strong Evidence
- Multiple high-quality randomized controlled trials (RCTs)
- Systematic reviews and meta-analyses
- Strong recommendation for use
- Benefits clearly outweigh risks

## Level B - Moderate Evidence  
- Limited RCTs or single high-quality RCT
- Well-designed cohort studies
- Moderate recommendation for use
- Benefits likely outweigh risks

## Level C - Weak Evidence
- Expert opinion and consensus
- Case series or case reports
- Weak recommendation for use
- Benefits may outweigh risks

## Protocol Evidence Sources

### NPUAP/EPUAP/PPPIA 2019
- International guideline for pressure injury prevention and treatment
- Evidence-based recommendations
- Gold standard for pressure injury care

### MINSAL Chile
- Chilean Ministry of Health guidelines
- Adapted for local healthcare system
- Regulatory compliance requirements
"""
                
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=evidence_doc
                        )
                    ]
                )
            
            elif uri == "protocols://protocol-categories":
                categories_doc = """# Medical Protocol Categories

## Prevention Protocols
- **Purpose**: Prevent development of pressure injuries
- **Target Population**: All at-risk patients
- **Key Elements**: Risk assessment, positioning, skin care, nutrition
- **Implementation**: Proactive, ongoing

## Treatment Protocols
- **Purpose**: Manage existing pressure injuries
- **Target Population**: Patients with confirmed pressure injuries
- **Key Elements**: Wound care, pressure relief, monitoring
- **Implementation**: Grade-specific, evidence-based

## Emergency Protocols
- **Purpose**: Manage critical/complex pressure injuries
- **Target Population**: Grade 3+ pressure injuries, complications
- **Key Elements**: Immediate intervention, specialist consultation
- **Implementation**: STAT protocols, 24/7 availability

## Regulatory Protocols
- **Purpose**: Ensure compliance with healthcare regulations
- **Target Population**: All pressure injury cases requiring reporting
- **Key Elements**: Documentation, reporting, quality assurance
- **Implementation**: Mandatory, time-sensitive
"""
                
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=categories_doc
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
    """Main entry point for Vigia Medical Protocol MCP Server"""
    
    # Load configuration from environment
    config = ProtocolConfig(
        protocol_db_path=os.getenv("MEDICAL_PROTOCOL_DB", "./data/protocols.json")
    )
    
    # Create and run the server
    protocol_server = VigiaMedicalProtocolServer(config)
    
    # Run the server
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await protocol_server.server.run(
            read_stream,
            write_stream,
            protocol_server.server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())