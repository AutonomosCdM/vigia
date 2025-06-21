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

# Optional imports for deployment compatibility
try:
    from .mcp_gateway import ServerlessMCPGateway, create_mcp_gateway
    mcp_gateway_available = True
except ImportError as e:
    print(f"Warning: MCP Gateway not available: {e}")
    mcp_gateway_available = False

try:
    from .mcp_slack import slack_server
    mcp_slack_available = True
except ImportError as e:
    print(f"Warning: MCP Slack not available: {e}")
    mcp_slack_available = False

try:
    from .mcp_twilio import twilio_server
    mcp_twilio_available = True
except ImportError as e:
    print(f"Warning: MCP Twilio not available: {e}")
    mcp_twilio_available = False

try:
    from .mcp_supabase import supabase_server
    mcp_supabase_available = True
except ImportError as e:
    print(f"Warning: MCP Supabase not available: {e}")
    mcp_supabase_available = False

try:
    from .mcp_redis import redis_server
    mcp_redis_available = True
except ImportError as e:
    print(f"Warning: MCP Redis not available: {e}")
    mcp_redis_available = False

__version__ = "1.0.0"
__author__ = "Vigia Medical Team"
__description__ = "Serverless MCP implementation for medical systems"

# Dynamic __all__ based on available imports
__all__ = []

if mcp_gateway_available:
    __all__.extend(["ServerlessMCPGateway", "create_mcp_gateway"])
if mcp_slack_available:
    __all__.append("slack_server")
if mcp_twilio_available:
    __all__.append("twilio_server")
if mcp_supabase_available:
    __all__.append("supabase_server")
if mcp_redis_available:
    __all__.append("redis_server")