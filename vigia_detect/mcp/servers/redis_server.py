#!/usr/bin/env python3
"""
Vigia Redis MCP Server
Custom MCP server for Redis cache and vector storage operations
Enables medical data caching, vector search, and real-time analytics
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import hashlib

try:
    import redis
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from mcp.server import Server
from mcp.types import (
    Tool, Resource, ResourceTemplate, TextContent,
    ListResourcesResult, ReadResourceResult, CallToolResult
)


@dataclass
class RedisConfig:
    """Redis server configuration"""
    url: str
    password: Optional[str] = None
    db: int = 0
    max_connections: int = 10
    timeout: int = 30


class VigiaRedisServer:
    """Vigia Redis MCP Server for medical caching and vectors"""
    
    def __init__(self, config: RedisConfig):
        self.config = config
        self.server = Server("vigia-redis")
        self.redis_client = None
        self._setup_tools()
        self._setup_resources()
    
    async def _get_redis_client(self):
        """Get or create Redis client"""
        if not REDIS_AVAILABLE:
            raise ImportError("Redis library not available. Install with: pip install redis")
        
        if not self.redis_client:
            self.redis_client = aioredis.from_url(
                self.config.url,
                password=self.config.password,
                db=self.config.db,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.timeout
            )
        return self.redis_client
    
    def _setup_tools(self):
        """Setup Redis MCP tools"""
        
        @self.server.call_tool()
        async def cache_patient_data(arguments: Dict[str, Any]) -> List[TextContent]:
            """Cache patient data with TTL"""
            try:
                patient_id = arguments.get("patient_id", "")
                patient_data = arguments.get("patient_data", {})
                ttl_hours = arguments.get("ttl_hours", 24)
                
                if not patient_id:
                    return [TextContent(
                        type="text",
                        text="❌ Patient ID is required"
                    )]
                
                redis_client = await self._get_redis_client()
                
                # Create cache key
                cache_key = f"vigia:patient:{patient_id}"
                
                # Add metadata
                cached_data = {
                    "patient_data": patient_data,
                    "cached_at": datetime.utcnow().isoformat(),
                    "source": "vigia_medical_system",
                    "version": "1.4.0"
                }
                
                # Cache with TTL
                await redis_client.setex(
                    cache_key,
                    timedelta(hours=ttl_hours),
                    json.dumps(cached_data)
                )
                
                return [TextContent(
                    type="text",
                    text=f"✅ Patient data cached successfully\n"
                         f"Key: {cache_key}\n"
                         f"TTL: {ttl_hours} hours\n"
                         f"Data size: {len(json.dumps(cached_data))} bytes"
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error caching patient data: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def get_patient_data(arguments: Dict[str, Any]) -> List[TextContent]:
            """Retrieve cached patient data"""
            try:
                patient_id = arguments.get("patient_id", "")
                
                if not patient_id:
                    return [TextContent(
                        type="text",
                        text="❌ Patient ID is required"
                    )]
                
                redis_client = await self._get_redis_client()
                cache_key = f"vigia:patient:{patient_id}"
                
                cached_data = await redis_client.get(cache_key)
                
                if cached_data:
                    data = json.loads(cached_data)
                    ttl = await redis_client.ttl(cache_key)
                    
                    return [TextContent(
                        type="text",
                        text=f"✅ Patient data retrieved from cache\n"
                             f"Cached at: {data.get('cached_at', 'Unknown')}\n"
                             f"TTL remaining: {ttl} seconds\n"
                             f"```json\n{json.dumps(data['patient_data'], indent=2)}\n```"
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=f"❌ No cached data found for patient {patient_id}"
                    )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error retrieving patient data: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def cache_lpp_detection(arguments: Dict[str, Any]) -> List[TextContent]:
            """Cache LPP detection results"""
            try:
                detection_id = arguments.get("detection_id", "")
                lpp_data = arguments.get("lpp_data", {})
                image_hash = arguments.get("image_hash", "")
                
                if not detection_id:
                    detection_id = f"lpp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                redis_client = await self._get_redis_client()
                
                # Cache detection result
                detection_key = f"vigia:lpp_detection:{detection_id}"
                detection_cache = {
                    "lpp_data": lpp_data,
                    "image_hash": image_hash,
                    "detected_at": datetime.utcnow().isoformat(),
                    "detection_id": detection_id,
                    "system_version": "1.4.0"
                }
                
                await redis_client.setex(
                    detection_key,
                    timedelta(days=30),  # Keep detection results for 30 days
                    json.dumps(detection_cache)
                )
                
                # Add to detection index
                lpp_grade = lpp_data.get("grade", 0)
                confidence = lpp_data.get("confidence", 0.0)
                patient_id = lpp_data.get("patient_id", "")
                
                # Index by grade
                grade_key = f"vigia:lpp_index:grade_{lpp_grade}"
                await redis_client.zadd(grade_key, {detection_id: confidence})
                
                # Index by patient
                if patient_id:
                    patient_key = f"vigia:lpp_index:patient_{patient_id}"
                    await redis_client.zadd(patient_key, {detection_id: datetime.utcnow().timestamp()})
                
                # Update statistics
                stats_key = "vigia:lpp_stats"
                await redis_client.hincrby(stats_key, f"grade_{lpp_grade}_count", 1)
                await redis_client.hincrby(stats_key, "total_detections", 1)
                
                return [TextContent(
                    type="text",
                    text=f"✅ LPP detection cached successfully\n"
                         f"Detection ID: {detection_id}\n"
                         f"LPP Grade: {lpp_grade}\n"
                         f"Confidence: {confidence:.2f}\n"
                         f"Cache TTL: 30 days"
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error caching LPP detection: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def search_lpp_detections(arguments: Dict[str, Any]) -> List[TextContent]:
            """Search LPP detections by criteria"""
            try:
                search_criteria = arguments.get("criteria", {})
                limit = arguments.get("limit", 10)
                
                redis_client = await self._get_redis_client()
                results = []
                
                # Search by LPP grade
                if "lpp_grade" in search_criteria:
                    grade = search_criteria["lpp_grade"]
                    grade_key = f"vigia:lpp_index:grade_{grade}"
                    
                    # Get top detections by confidence
                    detection_ids = await redis_client.zrevrange(grade_key, 0, limit-1, withscores=True)
                    
                    for detection_id, confidence in detection_ids:
                        detection_key = f"vigia:lpp_detection:{detection_id}"
                        detection_data = await redis_client.get(detection_key)
                        
                        if detection_data:
                            data = json.loads(detection_data)
                            results.append({
                                "detection_id": detection_id,
                                "confidence": confidence,
                                "data": data
                            })
                
                # Search by patient ID
                elif "patient_id" in search_criteria:
                    patient_id = search_criteria["patient_id"]
                    patient_key = f"vigia:lpp_index:patient_{patient_id}"
                    
                    # Get recent detections
                    detection_ids = await redis_client.zrevrange(patient_key, 0, limit-1, withscores=True)
                    
                    for detection_id, timestamp in detection_ids:
                        detection_key = f"vigia:lpp_detection:{detection_id}"
                        detection_data = await redis_client.get(detection_key)
                        
                        if detection_data:
                            data = json.loads(detection_data)
                            results.append({
                                "detection_id": detection_id,
                                "timestamp": timestamp,
                                "data": data
                            })
                
                if results:
                    result_text = f"✅ Found {len(results)} LPP detections:\n\n"
                    for i, result in enumerate(results[:5], 1):  # Show first 5
                        result_text += f"{i}. ID: {result['detection_id']}\n"
                        lpp_data = result['data']['lpp_data']
                        result_text += f"   Grade: {lpp_data.get('grade', 'N/A')}\n"
                        result_text += f"   Confidence: {lpp_data.get('confidence', 0):.2f}\n"
                        result_text += f"   Date: {result['data'].get('detected_at', 'N/A')}\n\n"
                    
                    if len(results) > 5:
                        result_text += f"... and {len(results) - 5} more results\n"
                else:
                    result_text = "❌ No LPP detections found matching criteria"
                
                return [TextContent(
                    type="text",
                    text=result_text
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error searching LPP detections: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def get_lpp_statistics(arguments: Dict[str, Any]) -> List[TextContent]:
            """Get LPP detection statistics"""
            try:
                redis_client = await self._get_redis_client()
                stats_key = "vigia:lpp_stats"
                
                # Get all statistics
                stats = await redis_client.hgetall(stats_key)
                
                if not stats:
                    return [TextContent(
                        type="text",
                        text="❌ No statistics available"
                    )]
                
                # Parse statistics
                total_detections = int(stats.get(b"total_detections", 0))
                grade_1_count = int(stats.get(b"grade_1_count", 0))
                grade_2_count = int(stats.get(b"grade_2_count", 0))
                grade_3_count = int(stats.get(b"grade_3_count", 0))
                grade_4_count = int(stats.get(b"grade_4_count", 0))
                
                # Calculate percentages
                def calc_percentage(count, total):
                    return (count / total * 100) if total > 0 else 0
                
                result_text = f"📊 LPP Detection Statistics\n\n"
                result_text += f"Total Detections: {total_detections}\n\n"
                result_text += f"Distribution by Grade:\n"
                result_text += f"  Grade 1: {grade_1_count} ({calc_percentage(grade_1_count, total_detections):.1f}%)\n"
                result_text += f"  Grade 2: {grade_2_count} ({calc_percentage(grade_2_count, total_detections):.1f}%)\n"
                result_text += f"  Grade 3: {grade_3_count} ({calc_percentage(grade_3_count, total_detections):.1f}%)\n"
                result_text += f"  Grade 4: {grade_4_count} ({calc_percentage(grade_4_count, total_detections):.1f}%)\n\n"
                
                # Critical cases (Grade 3+)
                critical_cases = grade_3_count + grade_4_count
                result_text += f"🚨 Critical Cases (Grade 3+): {critical_cases} ({calc_percentage(critical_cases, total_detections):.1f}%)\n"
                
                return [TextContent(
                    type="text",
                    text=result_text
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error getting statistics: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def cache_medical_protocol(arguments: Dict[str, Any]) -> List[TextContent]:
            """Cache medical protocol for quick access"""
            try:
                protocol_id = arguments.get("protocol_id", "")
                protocol_data = arguments.get("protocol_data", {})
                vector_embedding = arguments.get("vector_embedding", [])
                
                if not protocol_id:
                    return [TextContent(
                        type="text",
                        text="❌ Protocol ID is required"
                    )]
                
                redis_client = await self._get_redis_client()
                
                # Cache protocol data
                protocol_key = f"vigia:protocol:{protocol_id}"
                cached_protocol = {
                    "protocol_data": protocol_data,
                    "vector_embedding": vector_embedding,
                    "cached_at": datetime.utcnow().isoformat(),
                    "protocol_id": protocol_id
                }
                
                await redis_client.setex(
                    protocol_key,
                    timedelta(days=7),  # Keep protocols for 1 week
                    json.dumps(cached_protocol)
                )
                
                # Index for search
                protocol_name = protocol_data.get("name", "")
                if protocol_name:
                    search_key = f"vigia:protocol_search:{protocol_name.lower()}"
                    await redis_client.sadd(search_key, protocol_id)
                
                return [TextContent(
                    type="text",
                    text=f"✅ Medical protocol cached successfully\n"
                         f"Protocol ID: {protocol_id}\n"
                         f"Name: {protocol_name}\n"
                         f"Cache TTL: 7 days"
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Error caching medical protocol: {str(e)}"
                )]
        
        @self.server.call_tool()
        async def redis_health_check(arguments: Dict[str, Any]) -> List[TextContent]:
            """Check Redis server health and connection"""
            try:
                redis_client = await self._get_redis_client()
                
                # Test ping
                pong = await redis_client.ping()
                
                # Get server info
                info = await redis_client.info()
                
                # Test set/get
                test_key = "vigia:health_check"
                test_value = datetime.utcnow().isoformat()
                await redis_client.setex(test_key, 60, test_value)
                retrieved_value = await redis_client.get(test_key)
                
                # Get memory usage
                memory_used = info.get("used_memory_human", "Unknown")
                connected_clients = info.get("connected_clients", 0)
                
                result_text = f"✅ Redis Health Check Passed\n\n"
                result_text += f"Connection: {'✅ OK' if pong else '❌ Failed'}\n"
                result_text += f"Set/Get Test: {'✅ OK' if retrieved_value else '❌ Failed'}\n"
                result_text += f"Memory Used: {memory_used}\n"
                result_text += f"Connected Clients: {connected_clients}\n"
                result_text += f"Redis Version: {info.get('redis_version', 'Unknown')}\n"
                
                # Clean up test key
                await redis_client.delete(test_key)
                
                return [TextContent(
                    type="text",
                    text=result_text
                )]
                
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=f"❌ Redis health check failed: {str(e)}"
                )]
    
    def _setup_resources(self):
        """Setup Redis MCP resources"""
        
        @self.server.list_resources()
        async def list_resources() -> ListResourcesResult:
            """List available Redis resources"""
            return ListResourcesResult(
                resources=[
                    Resource(
                        uri="redis://cache-patterns",
                        name="Redis Cache Patterns",
                        description="Common caching patterns for medical data",
                        mimeType="text/markdown"
                    ),
                    Resource(
                        uri="redis://lpp-schema",
                        name="LPP Detection Schema",
                        description="Schema for LPP detection caching",
                        mimeType="application/json"
                    ),
                    Resource(
                        uri="redis://medical-indexes",
                        name="Medical Data Indexes",
                        description="Index strategies for medical data",
                        mimeType="text/markdown"
                    )
                ]
            )
        
        @self.server.read_resource()
        async def read_resource(uri: str) -> ReadResourceResult:
            """Read Redis resource documentation"""
            
            if uri == "redis://cache-patterns":
                patterns_doc = """# Redis Cache Patterns for Medical Data

