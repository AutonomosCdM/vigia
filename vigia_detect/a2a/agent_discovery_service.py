"""
Agent Discovery Service - Distributed Agent Registration and Discovery
=====================================================================

Servicio distribuido para descubrimiento automático de agentes médicos
especializados con capacidades de load balancing y health monitoring.

Features:
- Automatic agent registration and discovery
- Capability-based agent matching
- Health monitoring and failover
- Load balancing across agent instances
- Service mesh integration
- Medical compliance tracking
"""

import asyncio
import json
import time
import logging
import hashlib
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict
import aiohttp
from aiohttp import web
import aioredis
import consul
from kazoo.client import KazooClient

from .protocol_layer import A2AMessage, A2AProtocolLayer, MessagePriority, AuthLevel
from ..utils.secure_logger import SecureLogger
from ..utils.audit_service import AuditService, AuditEventType

logger = SecureLogger("agent_discovery_service")


class AgentType(Enum):
    """Types of specialized medical agents"""
    IMAGE_ANALYSIS = "image_analysis"
    CLINICAL_ASSESSMENT = "clinical_assessment"
    PROTOCOL_CONSULTANT = "protocol_consultant"
    COMMUNICATION = "communication"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"
    MASTER_ORCHESTRATOR = "master_orchestrator"


