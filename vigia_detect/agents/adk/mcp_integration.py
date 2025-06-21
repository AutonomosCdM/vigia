"""
ADK-MCP Integration Layer
========================

Integration layer that connects Google ADK agents with MCP serverless tools.
Provides seamless integration between ADK workflows and MCP services.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from google.adk.agents import BaseAgent, AgentContext
from google.adk.core.types import AgentMessage, AgentResponse, AgentCapability
from google.adk.tools import Tool

from ...api.mcp_gateway import create_mcp_gateway, ServerlessMCPGateway
from ...utils.shared_utilities import VigiaLogger

logger = VigiaLogger.get_logger(__name__)


class MCPTool(Tool):
    """
    ADK Tool that interfaces with MCP services.
    
    Bridges the gap between ADK tool framework and MCP protocol.
    """
    
    def __init__(self, mcp_service: str, mcp_tool_name: str, gateway: ServerlessMCPGateway):
        """Initialize MCP Tool"""
        self.mcp_service = mcp_service
        self.mcp_tool_name = mcp_tool_name
        self.gateway = gateway
        
        super().__init__(
            name=f"mcp_{mcp_service}_{mcp_tool_name}",
            description=f"MCP tool for {mcp_service}: {mcp_tool_name}",
            parameters={}  # Will be dynamically populated
        )
    
    async def execute(self, context: AgentContext, **kwargs) -> Dict[str, Any]:
        """Execute MCP tool through gateway"""
        try:
            # Prepare MCP request
            mcp_request = {
                "name": self.mcp_tool_name,
                "arguments": kwargs,
                "medical_context": self._extract_medical_context(context)
            }
            
            # Call MCP service through gateway
            result = await self.gateway._call_single_mcp_service(self.mcp_service, mcp_request)
            
            logger.info(f"MCP tool executed: {self.name}")
            return result
            
        except Exception as e:
            logger.error(f"MCP tool execution failed: {self.name} - {e}")
            raise
    
    def _extract_medical_context(self, context: AgentContext) -> Dict[str, Any]:
        """Extract medical context from ADK context"""
        medical_context = {}
        
        # Extract from context data
        if hasattr(context, 'data') and context.data:
            medical_context.update({
                "patient_code": context.data.get("patient_code"),
                "lpp_grade": context.data.get("lpp_grade"),
                "confidence": context.data.get("confidence"),
                "location": context.data.get("location"),
                "severity": context.data.get("severity")
            })
        
        # Remove None values
        return {k: v for k, v in medical_context.items() if v is not None}


class MCPADKIntegration:
    """
    Integration service that connects ADK agents with MCP tools.
    
    Provides:
    - Automatic MCP tool registration for ADK agents
    - Medical workflow coordination between ADK and MCP
    - Context translation between ADK and MCP protocols
    """
    
    def __init__(self):
        """Initialize MCP-ADK integration"""
        self.gateway = None
        self.registered_tools = {}
        self.agent_mcp_mappings = {
            # Define which MCP tools each agent should have access to
            "ClinicalAssessmentAgent": ["supabase", "redis"],
            "CommunicationAgent": ["slack", "twilio"],
            "ProtocolAgent": ["redis", "supabase"],
            "ImageAnalysisAgent": ["supabase"],
            "WorkflowOrchestrationAgent": ["slack", "twilio", "supabase", "redis"]
        }
        
        logger.info("MCP-ADK Integration initialized")
    
    async def initialize_gateway(self) -> ServerlessMCPGateway:
        """Initialize MCP Gateway"""
        if not self.gateway:
            self.gateway = await create_mcp_gateway()
            await self.gateway.__aenter__()
        return self.gateway
    
    async def register_mcp_tools_for_agent(self, agent: BaseAgent) -> List[MCPTool]:
        """Register MCP tools for a specific ADK agent"""
        if not self.gateway:
            await self.initialize_gateway()
        
        agent_name = agent.__class__.__name__
        mcp_services = self.agent_mcp_mappings.get(agent_name, [])
        
        registered_tools = []
        
        for service_name in mcp_services:
            try:
                # Get available tools from MCP service
                tools_response = await self.gateway._call_single_mcp_service(
                    service_name, 
                    {"name": "list_tools", "arguments": {}}
                )
                
                # Register each tool as ADK MCPTool
                for tool_info in tools_response.get("tools", []):
                    mcp_tool = MCPTool(
                        mcp_service=service_name,
                        mcp_tool_name=tool_info["name"],
                        gateway=self.gateway
                    )
                    
                    # Update tool parameters from MCP schema
                    mcp_tool.parameters = tool_info.get("inputSchema", {})
                    mcp_tool.description = tool_info.get("description", mcp_tool.description)
                    
                    # Register with agent
                    agent.register_tool(mcp_tool)
                    registered_tools.append(mcp_tool)
                    
                    self.registered_tools[mcp_tool.name] = mcp_tool
                    
                    logger.info(f"Registered MCP tool for {agent_name}: {mcp_tool.name}")
                
            except Exception as e:
                logger.warning(f"Failed to register MCP tools from {service_name}: {e}")
        
        return registered_tools
    
    async def execute_medical_workflow(self, workflow_type: str, medical_data: Dict[str, Any], 
                                     notification_prefs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute medical workflow through MCP Gateway"""
        if not self.gateway:
            await self.initialize_gateway()
        
        # Prepare workflow request
        workflow_request = {
            "name": "orchestrate_medical_workflow",
            "arguments": {
                "workflow_type": workflow_type,
                "medical_data": medical_data,
                "notification_preferences": notification_prefs or {},
                "workflow_id": f"adk_{workflow_type}_{int(datetime.utcnow().timestamp())}"
            }
        }
        
        # Execute through gateway
        result = await self.gateway._call_tool(workflow_request)
        
        logger.info(f"Medical workflow executed: {workflow_type}")
        return result
    
    async def translate_adk_message_to_mcp(self, message: AgentMessage) -> Dict[str, Any]:
        """Translate ADK message to MCP request format"""
        return {
            "message_id": message.message_id,
            "sender_id": message.sender_id,
            "recipient_id": message.recipient_id,
            "content": message.content,
            "message_type": message.message_type,
            "timestamp": message.timestamp.isoformat() if message.timestamp else datetime.utcnow().isoformat(),
            "medical_context": self._extract_medical_context_from_message(message)
        }
    
    async def translate_mcp_response_to_adk(self, mcp_response: Dict[str, Any], 
                                          original_message: AgentMessage) -> AgentResponse:
        """Translate MCP response to ADK response format"""
        return AgentResponse(
            message_id=original_message.message_id,
            sender_id="mcp_gateway",
            recipient_id=original_message.sender_id,
            response_content=mcp_response,
            success=mcp_response.get("status") not in ["failed", "error"],
            timestamp=datetime.utcnow()
        )
    
    def _extract_medical_context_from_message(self, message: AgentMessage) -> Dict[str, Any]:
        """Extract medical context from ADK message"""
        content = message.content
        
        medical_context = {}
        
        if isinstance(content, dict):
            medical_context.update({
                "patient_code": content.get("patient_code"),
                "lpp_grade": content.get("lpp_grade"),
                "confidence": content.get("confidence"),
                "location": content.get("location"),
                "severity": content.get("severity"),
                "image_path": content.get("image_path")
            })
        
        # Remove None values
        return {k: v for k, v in medical_context.items() if v is not None}
    
    async def cleanup(self):
        """Cleanup MCP gateway connection"""
        if self.gateway:
            await self.gateway.__aexit__(None, None, None)
            self.gateway = None


