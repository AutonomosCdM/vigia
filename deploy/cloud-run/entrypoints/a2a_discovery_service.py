#!/usr/bin/env python3
"""
A2A Discovery Service Cloud Run Entrypoint
==========================================
Agent discovery and registry service for ADK A2A communication.
"""

import os
import logging
import asyncio
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException
import uvicorn
import redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import A2A discovery components
from vigia_detect.a2a.adk.agent_cards import AgentCard
from vigia_detect.a2a.agent_discovery_service import AgentDiscoveryService

# Initialize FastAPI app
app = FastAPI(
    title="Vigia A2A Discovery Service",
    description="Agent Discovery and Registry for ADK A2A Communication",
    version="1.0.0"
)

# Global discovery service instance
discovery_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize the A2A Discovery Service on startup."""
    global discovery_service
    try:
        logger.info("Initializing A2A Discovery Service...")
        discovery_service = AgentDiscoveryService()
        logger.info("A2A Discovery Service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize A2A Discovery Service: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service_type": "a2a_discovery",
        "version": "1.0.0"
    }

@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    if discovery_service is None:
        raise HTTPException(status_code=503, detail="Discovery service not initialized")
    return {
        "status": "ready",
        "service_type": "a2a_discovery",
        "capabilities": ["agent_registration", "agent_discovery", "health_monitoring"]
    }

@app.post("/agents/register")
async def register_agent(agent_card: Dict[str, Any]):
    """Register an agent in the discovery service."""
    if discovery_service is None:
        raise HTTPException(status_code=503, detail="Discovery service not initialized")
    
    try:
        # Convert to AgentCard object
        card = AgentCard(
            agent_id=agent_card.get("agent_id"),
            agent_name=agent_card.get("agent_name"),
            agent_type=agent_card.get("agent_type"),
            capabilities=agent_card.get("capabilities", []),
            endpoint_url=agent_card.get("endpoint_url"),
            health_check_url=agent_card.get("health_check_url"),
            metadata=agent_card.get("metadata", {})
        )
        
        result = await discovery_service.register_agent(card)
        
        return {
            "registered": True,
            "agent_id": card.agent_id,
            "registration_id": result.get("registration_id"),
            "timestamp": "2025-01-20T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Agent registration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/discover")
async def discover_agents(agent_type: str = None, capability: str = None):
    """Discover available agents."""
    if discovery_service is None:
        raise HTTPException(status_code=503, detail="Discovery service not initialized")
    
    try:
        filters = {}
        if agent_type:
            filters["agent_type"] = agent_type
        if capability:
            filters["capability"] = capability
        
        agents = await discovery_service.discover_agents(filters)
        
        return {
            "agents": [agent.to_dict() for agent in agents],
            "total_count": len(agents),
            "filters_applied": filters,
            "timestamp": "2025-01-20T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Agent discovery failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/{agent_id}")
async def get_agent_info(agent_id: str):
    """Get information about a specific agent."""
    if discovery_service is None:
        raise HTTPException(status_code=503, detail="Discovery service not initialized")
    
    try:
        agent = await discovery_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return agent.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Agent info retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/agents/{agent_id}")
async def unregister_agent(agent_id: str):
    """Unregister an agent from the discovery service."""
    if discovery_service is None:
        raise HTTPException(status_code=503, detail="Discovery service not initialized")
    
    try:
        result = await discovery_service.unregister_agent(agent_id)
        
        return {
            "unregistered": result,
            "agent_id": agent_id,
            "timestamp": "2025-01-20T00:00:00Z"
        }
        
    except Exception as e:
        logger.error(f"Agent unregistration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/{agent_id}/health")
async def check_agent_health(agent_id: str):
    """Check the health of a specific agent."""
    if discovery_service is None:
        raise HTTPException(status_code=503, detail="Discovery service not initialized")
    
    try:
        health_status = await discovery_service.check_agent_health(agent_id)
        return health_status
        
    except Exception as e:
        logger.error(f"Agent health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/network/topology")
async def get_network_topology():
    """Get the current A2A network topology."""
    if discovery_service is None:
        raise HTTPException(status_code=503, detail="Discovery service not initialized")
    
    try:
        topology = await discovery_service.get_network_topology()
        return topology
        
    except Exception as e:
        logger.error(f"Network topology retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_discovery_metrics():
    """Get discovery service metrics."""
    if discovery_service is None:
        raise HTTPException(status_code=503, detail="Discovery service not initialized")
    
    try:
        metrics = await discovery_service.get_metrics()
        return metrics
        
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)