## Patient Data Caching
- **Key Pattern**: `vigia:patient:{patient_id}`
- **TTL**: 24 hours
- **Content**: Patient demographic and clinical data

## LPP Detection Caching  
- **Key Pattern**: `vigia:lpp_detection:{detection_id}`
- **TTL**: 30 days
- **Content**: Detection results, confidence, metadata

## Medical Protocol Caching
- **Key Pattern**: `vigia:protocol:{protocol_id}`
- **TTL**: 7 days
- **Content**: Protocol data with vector embeddings

## Index Patterns

### LPP Grade Index
- **Key Pattern**: `vigia:lpp_index:grade_{grade}`
- **Type**: Sorted Set (ZSET)
- **Score**: Detection confidence

### Patient Detection Index
- **Key Pattern**: `vigia:lpp_index:patient_{patient_id}`
- **Type**: Sorted Set (ZSET)
- **Score**: Detection timestamp

### Statistics
- **Key Pattern**: `vigia:lpp_stats`
- **Type**: Hash
- **Fields**: grade counts, totals

## Best Practices

1. Always use TTL for medical data
2. Use consistent key naming patterns
3. Index frequently queried data
4. Monitor memory usage
5. Use appropriate data types
"""
                
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=patterns_doc
                        )
                    ]
                )
            
            elif uri == "redis://lpp-schema":
                schema = {
                    "lpp_detection": {
                        "detection_id": "string",
                        "lpp_data": {
                            "grade": "integer (1-4)",
                            "confidence": "float (0.0-1.0)",
                            "anatomical_location": "string",
                            "patient_id": "string"
                        },
                        "image_hash": "string",
                        "detected_at": "ISO datetime",
                        "system_version": "string"
                    },
                    "patient_cache": {
                        "patient_id": "string",
                        "patient_data": {
                            "age": "integer",
                            "gender": "string",
                            "medical_history": "array"
                        },
                        "cached_at": "ISO datetime",
                        "source": "string"
                    }
                }
                
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=json.dumps(schema, indent=2)
                        )
                    ]
                )
            
            else:
                return ReadResourceResult(
                    contents=[
                        TextContent(
                            type="text",
                            text=f"Resource not found: {uri}"
                        )
                    ]
                )


async def main():
    """Main entry point for Vigia Redis MCP Server"""
    
    # Load configuration from environment
    config = RedisConfig(
        url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        password=os.getenv("REDIS_PASSWORD")
    )
    
    # Create and run the server
    redis_server = VigiaRedisServer(config)
    
    # Run the server
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await redis_server.server.run(
            read_stream,
            write_stream,
            redis_server.server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())