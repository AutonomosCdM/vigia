# Redis CLI Commands for Vigia

This document contains Redis CLI commands for managing the Vigia medical caching system.

## Connection

```bash
# Local Redis
redis-cli

# Redis Cloud with SSL
redis-cli -h your-host.redislabs.com -p 12345 -a your-password --tls

# With environment variables
redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD --tls
```

## Index Management

### Create Medical Cache Index

```bash
FT.CREATE idx:medical_cache 
  ON HASH 
  PREFIX 1 "cache:medical:" 
  SCHEMA 
    query TEXT NOSTEM 
    response TEXT 
    medical_context TEXT NOSTEM 
    timestamp NUMERIC 
    ttl NUMERIC 
    hit_count NUMERIC 
    embedding VECTOR FLAT 6 
      TYPE FLOAT32 
      DIM 384 
      DISTANCE_METRIC COSINE
```

### Create Medical Protocols Index

```bash
FT.CREATE idx:medical_protocols 
  ON HASH 
  PREFIX 1 "protocol:" 
  SCHEMA 
    title TEXT NOSTEM WEIGHT 2.0 
    content TEXT WEIGHT 1.0 
    source TEXT NOSTEM 
    tags TAG 
    lpp_grades TAG 
    page_number NUMERIC 
    embedding VECTOR HNSW 8 
      TYPE FLOAT32 
      DIM 384 
      DISTANCE_METRIC COSINE 
      M 16 
      EF_CONSTRUCTION 200
```

### Drop Indexes (if needed)

```bash
FT.DROPINDEX idx:medical_cache
FT.DROPINDEX idx:medical_protocols
```

## Index Information

```bash
# Get index info
FT.INFO idx:medical_cache
FT.INFO idx:medical_protocols

# List all indexes
FT._LIST
```

## Data Management

### Add Medical Protocol

```bash
HSET protocol:prevention_001 
  title "Protocolo de Prevención de LPP - MINSAL" 
  content "Las lesiones por presión son áreas de daño..." 
  source "MINSAL Chile 2019" 
  tags "prevention,care,assessment" 
  lpp_grades "grade_0,grade_1" 
  page_number 15
```

### Search Protocols

```bash
# Search by text
FT.SEARCH idx:medical_protocols "prevención" LIMIT 0 5

# Search by tag
FT.SEARCH idx:medical_protocols "@tags:{prevention}" LIMIT 0 5

# Search by grade
FT.SEARCH idx:medical_protocols "@lpp_grades:{grade_2}" LIMIT 0 5

# Combined search
FT.SEARCH idx:medical_protocols "@tags:{treatment} @lpp_grades:{grade_3}" LIMIT 0 5
```

### Vector Search (with embeddings)

```bash
# KNN search (requires actual embedding bytes)
FT.SEARCH idx:medical_protocols 
  "*=>[KNN 5 @embedding $vector AS score]" 
  PARAMS 2 vector "embedding_bytes_here" 
  RETURN 3 title score content 
  SORTBY score 
  LIMIT 0 5 
  DIALECT 2
```

## Cache Management

### View Cache Entries

```bash
# Scan cache keys
SCAN 0 MATCH "cache:medical:*" COUNT 10

# Get specific cache entry
HGETALL cache:medical:some_key

# Count cache entries
FT.SEARCH idx:medical_cache "*" LIMIT 0 0
```

### Cache Statistics

```bash
# Get all keys and calculate stats
EVAL "
  local keys = redis.call('keys', 'cache:medical:*')
  local total_hits = 0
  for i=1,#keys do
    local hits = redis.call('hget', keys[i], 'hit_count')
    if hits then total_hits = total_hits + tonumber(hits) end
  end
  return {#keys, total_hits}
" 0
```

## Monitoring

### Monitor queries in real-time

```bash
MONITOR
```

### Get slow queries

```bash
SLOWLOG GET 10
```

### Memory usage

```bash
INFO memory
MEMORY STATS
```

## Useful Queries

### Find protocols by grade and type

```bash
# Grade 2 treatment protocols
FT.SEARCH idx:medical_protocols 
  "@tags:{treatment} @lpp_grades:{grade_2}" 
  RETURN 2 title content 
  LIMIT 0 3

# All prevention protocols
FT.SEARCH idx:medical_protocols 
  "@tags:{prevention}" 
  RETURN 3 title source tags 
  LIMIT 0 10
```

### Aggregate queries

```bash
# Count protocols by grade
FT.AGGREGATE idx:medical_protocols "*" 
  GROUPBY 1 @lpp_grades 
  REDUCE COUNT 0 AS count 
  SORTBY 2 @count DESC
```

## Maintenance

### Backup index definitions

```bash
# Export index schema
FT.INFO idx:medical_cache > cache_index_schema.txt
FT.INFO idx:medical_protocols > protocols_index_schema.txt
```

### Clear all data (CAUTION!)

```bash
FLUSHDB
```

### Check Redis modules

```bash
MODULE LIST
```

## Python Integration

These commands can be executed from Python:

```python
import redis

r = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)

# Create index
r.execute_command(
    'FT.CREATE', 'idx:test',
    'ON', 'HASH',
    'PREFIX', '1', 'test:',
    'SCHEMA', 'title', 'TEXT'
)

# Search
results = r.execute_command(
    'FT.SEARCH', 'idx:test', 'query'
)
```