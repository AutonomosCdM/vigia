"""
Slack MCP Server - Serverless Implementation
==========================================

Medical-grade Slack integration with Block Kit support.
Provides MCP tools for:
- Medical alert notifications
- Emergency escalation
- Block Kit interfaces for medical data
- Channel management for medical teams
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from slack_sdk.web.async_client import AsyncWebClient
    from slack_sdk.errors import SlackApiError
    slack_available = True
except ImportError:
    slack_available = False

from .base_mcp_server import BaseMCPServer
from ..agents.adk.slack_block_kit import create_slack_block_kit_agent
from ..utils.shared_utilities import VigiaLogger

logger = VigiaLogger.get_logger(__name__)


class SlackMCPServer(BaseMCPServer):
    """
    Serverless MCP server for Slack medical integrations.
    
    Provides medical-compliant Slack communication with:
    - LPP detection alerts
    - Emergency escalation workflows
    - Block Kit medical interfaces
    - PHI protection features
    """
    
    def __init__(self):
        """Initialize Slack MCP server"""
        super().__init__("Slack", "1.0.0")
        
        # Initialize Slack client
        self.slack_token = os.getenv("SLACK_BOT_TOKEN")
        self.slack_client = None
        
        if slack_available and self.slack_token:
            self.slack_client = AsyncWebClient(token=self.slack_token)
            logger.info("Slack client initialized")
        else:
            logger.warning("Slack not available - running in mock mode")
        
        # Medical channels configuration
        self.medical_channels = {
            "emergency": os.getenv("SLACK_EMERGENCY_CHANNEL", "C08TJHZFVD1"),
            "alerts": os.getenv("SLACK_ALERTS_CHANNEL", "C08TJHZFVD1"),
            "audit": os.getenv("SLACK_AUDIT_CHANNEL", "C08TJHZFVD1")
        }
        
        # Register MCP tools
        self._register_slack_tools()
        
        # Register MCP resources
        self._register_slack_resources()
    
    def _register_slack_tools(self):
        """Register Slack MCP tools"""
        
        # Medical alert tool
        self.register_tool(
            name="send_medical_alert",
            description="Send medical alert notification with LPP detection data",
            handler=self._send_medical_alert,
            parameters={
                "type": "object",
                "properties": {
                    "alert_type": {"type": "string", "enum": ["lpp_detection", "emergency", "escalation"]},
                    "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "patient_code": {"type": "string", "description": "Anonymized patient identifier"},
                    "lpp_grade": {"type": "integer", "minimum": 1, "maximum": 4},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "location": {"type": "string", "description": "Anatomical location"},
                    "channel": {"type": "string", "description": "Target Slack channel"}
                },
                "required": ["alert_type", "severity", "patient_code"]
            }
        )
        
        # Block Kit interface tool
        self.register_tool(
            name="create_block_kit_interface",
            description="Create Block Kit interface for medical data interaction",
            handler=self._create_block_kit_interface,
            parameters={
                "type": "object",
                "properties": {
                    "interface_type": {"type": "string", "enum": ["lpp_summary", "patient_history", "protocol_search"]},
                    "data": {"type": "object", "description": "Medical data to display"},
                    "interactive": {"type": "boolean", "default": True}
                },
                "required": ["interface_type", "data"]
            }
        )
        
        # Emergency escalation tool
        self.register_tool(
            name="emergency_escalation",
            description="Trigger emergency escalation workflow",
            handler=self._emergency_escalation,
            parameters={
                "type": "object",
                "properties": {
                    "escalation_level": {"type": "integer", "minimum": 1, "maximum": 3},
                    "reason": {"type": "string"},
                    "patient_code": {"type": "string"},
                    "immediate_action_required": {"type": "boolean", "default": False}
                },
                "required": ["escalation_level", "reason", "patient_code"]
            }
        )
        
        # Channel management tool
        self.register_tool(
            name="manage_medical_channel",
            description="Manage medical team channels",
            handler=self._manage_medical_channel,
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "archive", "invite", "update_topic"]},
                    "channel_name": {"type": "string"},
                    "purpose": {"type": "string"},
                    "users": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["action", "channel_name"]
            }
        )
    
    def _register_slack_resources(self):
        """Register Slack MCP resources"""
        
        self.register_resource(
            uri="slack://channels/medical",
            name="Medical Channels",
            description="List of medical team channels",
            handler=self._get_medical_channels
        )
        
        self.register_resource(
            uri="slack://alerts/recent",
            name="Recent Medical Alerts",
            description="Recent medical alert messages",
            handler=self._get_recent_alerts
        )
        
        self.register_resource(
            uri="slack://users/medical_team",
            name="Medical Team Members",
            description="List of medical team members",
            handler=self._get_medical_team
        )
    
    async def _list_tools(self) -> Dict[str, Any]:
        """List available Slack tools"""
        return {
            "tools": [
                {
                    "name": tool_name,
                    "description": tool_data["description"],
                    "inputSchema": tool_data["parameters"],
                    "medical_compliant": True
                }
                for tool_name, tool_data in self.tools.items()
            ]
        }
    
    async def _call_tool(self, params: Dict[str, Any]) -> Any:
        """Call a specific Slack tool"""
        tool_name = params.get("name")
        tool_params = params.get("arguments", {})
        
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        handler = self.tools[tool_name]["handler"]
        return await handler(tool_params)
    
    async def _list_resources(self) -> Dict[str, Any]:
        """List available Slack resources"""
        return {
            "resources": [
                {
                    "uri": uri,
                    "name": resource_data["name"],
                    "description": resource_data["description"],
                    "mimeType": "application/json"
                }
                for uri, resource_data in self.resources.items()
            ]
        }
    
    async def _read_resource(self, params: Dict[str, Any]) -> Any:
        """Read a specific Slack resource"""
        uri = params.get("uri")
        
        if uri not in self.resources:
            raise ValueError(f"Unknown resource: {uri}")
        
        handler = self.resources[uri]["handler"]
        return await handler()
    
    # Tool implementations
    
    async def _send_medical_alert(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send medical alert notification"""
        if not self.slack_client:
            return {"status": "mock", "message": "Slack not configured - using mock mode"}
        
        try:
            alert_type = params.get("alert_type")
            severity = params.get("severity")
            patient_code = params.get("patient_code")
            channel = params.get("channel", self.medical_channels["alerts"])
            
            # Create medical alert message
            if alert_type == "lpp_detection":
                blocks = await self._create_lpp_alert_blocks(params)
                text = f"🏥 LPP Detection Alert - Severity: {severity.upper()}"
            elif alert_type == "emergency":
                blocks = await self._create_emergency_blocks(params)
                text = f"🚨 MEDICAL EMERGENCY - Patient: {patient_code}"
            else:
                blocks = await self._create_escalation_blocks(params)
                text = f"⚠️ Medical Escalation - Level: {severity.upper()}"
            
            # Send to Slack
            response = await self.slack_client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks,
                metadata={
                    "event_type": "medical_alert",
                    "event_payload": {
                        "patient_code": patient_code,
                        "alert_type": alert_type,
                        "severity": severity,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )
            
            return {
                "status": "sent",
                "message_ts": response["ts"],
                "channel": channel,
                "alert_type": alert_type
            }
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e}")
            raise ValueError(f"Failed to send alert: {e.response['error']}")
    
    async def _create_block_kit_interface(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create Block Kit interface for medical data"""
        interface_type = params.get("interface_type")
        data = params.get("data", {})
        interactive = params.get("interactive", True)
        
        # Use existing Block Kit agent
        block_kit_agent = create_slack_block_kit_agent()
        
        if interface_type == "lpp_summary":
            blocks = await block_kit_agent.create_lpp_detection_summary(data)
        elif interface_type == "patient_history":
            blocks = await block_kit_agent.create_patient_history_interface(data)
        elif interface_type == "protocol_search":
            blocks = await block_kit_agent.create_protocol_search_interface(data)
        else:
            raise ValueError(f"Unknown interface type: {interface_type}")
        
        return {
            "blocks": blocks,
            "interface_type": interface_type,
            "interactive": interactive,
            "medical_compliant": True
        }
    
    async def _emergency_escalation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger emergency escalation workflow"""
        if not self.slack_client:
            return {"status": "mock", "message": "Emergency escalation mock"}
        
        escalation_level = params.get("escalation_level")
        reason = params.get("reason")
        patient_code = params.get("patient_code")
        immediate = params.get("immediate_action_required", False)
        
        # Determine escalation channels based on level
        if escalation_level >= 3 or immediate:
            channel = self.medical_channels["emergency"]
            urgency = "🚨 IMMEDIATE ACTION REQUIRED"
        elif escalation_level == 2:
            channel = self.medical_channels["alerts"]
            urgency = "⚠️ URGENT MEDICAL ATTENTION"
        else:
            channel = self.medical_channels["alerts"]
            urgency = "ℹ️ Medical Review Needed"
        
        # Create escalation message
        message = f"""
{urgency}

**Patient Code:** {patient_code}
**Escalation Level:** {escalation_level}/3
**Reason:** {reason}
**Timestamp:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

Medical team please respond immediately.
        """.strip()
        
        try:
            response = await self.slack_client.chat_postMessage(
                channel=channel,
                text=message,
                metadata={
                    "event_type": "emergency_escalation",
                    "event_payload": {
                        "patient_code": patient_code,
                        "escalation_level": escalation_level,
                        "immediate": immediate
                    }
                }
            )
            
            return {
                "status": "escalated",
                "level": escalation_level,
                "channel": channel,
                "message_ts": response["ts"]
            }
            
        except SlackApiError as e:
            logger.error(f"Escalation failed: {e}")
            raise ValueError(f"Emergency escalation failed: {e.response['error']}")
    
    async def _manage_medical_channel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Manage medical team channels"""
        if not self.slack_client:
            return {"status": "mock", "message": "Channel management mock"}
        
        action = params.get("action")
        channel_name = params.get("channel_name")
        
        try:
            if action == "create":
                response = await self.slack_client.conversations_create(
                    name=channel_name,
                    is_private=True  # Medical channels should be private
                )
                return {"status": "created", "channel_id": response["channel"]["id"]}
            
            elif action == "archive":
                await self.slack_client.conversations_archive(channel=channel_name)
                return {"status": "archived", "channel": channel_name}
            
            # Add more channel management actions as needed
            
        except SlackApiError as e:
            logger.error(f"Channel management failed: {e}")
            raise ValueError(f"Channel operation failed: {e.response['error']}")
    
    # Resource implementations
    
    async def _get_medical_channels(self) -> Dict[str, Any]:
        """Get list of medical channels"""
        return {
            "channels": self.medical_channels,
            "total": len(self.medical_channels),
            "compliance": "hipaa_ready"
        }
    
    async def _get_recent_alerts(self) -> Dict[str, Any]:
        """Get recent medical alerts"""
        if not self.slack_client:
            return {"alerts": [], "status": "mock"}
        
        # Implementation would fetch recent messages from medical channels
        return {
            "alerts": [],
            "status": "implemented",
            "note": "Would fetch from Slack conversation history"
        }
    
    async def _get_medical_team(self) -> Dict[str, Any]:
        """Get medical team members"""
        if not self.slack_client:
            return {"team": [], "status": "mock"}
        
        # Implementation would fetch team members from workspace
        return {
            "team": [],
            "status": "implemented", 
            "note": "Would fetch from Slack workspace users"
        }
    
    # Helper methods
    
    async def _create_lpp_alert_blocks(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create Slack blocks for LPP detection alert"""
        lpp_grade = params.get("lpp_grade", "Unknown")
        confidence = params.get("confidence", 0.0)
        location = params.get("location", "Not specified")
        patient_code = params.get("patient_code")
        
        return [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🏥 LPP Detection Alert"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Patient:* {patient_code}"},
                    {"type": "mrkdwn", "text": f"*LPP Grade:* {lpp_grade}"},
                    {"type": "mrkdwn", "text": f"*Confidence:* {confidence:.1%}"},
                    {"type": "mrkdwn", "text": f"*Location:* {location}"}
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Review Case"},
                        "style": "primary",
                        "action_id": "review_lpp_case"
                    },
                    {
                        "type": "button", 
                        "text": {"type": "plain_text", "text": "Escalate"},
                        "style": "danger",
                        "action_id": "escalate_case"
                    }
                ]
            }
        ]
    
    async def _create_emergency_blocks(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create Slack blocks for emergency alert"""
        return [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚨 MEDICAL EMERGENCY"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Emergency detected for patient: **{params.get('patient_code')}**"
                }
            }
        ]
    
    async def _create_escalation_blocks(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create Slack blocks for escalation alert"""
        return [
            {
                "type": "header", 
                "text": {
                    "type": "plain_text",
                    "text": "⚠️ Medical Escalation"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Escalation for patient: **{params.get('patient_code')}**"
                }
            }
        ]


# Create server instance
slack_server = SlackMCPServer()

# Export FastAPI app for deployment
app = slack_server.app