# Global integration instance
mcp_adk_integration = MCPADKIntegration()


class MCPEnabledAgent:
    """
    Mixin class for ADK agents to enable MCP integration.
    
    Usage:
    class MyAgent(VigiaBaseAgent, MCPEnabledAgent):
        async def initialize(self):
            await self.setup_mcp_integration()
    """
    
    async def setup_mcp_integration(self):
        """Setup MCP integration for this agent"""
        global mcp_adk_integration
        
        try:
            # Register MCP tools for this agent
            mcp_tools = await mcp_adk_integration.register_mcp_tools_for_agent(self)
            
            logger.info(f"MCP integration setup complete: {len(mcp_tools)} tools registered")
            
            # Store reference to integration
            self._mcp_integration = mcp_adk_integration
            self._mcp_tools = mcp_tools
            
        except Exception as e:
            logger.error(f"Failed to setup MCP integration: {e}")
            # Continue without MCP - agent should still work
            self._mcp_integration = None
            self._mcp_tools = []
    
    async def execute_mcp_workflow(self, workflow_type: str, medical_data: Dict[str, Any],
                                 notification_prefs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute medical workflow through MCP"""
        if not self._mcp_integration:
            raise Exception("MCP integration not initialized")
        
        return await self._mcp_integration.execute_medical_workflow(
            workflow_type, medical_data, notification_prefs
        )
    
    async def send_mcp_notification(self, service: str, notification_type: str, 
                                  message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send notification through MCP service"""
        if not self._mcp_integration:
            raise Exception("MCP integration not initialized")
        
        # Find appropriate MCP tool
        tool_name = f"mcp_{service}_{notification_type}"
        mcp_tool = self._mcp_integration.registered_tools.get(tool_name)
        
        if not mcp_tool:
            raise Exception(f"MCP tool not found: {tool_name}")
        
        # Execute MCP tool
        return await mcp_tool.execute(None, **message_data)
    
    def get_available_mcp_tools(self) -> List[str]:
        """Get list of available MCP tools for this agent"""
        if not hasattr(self, '_mcp_tools'):
            return []
        
        return [tool.name for tool in self._mcp_tools]


# Utility functions for easy MCP integration

async def initialize_mcp_for_agent(agent: BaseAgent) -> List[MCPTool]:
    """Utility function to initialize MCP integration for any agent"""
    global mcp_adk_integration
    return await mcp_adk_integration.register_mcp_tools_for_agent(agent)


async def execute_medical_workflow_mcp(workflow_type: str, medical_data: Dict[str, Any],
                                     notification_prefs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Utility function to execute medical workflow through MCP"""
    global mcp_adk_integration
    return await mcp_adk_integration.execute_medical_workflow(workflow_type, medical_data, notification_prefs)


def create_mcp_enabled_agent(agent_class):
    """Decorator to automatically enable MCP integration for ADK agents"""
    
    class MCPEnabledAgentWrapper(agent_class, MCPEnabledAgent):
        
        async def initialize(self):
            # Call parent initialization if exists
            if hasattr(super(), 'initialize'):
                await super().initialize()
            
            # Setup MCP integration
            await self.setup_mcp_integration()
    
    return MCPEnabledAgentWrapper