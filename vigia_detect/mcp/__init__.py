"""
Vigia MCP (Model Context Protocol) Integration Module
Hybrid architecture combining Docker Hub MCP services with custom medical MCP servers
"""

from .gateway import MCPGateway, MCPRouter
from .client import MCPClient, MCPMedicalClient
# from .medical_server import VigiaMLPServer, LPPDetectionServer, FHIRIntegrationServer  # Requires additional dependencies

__version__ = "1.0.0"
__author__ = "Vigia Medical Team"

__all__ = [
    "MCPGateway",
    "MCPRouter", 
    "MCPClient",
    "MCPMedicalClient"
    # "VigiaMLPServer",  # Requires additional dependencies
    # "LPPDetectionServer",  # Requires additional dependencies
    # "FHIRIntegrationServer"  # Requires additional dependencies
]