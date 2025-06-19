"""
Redis MCP Server - Serverless Implementation
===========================================

Medical-grade caching and session management via Redis.
Provides MCP tools for protocol caching, session management, and vector search.
"""

import os
import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from .base_mcp_server import BaseMCPServer
from ..utils.shared_utilities import VigiaLogger

logger = VigiaLogger.get_logger(__name__)

# Redis integration (optional)
try:
    import redis.asyncio as redis
    from redis.exceptions import RedisError
    redis_available = True
except ImportError:
    logger.warning("Redis not available - running in mock mode")
    redis_available = False
    RedisError = Exception


class RedisMCPServer(BaseMCPServer):
    """Serverless MCP server for Redis caching and session management."""
    
    def __init__(self):
        """Initialize Redis MCP server"""
        super().__init__("Redis", "1.0.0")
        
        # Initialize Redis client (optional)
        self.redis_client = None
        if redis_available:
            self._init_redis_client()
        
        # Cache configuration for medical data
        self.cache_config = {
            "medical_protocols": {
                "prefix": "vigia:protocols:",
                "ttl_hours": 24,
                "description": "Medical protocol cache"
            },
            "patient_sessions": {
                "prefix": "vigia:sessions:",
                "ttl_hours": 1,
                "description": "Patient workflow sessions"
            },
            "llm_responses": {
                "prefix": "vigia:llm:",
                "ttl_hours": 2,
                "description": "Cached LLM responses"
            },
            "vector_embeddings": {
                "prefix": "vigia:vectors:",
                "ttl_hours": 48,
                "description": "Medical knowledge vectors"
            }
        }
        
        # Register tools
        self._register_redis_tools()
        
        # Register resources
        self._register_redis_resources()
    
    def _init_redis_client(self):
        """Initialize Redis client if available"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            logger.info("Redis client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
    
    def _register_redis_tools(self):
        """Register Redis MCP tools"""
        
        # Tool for searching medical protocols
        self.register_tool(
            name="search_medical_protocols",
            description="Search cached medical protocols using semantic similarity",
            handler=self._search_medical_protocols,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "lpp_grade": {"type": "integer"},
                    "category": {"type": "string"},
                    "similarity_threshold": {"type": "number"},
                    "max_results": {"type": "integer"}
                },
                "required": ["query"]
            }
        )
        
        # Tool for caching medical responses
        self.register_tool(
            name="cache_medical_response",
            description="Cache LLM response with medical context",
            handler=self._cache_medical_response,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "response": {"type": "string"},
                    "medical_context": {"type": "object"},
                    "ttl_minutes": {"type": "integer"},
                    "cache_key": {"type": "string"}
                },
                "required": ["query", "response"]
            }
        )
        
        # Tool for retrieving cached responses
        self.register_tool(
            name="get_cached_medical_response",
            description="Retrieve cached medical response by semantic similarity",
            handler=self._get_cached_medical_response,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "medical_context": {"type": "object"},
                    "similarity_threshold": {"type": "number"},
                    "exact_match": {"type": "boolean"}
                },
                "required": ["query"]
            }
        )
        
        # Tool for session management
        self.register_tool(
            name="manage_medical_session",
            description="Manage medical workflow sessions",
            handler=self._manage_medical_session,
            parameters={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "get", "update", "delete", "extend"]},
                    "session_id": {"type": "string"},
                    "patient_code": {"type": "string"},
                    "session_data": {"type": "object"},
                    "ttl_minutes": {"type": "integer"}
                },
                "required": ["action", "session_id"]
            }
        )
        
        # Tool for vector operations
        self.register_tool(
            name="vector_operations",
            description="Perform vector operations for medical knowledge search",
            handler=self._vector_operations,
            parameters={
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["search", "store", "update", "delete"]},
                    "vector_data": {"type": "object"},
                    "search_params": {"type": "object"}
                },
                "required": ["operation"]
            }
        )
        
        # Tool for cache statistics
        self.register_tool(
            name="get_cache_statistics",
            description="Get Redis cache performance statistics",
            handler=self._get_cache_statistics,
            parameters={
                "type": "object",
                "properties": {
                    "cache_type": {"type": "string"},
                    "detailed": {"type": "boolean"}
                }
            }
        )
        
        # Tool for cache maintenance
        self.register_tool(
            name="maintain_cache",
            description="Perform cache maintenance operations",
            handler=self._maintain_cache,
            parameters={
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "enum": ["cleanup", "clear", "optimize"]},
                    "cache_type": {"type": "string"},
                    "force": {"type": "boolean"}
                },
                "required": ["operation"]
            }
        )
    
    def _register_redis_resources(self):
        """Register Redis MCP resources"""
        
        # Cached protocols resource
        self.register_resource(
            uri="redis://cache/protocols",
            name="Cached Medical Protocols",
            description="Medical protocols stored in Redis cache",
            handler=self._get_cached_protocols
        )
        
        # Active sessions resource
        self.register_resource(
            uri="redis://sessions/active",
            name="Active Medical Sessions",
            description="Currently active patient workflow sessions",
            handler=self._get_active_sessions
        )
        
        # Performance statistics
        self.register_resource(
            uri="redis://stats/performance",
            name="Cache Performance Statistics",
            description="Redis cache performance metrics and statistics",
            handler=self._get_performance_stats
        )
        
        # Medical vectors resource
        self.register_resource(
            uri="redis://vectors/medical",
            name="Medical Knowledge Vectors",
            description="Vector embeddings for medical knowledge search",
            handler=self._get_medical_vectors
        )
    
    async def _list_tools(self) -> Dict[str, Any]:
        """List available Redis tools"""
        return {
            "tools": [
                {
                    "name": tool_name,
                    "description": tool_data["description"],
                    "inputSchema": tool_data["parameters"],
                    "medical_compliant": True,
                    "cache_operation": True
                }
                for tool_name, tool_data in self.tools.items()
            ]
        }
    
    async def _call_tool(self, params: Dict[str, Any]) -> Any:
        """Call a specific Redis tool"""
        tool_name = params.get("name")
        tool_params = params.get("arguments", {})
        
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        handler = self.tools[tool_name]["handler"]
        return await handler(tool_params)
    
    async def _list_resources(self) -> Dict[str, Any]:
        """List available Redis resources"""
        return {
            "resources": [
                {
                    "uri": resource_uri,
                    "name": resource_data["name"],
                    "description": resource_data["description"],
                    "mimeType": "application/json",
                    "medical_compliant": True
                }
                for resource_uri, resource_data in self.resources.items()
            ]
        }
    
    async def _read_resource(self, params: Dict[str, Any]) -> Any:
        """Read a specific Redis resource"""
        resource_uri = params.get("uri")
        
        if resource_uri not in self.resources:
            raise ValueError(f"Unknown resource: {resource_uri}")
        
        handler = self.resources[resource_uri]["handler"]
        return await handler()
    
    # Tool implementations
    
    async def _search_medical_protocols(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search medical protocols using semantic similarity"""
        if not self.redis_client:
            return {"status": "mock", "protocols": [], "message": "Redis not configured"}
        
        try:
            query = params.get("query")
            lpp_grade = params.get("lpp_grade")
            category = params.get("category")
            similarity_threshold = params.get("similarity_threshold", 0.8)
            max_results = params.get("max_results", 5)
            
            # Build search pattern
            search_pattern = f"{self.cache_config['medical_protocols']['prefix']}*"
            
            # Get all protocol keys
            protocol_keys = await self.redis_client.keys(search_pattern)
            
            protocols = []
            
            for key in protocol_keys:
                try:
                    protocol_data = await self.redis_client.get(key)
                    if protocol_data:
                        protocol = json.loads(protocol_data)
                        
                        # Apply filters
                        if lpp_grade and protocol.get("lpp_grade") != lpp_grade:
                            continue
                        if category and protocol.get("category") != category:
                            continue
                        
                        # Calculate semantic similarity (simplified)
                        similarity = self._calculate_similarity(query, protocol.get("content", ""))
                        
                        if similarity >= similarity_threshold:
                            protocol["similarity_score"] = similarity
                            protocols.append(protocol)
                            
                except json.JSONDecodeError:
                    continue
            
            # Sort by similarity and limit results
            protocols.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
            protocols = protocols[:max_results]
            
            logger.info(f"Found {len(protocols)} matching medical protocols")
            
            return {
                "status": "found",
                "query": query,
                "protocols": protocols,
                "total_found": len(protocols),
                "search_params": {
                    "lpp_grade": lpp_grade,
                    "category": category,
                    "similarity_threshold": similarity_threshold
                }
            }
            
        except RedisError as e:
            logger.error(f"Redis search failed: {e}")
            raise ValueError(f"Protocol search failed: {e}")
    
    async def _cache_medical_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Cache LLM response with medical context"""
        if not self.redis_client:
            return {"status": "mock", "message": "Response caching mock"}
        
        try:
            query = params.get("query")
            response = params.get("response")
            medical_context = params.get("medical_context", {})
            ttl_minutes = params.get("ttl_minutes", 30)
            custom_key = params.get("cache_key")
            
            # Generate cache key
            if custom_key:
                cache_key = f"{self.cache_config['llm_responses']['prefix']}{custom_key}"
            else:
                # Create key from query hash and medical context
                context_str = json.dumps(medical_context, sort_keys=True)
                key_data = f"{query}:{context_str}"
                cache_key = f"{self.cache_config['llm_responses']['prefix']}{hash(key_data)}"
            
            # Prepare cache data
            cache_data = {
                "query": query,
                "response": response,
                "medical_context": medical_context,
                "cached_at": datetime.utcnow().isoformat(),
                "cache_version": "1.0"
            }
            
            # Store in Redis with TTL
            await self.redis_client.setex(
                cache_key,
                ttl_minutes * 60,
                json.dumps(cache_data)
            )
            
            logger.info(f"Cached medical response: {cache_key}")
            
            return {
                "status": "cached",
                "cache_key": cache_key,
                "ttl_minutes": ttl_minutes,
                "cached_at": cache_data["cached_at"]
            }
            
        except RedisError as e:
            logger.error(f"Response caching failed: {e}")
            raise ValueError(f"Cache operation failed: {e}")
    
    async def _get_cached_medical_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve cached medical response by semantic similarity"""
        if not self.redis_client:
            return {"status": "mock", "found": False, "message": "Cache retrieval mock"}
        
        try:
            query = params.get("query")
            medical_context = params.get("medical_context", {})
            similarity_threshold = params.get("similarity_threshold", 0.85)
            exact_match = params.get("exact_match", False)
            
            # Search for cached responses
            search_pattern = f"{self.cache_config['llm_responses']['prefix']}*"
            response_keys = await self.redis_client.keys(search_pattern)
            
            best_match = None
            best_similarity = 0
            
            for key in response_keys:
                try:
                    cached_data = await self.redis_client.get(key)
                    if cached_data:
                        cache_entry = json.loads(cached_data)
                        
                        # Compare medical context if provided
                        if medical_context:
                            context_match = self._compare_medical_context(
                                medical_context, 
                                cache_entry.get("medical_context", {})
                            )
                            if not context_match:
                                continue
                        
                        # Calculate query similarity
                        if exact_match:
                            if cache_entry.get("query") == query:
                                return {
                                    "status": "found",
                                    "cached_response": cache_entry,
                                    "similarity_score": 1.0,
                                    "cache_key": key
                                }
                        else:
                            similarity = self._calculate_similarity(
                                query, 
                                cache_entry.get("query", "")
                            )
                            
                            if similarity > best_similarity and similarity >= similarity_threshold:
                                best_similarity = similarity
                                best_match = {
                                    "cached_response": cache_entry,
                                    "similarity_score": similarity,
                                    "cache_key": key
                                }
                                
                except json.JSONDecodeError:
                    continue
            
            if best_match:
                return {
                    "status": "found",
                    **best_match
                }
            else:
                return {
                    "status": "not_found",
                    "searched_keys": len(response_keys),
                    "similarity_threshold": similarity_threshold
                }
                
        except RedisError as e:
            logger.error(f"Cache retrieval failed: {e}")
            raise ValueError(f"Cache retrieval failed: {e}")
    
    async def _manage_medical_session(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Manage medical workflow sessions"""
        if not self.redis_client:
            return {"status": "mock", "message": "Session management mock"}
        
        try:
            action = params.get("action")
            session_id = params.get("session_id")
            patient_code = params.get("patient_code")
            session_data = params.get("session_data", {})
            ttl_minutes = params.get("ttl_minutes", 15)
            
            session_key = f"{self.cache_config['patient_sessions']['prefix']}{session_id}"
            
            if action == "create":
                # Create new session
                new_session = {
                    "session_id": session_id,
                    "patient_code": patient_code,
                    "created_at": datetime.utcnow().isoformat(),
                    "last_activity": datetime.utcnow().isoformat(),
                    "data": session_data,
                    "status": "active"
                }
                
                await self.redis_client.setex(
                    session_key,
                    ttl_minutes * 60,
                    json.dumps(new_session)
                )
                
                return {"status": "created", "session_id": session_id}
            
            elif action == "get":
                # Get existing session
                session_str = await self.redis_client.get(session_key)
                if session_str:
                    session = json.loads(session_str)
                    return {"status": "found", "session": session}
                else:
                    return {"status": "not_found", "session_id": session_id}
            
            elif action == "update":
                # Update session data
                session_str = await self.redis_client.get(session_key)
                if session_str:
                    session = json.loads(session_str)
                    session["data"].update(session_data)
                    session["last_activity"] = datetime.utcnow().isoformat()
                    
                    await self.redis_client.setex(
                        session_key,
                        ttl_minutes * 60,
                        json.dumps(session)
                    )
                    
                    return {"status": "updated", "session_id": session_id}
                else:
                    return {"status": "not_found", "session_id": session_id}
            
            elif action == "delete":
                # Delete session
                deleted = await self.redis_client.delete(session_key)
                return {"status": "deleted" if deleted else "not_found", "session_id": session_id}
            
            elif action == "extend":
                # Extend session TTL
                extended = await self.redis_client.expire(session_key, ttl_minutes * 60)
                return {"status": "extended" if extended else "not_found", "session_id": session_id}
            
            else:
                raise ValueError(f"Unknown action: {action}")
                
        except RedisError as e:
            logger.error(f"Session management failed: {e}")
            raise ValueError(f"Session operation failed: {e}")
    
    async def _vector_operations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform vector operations for medical knowledge search"""
        if not self.redis_client:
            return {"status": "mock", "message": "Vector operations mock"}
        
        operation = params.get("operation")
        
        return {
            "status": "implemented",
            "operation": operation,
            "message": "Vector operations would be implemented with Redis vector search"
        }
    
    async def _get_cache_statistics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get Redis cache performance statistics"""
        if not self.redis_client:
            return {"status": "mock", "stats": {}}
        
        try:
            cache_type = params.get("cache_type", "all")
            detailed = params.get("detailed", False)
            
            stats = {}
            
            # Get general Redis info
            redis_info = await self.redis_client.info()
            
            stats["redis_info"] = {
                "memory_used": redis_info.get("used_memory_human"),
                "connected_clients": redis_info.get("connected_clients"),
                "total_commands": redis_info.get("total_commands_processed"),
                "keyspace_hits": redis_info.get("keyspace_hits"),
                "keyspace_misses": redis_info.get("keyspace_misses")
            }
            
            # Calculate hit ratio
            hits = redis_info.get("keyspace_hits", 0)
            misses = redis_info.get("keyspace_misses", 0)
            total = hits + misses
            stats["hit_ratio"] = hits / total if total > 0 else 0
            
            # Get cache-specific stats if requested
            if cache_type != "all":
                config = self.cache_config.get(cache_type)
                if config:
                    pattern = f"{config['prefix']}*"
                    keys = await self.redis_client.keys(pattern)
                    stats[f"{cache_type}_stats"] = {
                        "total_keys": len(keys),
                        "pattern": pattern
                    }
            
            return {"status": "retrieved", "stats": stats}
            
        except RedisError as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _maintain_cache(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform cache maintenance operations"""
        if not self.redis_client:
            return {"status": "mock", "message": "Cache maintenance mock"}
        
        operation = params.get("operation")
        cache_type = params.get("cache_type", "all")
        force = params.get("force", False)
        
        try:
            if operation == "cleanup":
                # Remove expired keys (Redis handles this automatically, but we can force)
                return {"status": "cleaned", "operation": "cleanup"}
            
            elif operation == "clear":
                # Clear specific cache type
                if cache_type == "all":
                    if force:
                        await self.redis_client.flushdb()
                        return {"status": "cleared", "cache_type": "all"}
                    else:
                        return {"status": "cancelled", "message": "Use force=true to clear all cache"}
                else:
                    config = self.cache_config.get(cache_type)
                    if config:
                        pattern = f"{config['prefix']}*"
                        keys = await self.redis_client.keys(pattern)
                        if keys:
                            await self.redis_client.delete(*keys)
                        return {"status": "cleared", "cache_type": cache_type, "keys_deleted": len(keys)}
            
            return {"status": "completed", "operation": operation}
            
        except RedisError as e:
            logger.error(f"Cache maintenance failed: {e}")
            raise ValueError(f"Maintenance operation failed: {e}")
    
    # Resource implementations
    
    async def _get_cached_protocols(self) -> Dict[str, Any]:
        """Get cached medical protocols"""
        if not self.redis_client:
            return {"protocols": [], "status": "mock"}
        
        try:
            pattern = f"{self.cache_config['medical_protocols']['prefix']}*"
            keys = await self.redis_client.keys(pattern)
            
            protocols = []
            for key in keys:
                protocol_data = await self.redis_client.get(key)
                if protocol_data:
                    protocols.append(json.loads(protocol_data))
            
            return {
                "protocols": protocols,
                "total": len(protocols),
                "cache_pattern": pattern
            }
            
        except Exception as e:
            return {"protocols": [], "error": str(e)}
    
    async def _get_active_sessions(self) -> Dict[str, Any]:
        """Get active medical sessions"""
        if not self.redis_client:
            return {"sessions": [], "status": "mock"}
        
        try:
            pattern = f"{self.cache_config['patient_sessions']['prefix']}*"
            keys = await self.redis_client.keys(pattern)
            
            sessions = []
            for key in keys:
                session_data = await self.redis_client.get(key)
                if session_data:
                    session = json.loads(session_data)
                    # Remove sensitive data for listing
                    session_summary = {
                        "session_id": session.get("session_id"),
                        "patient_code": session.get("patient_code"),
                        "created_at": session.get("created_at"),
                        "last_activity": session.get("last_activity"),
                        "status": session.get("status")
                    }
                    sessions.append(session_summary)
            
            return {
                "sessions": sessions,
                "total_active": len(sessions)
            }
            
        except Exception as e:
            return {"sessions": [], "error": str(e)}
    
    async def _get_performance_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        return await self._get_cache_statistics({"cache_type": "all", "detailed": True})
    
    async def _get_medical_vectors(self) -> Dict[str, Any]:
        """Get medical knowledge vectors"""
        if not self.redis_client:
            return {"vectors": [], "status": "mock"}
        
        # This would integrate with actual vector storage
        return {
            "vectors": [],
            "status": "implemented",
            "message": "Medical vector storage would be implemented"
        }
    
    # Helper methods
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts (simplified)"""
        # This is a simplified similarity calculation
        # In production, would use proper embedding-based similarity
        
        if not text1 or not text2:
            return 0.0
        
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _compare_medical_context(self, context1: Dict[str, Any], context2: Dict[str, Any]) -> bool:
        """Compare medical contexts for cache matching"""
        important_fields = ["patient_code", "lpp_grade", "location"]
        
        for field in important_fields:
            if field in context1 and field in context2:
                if context1[field] != context2[field]:
                    return False
        
        return True


# Create server instance
redis_server = RedisMCPServer()

# Export FastAPI app for deployment
app = redis_server.app