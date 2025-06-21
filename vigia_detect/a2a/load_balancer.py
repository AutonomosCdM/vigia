"""
Medical Agent Load Balancer - Intelligent Request Distribution
============================================================

Load balancer inteligente para distribución de peticiones médicas
entre agentes especializados con algoritmos adaptativos y failover.

Features:
- Multiple load balancing algorithms
- Health-aware request routing
- Medical priority-based distribution
- Circuit breaker pattern
- Request queuing and throttling
- Metrics and monitoring
- Automatic failover and recovery
"""

import asyncio
import time
import random
import logging
import statistics
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import aiohttp
from aiohttp import web

from .protocol_layer import A2AMessage, MessagePriority, AuthLevel
from .agent_discovery_service import (
    AgentDiscoveryService, AgentRegistration, ServiceQuery, AgentType, AgentStatus
)
from ..utils.secure_logger import SecureLogger
from ..utils.audit_service import AuditService, AuditEventType

logger = SecureLogger("medical_load_balancer")


class LoadBalancingAlgorithm(Enum):
    """Load balancing algorithms"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    HEALTH_AWARE = "health_aware"
    MEDICAL_PRIORITY = "medical_priority"
    ADAPTIVE = "adaptive"


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, not allowing requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class LoadBalancerStats:
    """Load balancer statistics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    requests_per_minute: float = 0.0
    active_connections: int = 0
    
    # Per-agent stats
    agent_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Medical-specific stats
    critical_requests: int = 0
    high_priority_requests: int = 0
    phi_access_requests: int = 0


@dataclass
class CircuitBreaker:
    """Circuit breaker for agent health protection"""
    agent_id: str
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    test_request_timeout: int = 5  # seconds
    
    # State
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    
    def should_allow_request(self) -> bool:
        """Check if request should be allowed through circuit breaker"""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if we should transition to half-open
            if (self.last_failure_time and 
                (datetime.now(timezone.utc) - self.last_failure_time).total_seconds() > self.recovery_timeout):
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    def record_success(self):
        """Record successful request"""
        self.failure_count = 0
        self.last_success_time = datetime.now(timezone.utc)
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
    
    def record_failure(self):
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN


@dataclass
class RequestContext:
    """Context for load balancing decisions"""
    request_id: str
    agent_type: AgentType
    method: str
    priority: MessagePriority
    auth_level: AuthLevel
    medical_context: Optional[Dict[str, Any]] = None
    patient_urgency: Optional[str] = None
    requires_phi_access: bool = False
    preferred_agents: Optional[List[str]] = None
    exclude_agents: Optional[List[str]] = None
    timeout: float = 30.0


