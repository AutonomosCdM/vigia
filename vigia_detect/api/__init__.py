"""
Vigia MCP API - Serverless MCP Implementation
=============================================

Revolutionary serverless MCP architecture for medical systems.
Provides MCP Protocol compliance without Docker dependencies.

MCP Servers Available:
- Slack MCP Server: Medical alerts and Block Kit interfaces
- Twilio MCP Server: WhatsApp medical notifications  
- Supabase MCP Server: Medical data and audit trails
- Redis MCP Server: Medical protocol caching and search
- Gateway MCP Router: Coordinates multi-MCP medical workflows

Architecture:
- Each MCP server runs as FastAPI serverless endpoint
- HTTP/JSON-RPC transport (no Docker containers)
- Medical compliance built into each endpoint
- Independent fault tolerance per service

Usage:
from vigia_detect.api.mcp_gateway import ServerlessMCPGateway

gateway = ServerlessMCPGateway()
await gateway.medical_workflow(lpp_detection_data)
"""

from .mcp_gateway import ServerlessMCPGateway, create_mcp_gateway
from .mcp_slack import slack_server
from .mcp_twilio import twilio_server
from .mcp_supabase import supabase_server
from .mcp_redis import redis_server

__version__ = "1.0.0"
__author__ = "Vigia Medical Team"
__description__ = "Serverless MCP implementation for medical systems"

__all__ = [
    "ServerlessMCPGateway",
    "create_mcp_gateway",
    "slack_server",
    "twilio_server", 
    "supabase_server",
    "redis_server"
]