"""
Base MCP Server for Serverless Implementation
=============================================

Provides foundation for all MCP servers with:
- HTTP/JSON-RPC transport
- Medical compliance features
- Error handling and logging
- Request/response validation
"""

import json
import time
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from abc import ABC, abstractmethod

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..utils.shared_utilities import VigiaLogger

logger = VigiaLogger.get_logger(__name__)


class MCPRequest(BaseModel):
    """Standardized MCP request format"""
    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    method: str = Field(..., description="MCP method to call")
    params: Dict[str, Any] = Field(default_factory=dict, description="Method parameters")
    id: Optional[Union[str, int]] = Field(default=None, description="Request ID")
    medical_context: Optional[Dict[str, Any]] = Field(default=None, description="Medical context for HIPAA compliance")


class MCPResponse(BaseModel):
    """Standardized MCP response format"""
    jsonrpc: str = Field(default="2.0")
    result: Optional[Any] = Field(default=None)
    error: Optional[Dict[str, Any]] = Field(default=None)
    id: Optional[Union[str, int]] = Field(default=None)
    medical_audit: Optional[Dict[str, Any]] = Field(default=None, description="Medical audit trail")


class MCPError(BaseModel):
    """MCP error format"""
    code: int
    message: str
    data: Optional[Any] = None


class BaseMCPServer(ABC):
    """
    Base class for all serverless MCP servers.
    
    Provides:
    - JSON-RPC 2.0 protocol handling
    - Medical compliance features
    - Audit trail generation
    - Error handling
    """
    
    def __init__(self, name: str, version: str = "1.0.0"):
        """Initialize MCP server"""
        self.name = name
        self.version = version
        self.app = FastAPI(
            title=f"Vigia {name} MCP Server",
            description=f"Serverless MCP implementation for {name}",
            version=version
        )
        
        # Register endpoints
        self._setup_routes()
        
        # Tool registry
        self.tools: Dict[str, Any] = {}
        self.resources: Dict[str, Any] = {}
        
        # Initialize medical compliance
        self._setup_medical_compliance()
        
        logger.info(f"Initialized {name} MCP Server v{version}")
    
    def _setup_routes(self):
        """Setup FastAPI routes for MCP"""
        
        @self.app.post("/mcp")
        async def handle_mcp_request(request: MCPRequest) -> MCPResponse:
            """Handle MCP JSON-RPC requests"""
            try:
                # Medical audit logging
                audit_data = self._create_audit_entry(request)
                
                # Route request to appropriate handler
                if request.method == "tools/list":
                    result = await self._list_tools()
                elif request.method == "tools/call":
                    result = await self._call_tool(request.params)
                elif request.method == "resources/list":
                    result = await self._list_resources()
                elif request.method == "resources/read":
                    result = await self._read_resource(request.params)
                else:
                    # Custom method handling
                    result = await self._handle_custom_method(request.method, request.params)
                
                response = MCPResponse(
                    result=result,
                    id=request.id,
                    medical_audit=audit_data
                )
                
                logger.info(f"MCP request {request.method} completed successfully")
                return response
                
            except Exception as e:
                logger.error(f"MCP request failed: {e}")
                error_response = MCPResponse(
                    error={
                        "code": -32603,
                        "message": str(e),
                        "data": {"timestamp": datetime.utcnow().isoformat()}
                    },
                    id=request.id
                )
                return error_response
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "server": self.name,
                "version": self.version,
                "timestamp": datetime.utcnow().isoformat(),
                "medical_compliance": "hipaa_ready"
            }
        
        @self.app.get("/mcp/capabilities")
        async def get_capabilities():
            """Get MCP server capabilities"""
            return {
                "tools": list(self.tools.keys()),
                "resources": list(self.resources.keys()),
                "transport": "http",
                "medical_features": ["hipaa_compliance", "audit_trail", "phi_protection"]
            }
    
    def _setup_medical_compliance(self):
        """Setup medical compliance features"""
        # HIPAA compliance settings
        self.medical_config = {
            "phi_protection": True,
            "audit_required": True,
            "encryption_required": True,
            "retention_days": 2555  # 7 years HIPAA requirement
        }
    
    def _create_audit_entry(self, request: MCPRequest) -> Dict[str, Any]:
        """Create medical audit trail entry"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "server": self.name,
            "method": request.method,
            "request_id": request.id,
            "medical_context": request.medical_context,
            "compliance_level": "hipaa",
            "phi_detected": self._detect_phi(request.params)
        }
    
    def _detect_phi(self, params: Dict[str, Any]) -> bool:
        """Detect if request contains PHI (Protected Health Information)"""
        phi_indicators = [
            "patient_id", "patient_name", "ssn", "medical_record",
            "birth_date", "phone", "email", "address"
        ]
        
        for key in params:
            if any(indicator in key.lower() for indicator in phi_indicators):
                return True
        return False
    
    @abstractmethod
    async def _list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        pass
    
    @abstractmethod
    async def _call_tool(self, params: Dict[str, Any]) -> Any:
        """Call a specific tool"""
        pass
    
    @abstractmethod
    async def _list_resources(self) -> Dict[str, Any]:
        """List available resources"""
        pass
    
    @abstractmethod
    async def _read_resource(self, params: Dict[str, Any]) -> Any:
        """Read a specific resource"""
        pass
    
    async def _handle_custom_method(self, method: str, params: Dict[str, Any]) -> Any:
        """Handle custom methods (override in subclasses)"""
        raise HTTPException(
            status_code=404,
            detail=f"Method '{method}' not implemented"
        )
    
    def register_tool(self, name: str, description: str, handler, parameters: Dict[str, Any]):
        """Register a new tool"""
        self.tools[name] = {
            "name": name,
            "description": description,
            "handler": handler,
            "parameters": parameters,
            "medical_safe": True
        }
        logger.info(f"Registered tool: {name}")
    
    def register_resource(self, uri: str, name: str, description: str, handler):
        """Register a new resource"""
        self.resources[uri] = {
            "uri": uri,
            "name": name,
            "description": description,
            "handler": handler,
            "medical_compliant": True
        }
        logger.info(f"Registered resource: {uri}")