class AgentStatus(Enum):
    """Agent health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNREACHABLE = "unreachable"
    MAINTENANCE = "maintenance"


class ServiceBackend(Enum):
    """Service discovery backends"""
    REDIS = "redis"
    CONSUL = "consul"
    ZOOKEEPER = "zookeeper"
    MEMORY = "memory"  # For testing


@dataclass
class AgentCapability:
    """Describes agent capability"""
    name: str
    version: str
    max_concurrent: int = 10
    avg_response_time: float = 0.0
    success_rate: float = 1.0
    medical_compliance: bool = True
    requires_phi_access: bool = False


@dataclass
class AgentRegistration:
    """Agent registration information"""
    agent_id: str
    agent_type: AgentType
    endpoint: str
    capabilities: List[AgentCapability]
    status: AgentStatus = AgentStatus.HEALTHY
    metadata: Optional[Dict[str, Any]] = None
    
    # Health metrics
    last_heartbeat: Optional[datetime] = None
    load_factor: float = 0.0  # 0.0 = no load, 1.0 = full capacity
    current_connections: int = 0
    total_requests: int = 0
    error_rate: float = 0.0
    
    # Medical compliance
    hipaa_compliant: bool = True
    audit_enabled: bool = True
    encryption_enabled: bool = True
    
    def __post_init__(self):
        if self.last_heartbeat is None:
            self.last_heartbeat = datetime.now(timezone.utc)
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ServiceQuery:
    """Query for finding suitable agents"""
    agent_type: Optional[AgentType] = None
    capability_name: Optional[str] = None
    min_success_rate: float = 0.8
    max_load_factor: float = 0.8
    requires_phi_access: Optional[bool] = None
    medical_compliant_only: bool = True
    preferred_agents: Optional[List[str]] = None
    exclude_agents: Optional[List[str]] = None


class AgentDiscoveryService:
    """
    Distributed agent discovery service with health monitoring
    and load balancing capabilities
    """
    
    def __init__(self, 
                 service_id: str = "vigia_discovery",
                 backend: ServiceBackend = ServiceBackend.REDIS,
                 redis_url: str = "redis://localhost:6379",
                 consul_host: str = "localhost",
                 consul_port: int = 8500,
                 zk_hosts: str = "localhost:2181"):
        
        self.service_id = service_id
        self.backend = backend
        
        # Storage backends
        self.redis_client: Optional[aioredis.Redis] = None
        self.consul_client: Optional[consul.Consul] = None
        self.zk_client: Optional[KazooClient] = None
        
        # In-memory storage (fallback/testing)
        self.memory_registry: Dict[str, AgentRegistration] = {}
        
        # Configuration
        self.redis_url = redis_url
        self.consul_host = consul_host
        self.consul_port = consul_port
        self.zk_hosts = zk_hosts
        
        # Health monitoring
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 90   # seconds
        self.health_check_interval = 60  # seconds
        
        # Statistics
        self.stats = {
            "total_agents": 0,
            "healthy_agents": 0,
            "total_queries": 0,
            "successful_discoveries": 0,
            "failed_discoveries": 0
        }
        
        # Background tasks
        self.background_tasks: Set[asyncio.Task] = set()
        
        # Audit service
        self.audit_service = AuditService()
        
        logger.info(f"Agent Discovery Service initialized with backend: {backend.value}")
    
    async def initialize(self):
        """Initialize service discovery backend"""
        try:
            if self.backend == ServiceBackend.REDIS:
                await self._init_redis()
            elif self.backend == ServiceBackend.CONSUL:
                await self._init_consul()
            elif self.backend == ServiceBackend.ZOOKEEPER:
                await self._init_zookeeper()
            elif self.backend == ServiceBackend.MEMORY:
                logger.info("Using in-memory backend for testing")
            
            # Start background tasks
            await self._start_background_tasks()
            
            logger.info("Agent Discovery Service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize discovery service: {e}")
            raise
    
    async def _init_redis(self):
        """Initialize Redis backend"""
        self.redis_client = aioredis.from_url(self.redis_url)
        await self.redis_client.ping()
        logger.info("Redis backend initialized")
    
    async def _init_consul(self):
        """Initialize Consul backend"""
        self.consul_client = consul.Consul(
            host=self.consul_host,
            port=self.consul_port
        )
        # Test connection
        self.consul_client.agent.self()
        logger.info("Consul backend initialized")
    
    async def _init_zookeeper(self):
        """Initialize ZooKeeper backend"""
        self.zk_client = KazooClient(hosts=self.zk_hosts)
        self.zk_client.start()
        logger.info("ZooKeeper backend initialized")
    
    async def _start_background_tasks(self):
        """Start background monitoring tasks"""
        # Health monitoring task
        health_task = asyncio.create_task(self._health_monitor_loop())
        self.background_tasks.add(health_task)
        health_task.add_done_callback(self.background_tasks.discard)
        
        # Statistics update task
        stats_task = asyncio.create_task(self._stats_update_loop())
        self.background_tasks.add(stats_task)
        stats_task.add_done_callback(self.background_tasks.discard)
        
        logger.info("Background monitoring tasks started")
    
    async def register_agent(self, registration: AgentRegistration) -> bool:
        """Register new agent in discovery service"""
        try:
            # Validate registration
            if not self._validate_registration(registration):
                return False
            
            # Store in backend
            await self._store_registration(registration)
            
            # Update statistics
            self.stats["total_agents"] += 1
            if registration.status == AgentStatus.HEALTHY:
                self.stats["healthy_agents"] += 1
            
            # Audit log
            await self.audit_service.log_event(
                AuditEventType.AGENT_REGISTERED,
                {
                    "agent_id": registration.agent_id,
                    "agent_type": registration.agent_type.value,
                    "endpoint": registration.endpoint,
                    "capabilities": [cap.name for cap in registration.capabilities]
                },
                session_id=f"discovery_{self.service_id}"
            )
            
            logger.info(f"Agent registered: {registration.agent_id} ({registration.agent_type.value})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent {registration.agent_id}: {e}")
            return False
    
    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister agent from discovery service"""
        try:
            # Remove from backend
            await self._remove_registration(agent_id)
            
            # Update statistics
            self.stats["total_agents"] = max(0, self.stats["total_agents"] - 1)
            
            # Audit log
            await self.audit_service.log_event(
                AuditEventType.AGENT_UNREGISTERED,
                {"agent_id": agent_id},
                session_id=f"discovery_{self.service_id}"
            )
            
            logger.info(f"Agent unregistered: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False
    
    async def discover_agents(self, query: ServiceQuery) -> List[AgentRegistration]:
        """Discover agents matching query criteria"""
        try:
            self.stats["total_queries"] += 1
            
            # Get all registrations
            all_agents = await self._get_all_registrations()
            
            # Filter by query criteria
            matching_agents = self._filter_agents(all_agents, query)
            
            # Sort by suitability (load, response time, success rate)
            sorted_agents = self._sort_by_suitability(matching_agents)
            
            if sorted_agents:
                self.stats["successful_discoveries"] += 1
            else:
                self.stats["failed_discoveries"] += 1
            
            logger.info(f"Discovery query returned {len(sorted_agents)} agents")
            return sorted_agents
            
        except Exception as e:
            logger.error(f"Agent discovery failed: {e}")
            self.stats["failed_discoveries"] += 1
            return []
    
    async def get_best_agent(self, query: ServiceQuery) -> Optional[AgentRegistration]:
        """Get single best agent for query"""
        agents = await self.discover_agents(query)
        return agents[0] if agents else None
    
    async def update_agent_health(self, agent_id: str, 
                                 status: AgentStatus,
                                 metrics: Optional[Dict[str, Any]] = None) -> bool:
        """Update agent health status and metrics"""
        try:
            registration = await self._get_registration(agent_id)
            if not registration:
                return False
            
            # Update status and metrics
            old_status = registration.status
            registration.status = status
            registration.last_heartbeat = datetime.now(timezone.utc)
            
            if metrics:
                registration.load_factor = metrics.get("load_factor", registration.load_factor)
                registration.current_connections = metrics.get("current_connections", registration.current_connections)
                registration.error_rate = metrics.get("error_rate", registration.error_rate)
                
                # Update capability metrics
                for capability in registration.capabilities:
                    cap_metrics = metrics.get(f"capability_{capability.name}", {})
                    capability.avg_response_time = cap_metrics.get("avg_response_time", capability.avg_response_time)
                    capability.success_rate = cap_metrics.get("success_rate", capability.success_rate)
            
            # Store updated registration
            await self._store_registration(registration)
            
            # Update statistics if status changed
            if old_status != status:
                if status == AgentStatus.HEALTHY and old_status != AgentStatus.HEALTHY:
                    self.stats["healthy_agents"] += 1
                elif status != AgentStatus.HEALTHY and old_status == AgentStatus.HEALTHY:
                    self.stats["healthy_agents"] = max(0, self.stats["healthy_agents"] - 1)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update agent health for {agent_id}: {e}")
            return False
    
    async def get_agent_status(self, agent_id: str) -> Optional[AgentRegistration]:
        """Get current agent registration and status"""
        return await self._get_registration(agent_id)
    
    async def list_agents(self, agent_type: Optional[AgentType] = None) -> List[AgentRegistration]:
        """List all registered agents, optionally filtered by type"""
        all_agents = await self._get_all_registrations()
        
        if agent_type:
            return [agent for agent in all_agents if agent.agent_type == agent_type]
        
        return all_agents
    
    def _validate_registration(self, registration: AgentRegistration) -> bool:
        """Validate agent registration data"""
        if not registration.agent_id or not registration.endpoint:
            logger.error("Invalid registration: missing agent_id or endpoint")
            return False
        
        if not registration.capabilities:
            logger.error("Invalid registration: no capabilities specified")
            return False
        
        # Validate medical compliance requirements
        if any(cap.requires_phi_access for cap in registration.capabilities):
            if not registration.hipaa_compliant or not registration.encryption_enabled:
                logger.error("Invalid registration: PHI access requires HIPAA compliance and encryption")
                return False
        
        return True
    
    def _filter_agents(self, agents: List[AgentRegistration], query: ServiceQuery) -> List[AgentRegistration]:
        """Filter agents based on query criteria"""
        filtered = []
        
        for agent in agents:
            # Skip unhealthy agents
            if agent.status not in [AgentStatus.HEALTHY, AgentStatus.DEGRADED]:
                continue
            
            # Filter by agent type
            if query.agent_type and agent.agent_type != query.agent_type:
                continue
            
            # Filter by capability
            if query.capability_name:
                if not any(cap.name == query.capability_name for cap in agent.capabilities):
                    continue
            
            # Filter by success rate
            if query.capability_name:
                capability = next((cap for cap in agent.capabilities if cap.name == query.capability_name), None)
                if capability and capability.success_rate < query.min_success_rate:
                    continue
            
            # Filter by load factor
            if agent.load_factor > query.max_load_factor:
                continue
            
            # Filter by PHI access requirements
            if query.requires_phi_access is not None:
                has_phi_capability = any(cap.requires_phi_access for cap in agent.capabilities)
                if query.requires_phi_access and not has_phi_capability:
                    continue
                if not query.requires_phi_access and has_phi_capability:
                    continue
            
            # Filter by medical compliance
            if query.medical_compliant_only and not agent.hipaa_compliant:
                continue
            
            # Handle preferred agents
            if query.preferred_agents and agent.agent_id in query.preferred_agents:
                filtered.insert(0, agent)  # Prioritize preferred agents
                continue
            
            # Handle excluded agents
            if query.exclude_agents and agent.agent_id in query.exclude_agents:
                continue
            
            filtered.append(agent)
        
        return filtered
    
    def _sort_by_suitability(self, agents: List[AgentRegistration]) -> List[AgentRegistration]:
        """Sort agents by suitability score (lower is better)"""
        def suitability_score(agent: AgentRegistration) -> float:
            # Calculate composite score (lower is better)
            load_penalty = agent.load_factor * 100
            error_penalty = agent.error_rate * 50
            
            # Response time penalty (average across capabilities)
            avg_response_time = sum(cap.avg_response_time for cap in agent.capabilities) / len(agent.capabilities)
            response_penalty = avg_response_time
            
            # Health status penalty
            status_penalty = 0
            if agent.status == AgentStatus.DEGRADED:
                status_penalty = 25
            elif agent.status == AgentStatus.UNHEALTHY:
                status_penalty = 100
            
            return load_penalty + error_penalty + response_penalty + status_penalty
        
        return sorted(agents, key=suitability_score)
    
    async def _health_monitor_loop(self):
        """Background health monitoring loop"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_checks()
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
    
    async def _perform_health_checks(self):
        """Perform health checks on all registered agents"""
        all_agents = await self._get_all_registrations()
        current_time = datetime.now(timezone.utc)
        
        for agent in all_agents:
            # Check heartbeat timeout
            if agent.last_heartbeat:
                time_since_heartbeat = (current_time - agent.last_heartbeat).total_seconds()
                
                if time_since_heartbeat > self.heartbeat_timeout:
                    if agent.status in [AgentStatus.HEALTHY, AgentStatus.DEGRADED]:
                        logger.warning(f"Agent {agent.agent_id} missed heartbeat, marking as unreachable")
                        await self.update_agent_health(agent.agent_id, AgentStatus.UNREACHABLE)
            
            # Perform active health check
            if agent.status != AgentStatus.UNREACHABLE:
                is_healthy = await self._ping_agent(agent)
                if not is_healthy and agent.status == AgentStatus.HEALTHY:
                    logger.warning(f"Agent {agent.agent_id} failed health check, marking as unhealthy")
                    await self.update_agent_health(agent.agent_id, AgentStatus.UNHEALTHY)
                elif is_healthy and agent.status == AgentStatus.UNHEALTHY:
                    logger.info(f"Agent {agent.agent_id} recovered, marking as healthy")
                    await self.update_agent_health(agent.agent_id, AgentStatus.HEALTHY)
    
    async def _ping_agent(self, agent: AgentRegistration) -> bool:
        """Ping agent to check if it's responsive"""
        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{agent.endpoint}/a2a/health") as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def _stats_update_loop(self):
        """Background statistics update loop"""
        while True:
            try:
                await asyncio.sleep(60)  # Update every minute
                await self._update_statistics()
            except Exception as e:
                logger.error(f"Stats update error: {e}")
    
    async def _update_statistics(self):
        """Update service statistics"""
        all_agents = await self._get_all_registrations()
        
        self.stats["total_agents"] = len(all_agents)
        self.stats["healthy_agents"] = len([
            agent for agent in all_agents 
            if agent.status == AgentStatus.HEALTHY
        ])
    
    # Backend-specific methods
    async def _store_registration(self, registration: AgentRegistration):
        """Store agent registration in backend"""
        if self.backend == ServiceBackend.REDIS:
            await self._redis_store(registration)
        elif self.backend == ServiceBackend.CONSUL:
            await self._consul_store(registration)
        elif self.backend == ServiceBackend.ZOOKEEPER:
            await self._zk_store(registration)
        else:  # MEMORY
            self.memory_registry[registration.agent_id] = registration
    
    async def _get_registration(self, agent_id: str) -> Optional[AgentRegistration]:
        """Get agent registration from backend"""
        if self.backend == ServiceBackend.REDIS:
            return await self._redis_get(agent_id)
        elif self.backend == ServiceBackend.CONSUL:
            return await self._consul_get(agent_id)
        elif self.backend == ServiceBackend.ZOOKEEPER:
            return await self._zk_get(agent_id)
        else:  # MEMORY
            return self.memory_registry.get(agent_id)
    
    async def _get_all_registrations(self) -> List[AgentRegistration]:
        """Get all agent registrations from backend"""
        if self.backend == ServiceBackend.REDIS:
            return await self._redis_get_all()
        elif self.backend == ServiceBackend.CONSUL:
            return await self._consul_get_all()
        elif self.backend == ServiceBackend.ZOOKEEPER:
            return await self._zk_get_all()
        else:  # MEMORY
            return list(self.memory_registry.values())
    
    async def _remove_registration(self, agent_id: str):
        """Remove agent registration from backend"""
        if self.backend == ServiceBackend.REDIS:
            await self._redis_remove(agent_id)
        elif self.backend == ServiceBackend.CONSUL:
            await self._consul_remove(agent_id)
        elif self.backend == ServiceBackend.ZOOKEEPER:
            await self._zk_remove(agent_id)
        else:  # MEMORY
            self.memory_registry.pop(agent_id, None)
    
    # Redis backend methods
    async def _redis_store(self, registration: AgentRegistration):
        """Store registration in Redis"""
        key = f"agent_registry:{registration.agent_id}"
        data = json.dumps(asdict(registration), default=str)
        await self.redis_client.set(key, data)
        await self.redis_client.expire(key, self.heartbeat_timeout * 2)
    
    async def _redis_get(self, agent_id: str) -> Optional[AgentRegistration]:
        """Get registration from Redis"""
        key = f"agent_registry:{agent_id}"
        data = await self.redis_client.get(key)
        if data:
            reg_dict = json.loads(data)
            return self._dict_to_registration(reg_dict)
        return None
    
    async def _redis_get_all(self) -> List[AgentRegistration]:
        """Get all registrations from Redis"""
        keys = await self.redis_client.keys("agent_registry:*")
        registrations = []
        
        for key in keys:
            data = await self.redis_client.get(key)
            if data:
                reg_dict = json.loads(data)
                registrations.append(self._dict_to_registration(reg_dict))
        
        return registrations
    
    async def _redis_remove(self, agent_id: str):
        """Remove registration from Redis"""
        key = f"agent_registry:{agent_id}"
        await self.redis_client.delete(key)
    
    # Consul backend methods (simplified implementations)
    async def _consul_store(self, registration: AgentRegistration):
        """Store registration in Consul"""
        # Implementation would use Consul's service registration API
        pass
    
    async def _consul_get(self, agent_id: str) -> Optional[AgentRegistration]:
        """Get registration from Consul"""
        # Implementation would use Consul's service discovery API
        pass
    
    async def _consul_get_all(self) -> List[AgentRegistration]:
        """Get all registrations from Consul"""
        # Implementation would use Consul's service listing API
        return []
    
    async def _consul_remove(self, agent_id: str):
        """Remove registration from Consul"""
        # Implementation would use Consul's service deregistration API
        pass
    
    # ZooKeeper backend methods (simplified implementations)
    async def _zk_store(self, registration: AgentRegistration):
        """Store registration in ZooKeeper"""
        # Implementation would use ZooKeeper's znode creation
        pass
    
    async def _zk_get(self, agent_id: str) -> Optional[AgentRegistration]:
        """Get registration from ZooKeeper"""
        # Implementation would use ZooKeeper's znode reading
        pass
    
    async def _zk_get_all(self) -> List[AgentRegistration]:
        """Get all registrations from ZooKeeper"""
        # Implementation would use ZooKeeper's znode listing
        return []
    
    async def _zk_remove(self, agent_id: str):
        """Remove registration from ZooKeeper"""
        # Implementation would use ZooKeeper's znode deletion
        pass
    
    def _dict_to_registration(self, reg_dict: Dict[str, Any]) -> AgentRegistration:
        """Convert dictionary back to AgentRegistration"""
        # Handle enum conversions
        reg_dict["agent_type"] = AgentType(reg_dict["agent_type"])
        reg_dict["status"] = AgentStatus(reg_dict["status"])
        
        # Handle datetime conversion
        if reg_dict["last_heartbeat"]:
            reg_dict["last_heartbeat"] = datetime.fromisoformat(reg_dict["last_heartbeat"])
        
        # Handle capabilities
        capabilities = []
        for cap_dict in reg_dict["capabilities"]:
            capabilities.append(AgentCapability(**cap_dict))
        reg_dict["capabilities"] = capabilities
        
        return AgentRegistration(**reg_dict)
    
    async def shutdown(self):
        """Shutdown discovery service"""
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        # Close backend connections
        if self.redis_client:
            await self.redis_client.close()
        if self.zk_client:
            self.zk_client.stop()
        
        logger.info("Agent Discovery Service shutdown complete")


# Factory function
def create_discovery_service(backend: ServiceBackend = ServiceBackend.MEMORY) -> AgentDiscoveryService:
    """Factory function to create discovery service"""
    return AgentDiscoveryService(backend=backend)


__all__ = [
    'AgentDiscoveryService',
    'AgentRegistration',
    'AgentCapability',
    'ServiceQuery',
    'AgentType',
    'AgentStatus',
    'ServiceBackend',
    'create_discovery_service'
]