class MedicalLoadBalancer:
    """
    Intelligent load balancer for medical agent requests
    with health-aware routing and medical priority handling
    """
    
    def __init__(self, 
                 discovery_service: AgentDiscoveryService,
                 default_algorithm: LoadBalancingAlgorithm = LoadBalancingAlgorithm.ADAPTIVE,
                 max_queue_size: int = 1000,
                 request_timeout: float = 30.0):
        
        self.discovery_service = discovery_service
        self.default_algorithm = default_algorithm
        self.max_queue_size = max_queue_size
        self.request_timeout = request_timeout
        
        # Load balancing state
        self.round_robin_counters: Dict[AgentType, int] = defaultdict(int)
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # Request queuing
        self.request_queues: Dict[MessagePriority, asyncio.Queue] = {
            MessagePriority.CRITICAL: asyncio.Queue(maxsize=max_queue_size),
            MessagePriority.HIGH: asyncio.Queue(maxsize=max_queue_size),
            MessagePriority.NORMAL: asyncio.Queue(maxsize=max_queue_size),
            MessagePriority.LOW: asyncio.Queue(maxsize=max_queue_size)
        }
        
        # Statistics and monitoring
        self.stats = LoadBalancerStats()
        self.response_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.request_history: deque = deque(maxlen=1000)
        
        # Background tasks
        self.background_tasks: set = set()
        
        # Audit service
        self.audit_service = AuditService()
        
        logger.info(f"Medical Load Balancer initialized with algorithm: {default_algorithm.value}")
    
    async def initialize(self):
        """Initialize load balancer"""
        # Start queue processors
        for priority in MessagePriority:
            task = asyncio.create_task(self._process_queue(priority))
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)
        
        # Start statistics updater
        stats_task = asyncio.create_task(self._update_stats_loop())
        self.background_tasks.add(stats_task)
        stats_task.add_done_callback(self.background_tasks.discard)
        
        logger.info("Load balancer initialization complete")
    
    async def route_request(self, 
                           context: RequestContext,
                           message: A2AMessage,
                           algorithm: Optional[LoadBalancingAlgorithm] = None) -> Any:
        """
        Route request to best available agent
        """
        algorithm = algorithm or self.default_algorithm
        
        try:
            # Record request
            self.stats.total_requests += 1
            self.request_history.append({
                "timestamp": datetime.now(timezone.utc),
                "request_id": context.request_id,
                "priority": context.priority.value,
                "agent_type": context.agent_type.value
            })
            
            # Handle critical/high priority requests immediately
            if context.priority in [MessagePriority.CRITICAL, MessagePriority.HIGH]:
                return await self._route_immediate(context, message, algorithm)
            
            # Queue normal/low priority requests
            await self._queue_request(context, message, algorithm)
            
            # Wait for response (this would be handled by queue processor)
            # For now, route immediately
            return await self._route_immediate(context, message, algorithm)
            
        except Exception as e:
            self.stats.failed_requests += 1
            logger.error(f"Request routing failed: {e}")
            raise
    
    async def _route_immediate(self,
                              context: RequestContext,
                              message: A2AMessage,
                              algorithm: LoadBalancingAlgorithm) -> Any:
        """Route request immediately without queuing"""
        
        # Find suitable agents
        suitable_agents = await self._find_suitable_agents(context)
        if not suitable_agents:
            raise Exception(f"No suitable agents found for {context.agent_type.value}")
        
        # Select agent based on algorithm
        selected_agent = await self._select_agent(suitable_agents, context, algorithm)
        if not selected_agent:
            raise Exception("No healthy agents available")
        
        # Check circuit breaker
        circuit_breaker = self._get_circuit_breaker(selected_agent.agent_id)
        if not circuit_breaker.should_allow_request():
            # Try alternative agent
            alternative_agents = [a for a in suitable_agents if a.agent_id != selected_agent.agent_id]
            if alternative_agents:
                selected_agent = alternative_agents[0]
            else:
                raise Exception(f"Agent {selected_agent.agent_id} circuit breaker open, no alternatives")
        
        # Route request
        try:
            start_time = time.time()
            result = await self._send_request_to_agent(selected_agent, message, context)
            
            # Record success
            response_time = time.time() - start_time
            self._record_success(selected_agent.agent_id, response_time)
            circuit_breaker.record_success()
            
            self.stats.successful_requests += 1
            return result
            
        except Exception as e:
            # Record failure
            self._record_failure(selected_agent.agent_id)
            circuit_breaker.record_failure()
            
            # Try failover if available
            alternative_agents = [a for a in suitable_agents if a.agent_id != selected_agent.agent_id]
            if alternative_agents:
                logger.warning(f"Failing over from {selected_agent.agent_id} to alternative agent")
                return await self._route_with_failover(alternative_agents, message, context)
            
            raise e
    
    async def _find_suitable_agents(self, context: RequestContext) -> List[AgentRegistration]:
        """Find agents suitable for the request"""
        query = ServiceQuery(
            agent_type=context.agent_type,
            requires_phi_access=context.requires_phi_access,
            medical_compliant_only=True,
            preferred_agents=context.preferred_agents,
            exclude_agents=context.exclude_agents
        )
        
        # Adjust query based on priority
        if context.priority == MessagePriority.CRITICAL:
            query.max_load_factor = 1.0  # Allow overload for critical requests
            query.min_success_rate = 0.5  # Lower threshold for emergencies
        elif context.priority == MessagePriority.HIGH:
            query.max_load_factor = 0.9
            query.min_success_rate = 0.7
        else:
            query.max_load_factor = 0.8
            query.min_success_rate = 0.8
        
        return await self.discovery_service.discover_agents(query)
    
    async def _select_agent(self,
                           agents: List[AgentRegistration],
                           context: RequestContext,
                           algorithm: LoadBalancingAlgorithm) -> Optional[AgentRegistration]:
        """Select best agent using specified algorithm"""
        
        if not agents:
            return None
        
        if algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
            return self._round_robin_select(agents, context.agent_type)
        
        elif algorithm == LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select(agents, context.agent_type)
        
        elif algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
            return self._least_connections_select(agents)
        
        elif algorithm == LoadBalancingAlgorithm.LEAST_RESPONSE_TIME:
            return self._least_response_time_select(agents)
        
        elif algorithm == LoadBalancingAlgorithm.HEALTH_AWARE:
            return self._health_aware_select(agents)
        
        elif algorithm == LoadBalancingAlgorithm.MEDICAL_PRIORITY:
            return self._medical_priority_select(agents, context)
        
        elif algorithm == LoadBalancingAlgorithm.ADAPTIVE:
            return self._adaptive_select(agents, context)
        
        else:
            return agents[0]  # Default to first agent
    
    def _round_robin_select(self, agents: List[AgentRegistration], agent_type: AgentType) -> AgentRegistration:
        """Round robin selection"""
        index = self.round_robin_counters[agent_type] % len(agents)
        self.round_robin_counters[agent_type] += 1
        return agents[index]
    
    def _weighted_round_robin_select(self, agents: List[AgentRegistration], agent_type: AgentType) -> AgentRegistration:
        """Weighted round robin based on agent capacity"""
        # Calculate weights based on inverse load factor
        weights = [max(0.1, 1.0 - agent.load_factor) for agent in agents]
        total_weight = sum(weights)
        
        # Normalize weights
        weights = [w / total_weight for w in weights]
        
        # Select based on weight
        r = random.random()
        cumulative = 0
        for i, weight in enumerate(weights):
            cumulative += weight
            if r <= cumulative:
                return agents[i]
        
        return agents[-1]  # Fallback
    
    def _least_connections_select(self, agents: List[AgentRegistration]) -> AgentRegistration:
        """Select agent with least current connections"""
        return min(agents, key=lambda a: a.current_connections)
    
    def _least_response_time_select(self, agents: List[AgentRegistration]) -> AgentRegistration:
        """Select agent with best response time"""
        def avg_response_time(agent: AgentRegistration) -> float:
            return sum(cap.avg_response_time for cap in agent.capabilities) / len(agent.capabilities)
        
        return min(agents, key=avg_response_time)
    
    def _health_aware_select(self, agents: List[AgentRegistration]) -> AgentRegistration:
        """Select agent based on health score"""
        def health_score(agent: AgentRegistration) -> float:
            # Higher score is better
            base_score = 100
            
            # Penalize based on load
            load_penalty = agent.load_factor * 50
            
            # Penalize based on error rate
            error_penalty = agent.error_rate * 30
            
            # Penalize based on status
            status_penalty = 0
            if agent.status == AgentStatus.DEGRADED:
                status_penalty = 20
            elif agent.status == AgentStatus.UNHEALTHY:
                status_penalty = 80
            
            return base_score - load_penalty - error_penalty - status_penalty
        
        return max(agents, key=health_score)
    
    def _medical_priority_select(self, agents: List[AgentRegistration], context: RequestContext) -> AgentRegistration:
        """Select agent based on medical priority requirements"""
        # For critical medical cases, prefer agents with:
        # 1. Lowest error rate
        # 2. Fastest response time
        # 3. Medical compliance
        
        if context.priority == MessagePriority.CRITICAL:
            # For critical cases, prioritize reliability
            medical_agents = [a for a in agents if a.hipaa_compliant and a.audit_enabled]
            if medical_agents:
                return min(medical_agents, key=lambda a: a.error_rate)
        
        # For other priorities, use health-aware selection
        return self._health_aware_select(agents)
    
    def _adaptive_select(self, agents: List[AgentRegistration], context: RequestContext) -> AgentRegistration:
        """Adaptive selection based on current conditions"""
        # Analyze recent performance and adapt algorithm
        
        # If high error rates, prefer most reliable agents
        recent_error_rate = self._calculate_recent_error_rate()
        if recent_error_rate > 0.1:  # 10% error rate
            return self._health_aware_select(agents)
        
        # If high load, balance connections
        avg_load = sum(a.load_factor for a in agents) / len(agents)
        if avg_load > 0.7:
            return self._least_connections_select(agents)
        
        # If medical critical, use medical priority
        if context.priority in [MessagePriority.CRITICAL, MessagePriority.HIGH]:
            return self._medical_priority_select(agents, context)
        
        # Default to weighted round robin
        return self._weighted_round_robin_select(agents, context.agent_type)
    
    def _calculate_recent_error_rate(self) -> float:
        """Calculate error rate from recent requests"""
        if not self.request_history:
            return 0.0
        
        recent_threshold = datetime.now(timezone.utc) - timedelta(minutes=5)
        recent_requests = [
            req for req in self.request_history 
            if req["timestamp"] > recent_threshold
        ]
        
        if not recent_requests:
            return 0.0
        
        # This is simplified - in practice, we'd track success/failure per request
        return min(0.2, self.stats.failed_requests / max(1, self.stats.total_requests))
    
    async def _send_request_to_agent(self,
                                    agent: AgentRegistration,
                                    message: A2AMessage,
                                    context: RequestContext) -> Any:
        """Send request to specific agent"""
        url = f"{agent.endpoint}/a2a/message"
        
        # Update message with routing info
        message.add_audit_entry("routed_by_load_balancer", "load_balancer", {
            "selected_agent": agent.agent_id,
            "algorithm_used": self.default_algorithm.value,
            "priority": context.priority.value
        })
        
        timeout = aiohttp.ClientTimeout(total=context.timeout)
        
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=message.to_dict()) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        raise Exception(f"Agent responded with status {response.status}")
        
        except asyncio.TimeoutError:
            raise Exception(f"Request to agent {agent.agent_id} timed out")
        except Exception as e:
            raise Exception(f"Request to agent {agent.agent_id} failed: {str(e)}")
    
    async def _route_with_failover(self,
                                  agents: List[AgentRegistration],
                                  message: A2AMessage,
                                  context: RequestContext) -> Any:
        """Route request with failover to alternative agents"""
        last_exception = None
        
        for agent in agents:
            circuit_breaker = self._get_circuit_breaker(agent.agent_id)
            if not circuit_breaker.should_allow_request():
                continue
            
            try:
                start_time = time.time()
                result = await self._send_request_to_agent(agent, message, context)
                
                # Record success
                response_time = time.time() - start_time
                self._record_success(agent.agent_id, response_time)
                circuit_breaker.record_success()
                
                return result
                
            except Exception as e:
                last_exception = e
                self._record_failure(agent.agent_id)
                circuit_breaker.record_failure()
                continue
        
        # All agents failed
        if last_exception:
            raise last_exception
        else:
            raise Exception("No healthy agents available for failover")
    
    async def _queue_request(self,
                            context: RequestContext,
                            message: A2AMessage,
                            algorithm: LoadBalancingAlgorithm):
        """Queue request for later processing"""
        queue = self.request_queues[context.priority]
        
        if queue.full():
            raise Exception(f"Request queue full for priority {context.priority.value}")
        
        await queue.put((context, message, algorithm))
    
    async def _process_queue(self, priority: MessagePriority):
        """Process requests from priority queue"""
        queue = self.request_queues[priority]
        
        while True:
            try:
                # Get request from queue
                context, message, algorithm = await queue.get()
                
                # Process request
                try:
                    await self._route_immediate(context, message, algorithm)
                except Exception as e:
                    logger.error(f"Queued request processing failed: {e}")
                finally:
                    queue.task_done()
                    
            except Exception as e:
                logger.error(f"Queue processing error for {priority.value}: {e}")
                await asyncio.sleep(1)  # Brief pause before retrying
    
    def _get_circuit_breaker(self, agent_id: str) -> CircuitBreaker:
        """Get or create circuit breaker for agent"""
        if agent_id not in self.circuit_breakers:
            self.circuit_breakers[agent_id] = CircuitBreaker(agent_id)
        return self.circuit_breakers[agent_id]
    
    def _record_success(self, agent_id: str, response_time: float):
        """Record successful request for agent"""
        # Update response times
        self.response_times[agent_id].append(response_time)
        
        # Update agent stats
        if agent_id not in self.stats.agent_stats:
            self.stats.agent_stats[agent_id] = {
                "requests": 0,
                "successes": 0,
                "failures": 0,
                "avg_response_time": 0.0
            }
        
        agent_stats = self.stats.agent_stats[agent_id]
        agent_stats["requests"] += 1
        agent_stats["successes"] += 1
        
        # Update average response time
        agent_stats["avg_response_time"] = statistics.mean(self.response_times[agent_id])
    
    def _record_failure(self, agent_id: str):
        """Record failed request for agent"""
        if agent_id not in self.stats.agent_stats:
            self.stats.agent_stats[agent_id] = {
                "requests": 0,
                "successes": 0,
                "failures": 0,
                "avg_response_time": 0.0
            }
        
        agent_stats = self.stats.agent_stats[agent_id]
        agent_stats["requests"] += 1
        agent_stats["failures"] += 1
    
    async def _update_stats_loop(self):
        """Background task to update statistics"""
        while True:
            try:
                await asyncio.sleep(60)  # Update every minute
                await self._update_statistics()
            except Exception as e:
                logger.error(f"Stats update error: {e}")
    
    async def _update_statistics(self):
        """Update load balancer statistics"""
        # Calculate requests per minute
        recent_threshold = datetime.now(timezone.utc) - timedelta(minutes=1)
        recent_requests = [
            req for req in self.request_history 
            if req["timestamp"] > recent_threshold
        ]
        self.stats.requests_per_minute = len(recent_requests)
        
        # Update average response time
        all_response_times = []
        for agent_times in self.response_times.values():
            all_response_times.extend(agent_times)
        
        if all_response_times:
            self.stats.avg_response_time = statistics.mean(all_response_times)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current load balancer statistics"""
        return {
            "load_balancer_stats": self.stats.__dict__,
            "circuit_breakers": {
                agent_id: {
                    "state": cb.state.value,
                    "failure_count": cb.failure_count,
                    "last_failure": cb.last_failure_time.isoformat() if cb.last_failure_time else None
                }
                for agent_id, cb in self.circuit_breakers.items()
            },
            "queue_sizes": {
                priority.value: queue.qsize()
                for priority, queue in self.request_queues.items()
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on load balancer"""
        # Check queue health
        queue_health = {}
        for priority, queue in self.request_queues.items():
            queue_health[priority.value] = {
                "size": queue.qsize(),
                "max_size": queue.maxsize,
                "utilization": queue.qsize() / queue.maxsize if queue.maxsize > 0 else 0
            }
        
        # Check circuit breaker health
        circuit_health = {}
        for agent_id, cb in self.circuit_breakers.items():
            circuit_health[agent_id] = cb.state.value
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "queue_health": queue_health,
            "circuit_breaker_health": circuit_health,
            "background_tasks": len(self.background_tasks)
        }
    
    async def shutdown(self):
        """Shutdown load balancer"""
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        
        logger.info("Medical Load Balancer shutdown complete")


# Factory function
def create_load_balancer(discovery_service: AgentDiscoveryService,
                        algorithm: LoadBalancingAlgorithm = LoadBalancingAlgorithm.ADAPTIVE) -> MedicalLoadBalancer:
    """Factory function to create load balancer"""
    return MedicalLoadBalancer(
        discovery_service=discovery_service,
        default_algorithm=algorithm
    )


__all__ = [
    'MedicalLoadBalancer',
    'LoadBalancingAlgorithm',
    'RequestContext',
    'LoadBalancerStats',
    'CircuitBreaker',
    'CircuitState',
    'create_load_balancer'
]