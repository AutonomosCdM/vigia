# Redis Setup Guide for Vigia

## Overview

Vigia uses Redis for semantic caching and vector search capabilities. The system can run in two modes:

1. **Production Mode**: With real Redis instance (recommended)
2. **Development Mode**: With mock Redis client (in-memory)

## Development Mode (Mock Client)

By default, if Redis is not configured, the system will use a mock client that simulates Redis behavior in memory. This is useful for:

- Local development without Redis
- Testing functionality
- Demo purposes

```bash
# Run demo with mock client (no Redis required)
python examples/redis_phase2_demo.py
```

## Production Mode (Real Redis)

### Option 1: Redis Cloud (Recommended)

1. **Create a Redis Cloud account**: https://redis.com/try-free/

2. **Create a new database** with:
   - Redis Stack (includes RediSearch)
   - At least 100MB RAM
   - SSL enabled

3. **Get connection details**:
   - Endpoint (host:port)
   - Password
   - SSL requirement

4. **Configure environment**:
   ```bash
   # In vigia_detect/.env
   REDIS_HOST=your-redis-endpoint.redislabs.com
   REDIS_PORT=12345
   REDIS_PASSWORD=your-redis-password
   REDIS_SSL=true
   ```

### Option 2: Local Redis Stack

1. **Install Redis Stack** (includes RediSearch):
   ```bash
   # macOS
   brew tap redis-stack/redis-stack
   brew install redis-stack
   
   # Docker
   docker run -d --name redis-stack \
     -p 6379:6379 \
     redis/redis-stack:latest
   ```

2. **Configure environment**:
   ```bash
   # In vigia_detect/.env
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_PASSWORD=
   REDIS_SSL=false
   ```

### Option 3: Existing Redis with RediSearch

If you have an existing Redis instance, ensure it has RediSearch module installed:

```bash
# Check if RediSearch is available
redis-cli MODULE LIST
```

## Configuration

### Environment Variables

Create or update `vigia_detect/.env`:

```bash
# Redis Connection
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=your-password
REDIS_SSL=true

# Optional: Cache settings
REDIS_CACHE_TTL=3600  # 1 hour
REDIS_CACHE_INDEX=lpp_semantic_cache
REDIS_VECTOR_INDEX=lpp_protocols
```

### Test Connection

```bash
# Test Redis connection
python scripts/test_redis_connection.py

# If successful, run migration
python scripts/migrate_redis_phase2.py
```

## Features by Mode

| Feature | Mock Mode | Redis Mode |
|---------|-----------|------------|
| Semantic Caching | ✓ (in-memory) | ✓ (persistent) |
| Vector Search | ✓ (simulated) | ✓ (full HNSW) |
| Protocol Indexing | ✓ (limited) | ✓ (unlimited) |
| Persistence | ✗ | ✓ |
| Distributed | ✗ | ✓ |
| Performance | Limited | High |

## Troubleshooting

### "Connection refused" error
- Check if Redis is running: `redis-cli ping`
- Verify host and port in configuration
- Check firewall settings

### "Auth failed" error
- Verify password is correct
- For Redis Cloud, ensure using the database password, not account password

### "SSL required" error
- Set `REDIS_SSL=true` for Redis Cloud
- Set `REDIS_SSL=false` for local Redis

### Mock client being used unexpectedly
- Check environment variables are loaded
- Verify `.env` file location
- Test connection with `scripts/test_redis_connection.py`

## Performance Tips

1. **For production**, use Redis Cloud or dedicated Redis instance
2. **Index medical protocols** during off-peak hours
3. **Monitor cache hit rate** to optimize similarity threshold
4. **Use connection pooling** for high-traffic scenarios

## Next Steps

1. Configure Redis connection
2. Run migration script to index protocols
3. Test with demo script
4. Integrate into your workflow

For more details, see [Redis Phase 2 Documentation](REDIS_PHASE2_DOCS.md).