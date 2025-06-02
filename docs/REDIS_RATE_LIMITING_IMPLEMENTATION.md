# Redis Rate Limiting Implementation Plan

## Overview

This document outlines the implementation of Redis-based rate limiting for the Vigia system to protect against abuse and ensure system stability.

## Current State

- **No rate limiting** currently implemented
- Redis infrastructure exists but only used for caching
- Test expectations exist but no actual implementation
- Vulnerable endpoints: webhook server, WhatsApp server, API endpoints

## Implementation Strategy

### Phase 1: Core Rate Limiter (Week 1)

#### 1. Redis Rate Limiter Service

```python
# vigia_detect/redis_layer/rate_limiter.py
from datetime import datetime, timedelta
from typing import Optional, Tuple
import redis.asyncio as redis
from vigia_detect.redis_layer.config import get_redis_settings

class RateLimiter:
    """Redis-based rate limiter using sliding window algorithm"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        
    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
        cost: int = 1
    ) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit
        
        Args:
            key: Unique identifier (e.g., "rate_limit:api:{ip}")
            limit: Maximum requests allowed
            window: Time window in seconds
            cost: Cost of this request (default 1)
            
        Returns:
            (allowed, remaining, reset_time)
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=window)
        
        pipe = self.redis.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start.timestamp())
        
        # Count current requests
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {f"{now.timestamp()}:{id(now)}": now.timestamp()})
        
        # Set expiry
        pipe.expire(key, window)
        
        results = await pipe.execute()
        current_count = results[1]
        
        if current_count + cost > limit:
            return False, 0, int(now.timestamp()) + window
            
        remaining = limit - current_count - cost
        return True, remaining, int(now.timestamp()) + window
```

#### 2. FastAPI Middleware

```python
# vigia_detect/middleware/rate_limit.py
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
import ipaddress

class RateLimitMiddleware:
    """FastAPI rate limiting middleware"""
    
    def __init__(self, app, rate_limiter: RateLimiter):
        self.app = app
        self.rate_limiter = rate_limiter
        
    async def __call__(self, request: Request, call_next):
        # Extract client IP
        client_ip = self.get_client_ip(request)
        
        # Define rate limits by endpoint
        limits = self.get_endpoint_limits(request.url.path)
        
        # Check rate limit
        key = f"rate_limit:{request.url.path}:{client_ip}"
        allowed, remaining, reset = await self.rate_limiter.check_rate_limit(
            key, 
            limits["requests"], 
            limits["window"]
        )
        
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": reset
                },
                headers={
                    "X-RateLimit-Limit": str(limits["requests"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset),
                    "Retry-After": str(reset)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limits["requests"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset)
        
        return response
```

### Phase 2: Integration (Week 2)

#### 1. Webhook Server Protection

```python
# Update webhook server
from vigia_detect.redis_layer.rate_limiter import RateLimiter
from vigia_detect.middleware.rate_limit import RateLimitMiddleware

# In server setup
rate_limiter = RateLimiter(redis_client)
app.add_middleware(RateLimitMiddleware, rate_limiter=rate_limiter)
```

#### 2. WhatsApp Server Protection

```python
# Flask rate limiting decorator
from functools import wraps
from flask import request, jsonify

def rate_limit(limit=60, window=60):
    def decorator(f):
        @wraps(f)
        async def decorated_function(*args, **kwargs):
            client_ip = request.remote_addr
            key = f"rate_limit:whatsapp:{client_ip}"
            
            allowed, remaining, reset = await rate_limiter.check_rate_limit(
                key, limit, window
            )
            
            if not allowed:
                return jsonify({
                    "error": "Rate limit exceeded",
                    "retry_after": reset
                }), 429
                
            return await f(*args, **kwargs)
        return decorated_function
    return decorator
```

### Phase 3: Advanced Features (Week 3)

#### 1. Tiered Rate Limiting

```python
class TieredRateLimiter(RateLimiter):
    """Rate limiter with different tiers"""
    
    TIERS = {
        "anonymous": {"requests": 60, "window": 3600},
        "authenticated": {"requests": 600, "window": 3600},
        "premium": {"requests": 6000, "window": 3600}
    }
    
    async def check_tiered_limit(self, user_tier: str, endpoint: str, identifier: str):
        tier_config = self.TIERS.get(user_tier, self.TIERS["anonymous"])
        key = f"rate_limit:{user_tier}:{endpoint}:{identifier}"
        return await self.check_rate_limit(
            key,
            tier_config["requests"],
            tier_config["window"]
        )
```

#### 2. Distributed Rate Limiting

