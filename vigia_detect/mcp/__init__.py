"""
Vigia MCP (Model Context Protocol) Integration Module
Hybrid architecture combining Docker Hub MCP services with custom medical MCP servers
"""

from .gateway import MCPGateway, MCPRouter
from .medical_server import VigiaMLPServer, LPPDetectionServer, FHIRIntegrationServer
from .client import MCPClient, MCPMedicalClient

__version__ = "1.0.0"
__author__ = "Vigia Medical Team"

__all__ = [
    "MCPGateway",
    "MCPRouter", 
    "VigiaMLPServer",
    "LPPDetectionServer",
    "FHIRIntegrationServer",
    "MCPClient",
    "MCPMedicalClient"
]