```python
# For multi-instance deployments
class DistributedRateLimiter(RateLimiter):
    """Rate limiter for distributed systems"""
    
    async def check_global_rate_limit(self, key: str, limit: int, window: int):
        """Uses Redis Lua script for atomic operations"""
        lua_script = """
        local key = KEYS[1]
        local limit = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        
        -- Clean old entries
        redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
        
        -- Count current
        local current = redis.call('ZCARD', key)
        
        if current < limit then
            redis.call('ZADD', key, now, now)
            redis.call('EXPIRE', key, window)
            return {1, limit - current - 1}
        else
            return {0, 0}
        end
        """
        
        result = await self.redis.eval(
            lua_script, 1, key, limit, window, datetime.now().timestamp()
        )
        return result[0] == 1, result[1], int(datetime.now().timestamp()) + window
```

## Configuration

### Environment Variables

```bash
# Rate limiting configuration
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REDIS_DB=1  # Separate DB for rate limits

# Default limits
RATE_LIMIT_DEFAULT_REQUESTS=60
RATE_LIMIT_DEFAULT_WINDOW=60

# Endpoint-specific limits
RATE_LIMIT_WEBHOOK_REQUESTS=100
RATE_LIMIT_WEBHOOK_WINDOW=60
RATE_LIMIT_WHATSAPP_REQUESTS=30
RATE_LIMIT_WHATSAPP_WINDOW=60
RATE_LIMIT_IMAGE_REQUESTS=10
RATE_LIMIT_IMAGE_WINDOW=60
```

### Settings Update

```python
# config/settings.py additions
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(True, env="RATE_LIMIT_ENABLED")
    rate_limit_redis_db: int = Field(1, env="RATE_LIMIT_REDIS_DB")
    rate_limit_default_requests: int = Field(60, env="RATE_LIMIT_DEFAULT_REQUESTS")
    rate_limit_default_window: int = Field(60, env="RATE_LIMIT_DEFAULT_WINDOW")
    
    # Endpoint-specific
    rate_limit_webhook_requests: int = Field(100, env="RATE_LIMIT_WEBHOOK_REQUESTS")
    rate_limit_webhook_window: int = Field(60, env="RATE_LIMIT_WEBHOOK_WINDOW")
    rate_limit_whatsapp_requests: int = Field(30, env="RATE_LIMIT_WHATSAPP_REQUESTS")
    rate_limit_whatsapp_window: int = Field(60, env="RATE_LIMIT_WHATSAPP_WINDOW")
```

## Testing Strategy

### Unit Tests

```python
# tests/test_rate_limiter.py
async def test_rate_limit_allows_under_limit():
    limiter = RateLimiter(redis_client)
    
    for i in range(10):
        allowed, remaining, _ = await limiter.check_rate_limit(
            "test_key", limit=10, window=60
        )
        assert allowed
        assert remaining == 9 - i

async def test_rate_limit_blocks_over_limit():
    limiter = RateLimiter(redis_client)
    
    # Exhaust limit
    for _ in range(10):
        await limiter.check_rate_limit("test_key", limit=10, window=60)
    
    # Next request should be blocked
    allowed, remaining, _ = await limiter.check_rate_limit(
        "test_key", limit=10, window=60
    )
    assert not allowed
    assert remaining == 0
```

### Integration Tests

```python
# tests/integration/test_rate_limit_integration.py
async def test_webhook_rate_limiting():
    # Make requests up to limit
    for _ in range(100):
        response = await client.post("/webhook/events")
        assert response.status_code == 200
    
    # Next request should be rate limited
    response = await client.post("/webhook/events")
    assert response.status_code == 429
    assert "retry_after" in response.json()
```

## Monitoring

### Metrics to Track

1. **Rate Limit Hits**: Count of requests blocked
2. **Usage Patterns**: Requests per endpoint per time window
3. **Abuse Detection**: IPs hitting rate limits frequently
4. **Performance Impact**: Latency added by rate limiting

### Prometheus Metrics

```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram

rate_limit_hits = Counter(
    'vigia_rate_limit_hits_total',
    'Total number of rate limited requests',
    ['endpoint', 'ip']
)

rate_limit_check_duration = Histogram(
    'vigia_rate_limit_check_duration_seconds',
    'Time spent checking rate limits'
)
```

## Rollout Plan

1. **Week 1**: Implement core rate limiter and tests
2. **Week 2**: Integrate with webhook and WhatsApp servers
3. **Week 3**: Add monitoring and advanced features
4. **Week 4**: Production deployment with conservative limits
5. **Week 5**: Tune limits based on real usage data

## Security Considerations

1. **IP Spoofing**: Use proper IP extraction considering proxies
2. **Distributed Attacks**: Implement global rate limits
3. **Bypass Prevention**: Rate limit by both IP and API key
4. **Error Disclosure**: Don't reveal internal limits to attackers

## Performance Optimization

1. **Redis Pipeline**: Batch operations for efficiency
2. **Lua Scripts**: Atomic operations for consistency
3. **Connection Pooling**: Reuse Redis connections
4. **Async Operations**: Non-blocking rate limit checks

## Next Steps

1. Review and approve implementation plan
2. Set up development environment for testing
3. Implement Phase 1 core functionality
4. Create comprehensive test suite
5. Document API changes for clients