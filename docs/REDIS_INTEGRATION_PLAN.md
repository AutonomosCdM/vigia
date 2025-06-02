# LPP-Detect Redis Integration Plan
**Implementación de Memory, RAG y Aprendizaje Continuo**

## ARQUITECTURA HÍBRIDA: REDIS + SUPABASE

### PRINCIPIOS FUNDAMENTALES
- **Supabase**: Single source of truth para datos médicos críticos
- **Redis**: Acceleration/AI layer para performance y features inteligentes  
- **No duplicación**: Roles complementarios claramente definidos
- **TTL management**: Datos temporales con expiración automática

---

## COMPONENTES REDIS IDENTIFICADOS

### TIER 1: FOUNDATIONAL COMPONENTS
1. **RedisVL (Redis Vector Library)**
   - Vector search protocolos MINSAL/EPUAP
   - RAG knowledge base médico
   - HNSW indexing para búsqueda semántica

2. **SemanticSessionManager**  
   - Memoria conversacional inteligente
   - Context-aware patient interactions
   - Distance threshold 0.7 para casos similares

3. **LangGraph + Redis Checkpoints**
   - Persistencia automática estados ADK agents
   - Thread-level session management
   - Recovery automático ante fallos

### TIER 2: OPTIMIZATION COMPONENTS
4. **Semantic Caching**
   - 31% reducción queries redundantes
   - Cache responses Gemini API
   - ROI inmediato en costos LLM

5. **Agent Memory Server**
   - Long-term memory management
   - REST + MCP APIs
   - Semantic deduplication automática

6. **Mem0 Integration**
   - Auto-improving memory layer
   - 80% reducción costos LLM
   - User preferences learning

---

## IMPLEMENTACIÓN ESCALONADA

### FASE 1: REDIS MINIMAL (Semana 1-2)
**Objetivo**: Cache básico sin duplicación datos

**Componentes a implementar:**
- [ ] Setup Redis Stack server
- [ ] Semantic caching LLM responses únicamente
- [ ] Vector embeddings protocolos MINSAL (no datos pacientes)
- [ ] TTL 24h para todas las entradas

**Archivos a crear:**
```
lpp_detect/
├── redis_layer/
│   ├── __init__.py
│   ├── cache_service.py          # Semantic caching
│   ├── vector_service.py         # RedisVL para protocolos
│   └── config.py                 # Redis configuration
├── config/
│   └── redis_config.yaml        # Redis settings
└── tests/
    └── test_redis_integration.py
```

**Validación:**
- Cache hit rate >70% para consultas frecuentes
- Vector search latencia <50ms
- Sin duplicación datos Supabase

### FASE 2: SESSION MANAGEMENT (Semana 3-4)  
**Objetivo**: Memoria conversacional inteligente

**Componentes a implementar:**
- [ ] SemanticSessionManager implementation
- [ ] LangGraph Redis checkpoints
- [ ] Auto-sync to Supabase on session close
- [ ] Thread-level persistence ADK agents

**Archivos a crear:**
```
lpp_detect/
├── redis_layer/
│   ├── session_manager.py        # SemanticSessionManager
│   ├── checkpoint_service.py     # LangGraph persistence
│   └── sync_service.py           # Redis↔Supabase sync
├── agents/
│   └── enhanced_lpp_agent.py     # Agent con Redis memory
```

**Validación:**
- Session recovery 100% funcional
- Context preservation across conversations
- Sync automático Supabase sin pérdida datos

### FASE 3: ADVANCED MEMORY (Semana 5-6)
**Objetivo**: Memory server completo y RAG avanzado

**Componentes a implementar:**
- [ ] Agent Memory Server deployment
- [ ] Advanced RAG con RedisVL
- [ ] Semantic deduplication
- [ ] Cross-thread memory management

**Archivos a crear:**
```
lpp_detect/
├── redis_layer/
│   ├── memory_server.py          # Agent Memory Server
│   ├── rag_service.py            # Advanced RAG
│   └── deduplication.py          # Semantic dedup
├── knowledge/
│   ├── medical_protocols/        # MINSAL/EPUAP docs
│   └── embeddings_loader.py     # Protocol vectorization
```

**Validación:**
- RAG accuracy >85% sobre protocolos médicos
- Memory deduplication funcional
- Cross-session context preservation

### FASE 4: PRODUCTION OPTIMIZATION (Semana 7-8)
**Objetivo**: Sistema completo optimizado

**Componentes a implementar:**
- [ ] Mem0 integration
- [ ] Geospatial clinic finder
- [ ] Router allow/block medical queries  
- [ ] Performance monitoring completo

**Archivos a crear:**
```
lpp_detect/
├── redis_layer/
│   ├── mem0_service.py           # Auto-improving memory
│   ├── geo_service.py            # Clinic geospatial
│   ├── router_service.py         # Query routing
│   └── monitoring.py            # Performance metrics
├── deployment/
│   └── redis_monitoring.yaml    # Monitoring config
```

**Validación:**
- Sistema completo funcional end-to-end
- Performance benchmarks achieved
- Cost optimization documented

---

## FLUJO DE DATOS ARQUITECTURA

### HOT PATH (Redis)
```
User Query → Semantic Cache Check → Redis Vector Search → Agent Processing → Cache Result
     ↓
LangGraph Checkpoint → Session Memory → Response Generation → Session Update
```

### COLD PATH (Supabase)  
```
Session End → Persist to Supabase → Clear Redis TTL → Archive Session Data
     ↓
Historical Query → Supabase Query → Load to Redis Cache → Continue Hot Path
```

---

## CONFIGURACIÓN TÉCNICA

### REDIS STACK REQUIREMENTS
```yaml
redis:
  version: "redis/redis-stack:latest"
  memory: "4GB"
  persistence: "RDB + AOF"
  modules:
    - RedisSearch
    - RedisJSON  
    - RedisGraph
    - RedisTimeSeries
```

### INTEGRATION PATTERNS
```python
# Agent enhanced con Redis
lpp_agent = Agent(
    model="gemini-2.0-flash-exp",
    memory_service=RedisMemoryService(),
    cache_service=SemanticCache(),
    session_service=RedisSessionManager(),
    tools=[
        redis_vector_search,      # RAG médico
        semantic_cache_tool,      # Optimización
        memory_retrieval,         # Historial  
        supabase_sync_tool       # Persistence
    ]
)
```

---

## MÉTRICAS DE ÉXITO

### PERFORMANCE TARGETS
- [ ] Cache hit rate: >70%
- [ ] Vector search latency: <50ms
- [ ] Session recovery: <100ms
- [ ] Memory deduplication: >60% reduction

### COST OPTIMIZATION
- [ ] LLM API calls reduction: >30%
- [ ] Query response time: <200ms avg
- [ ] Memory usage efficiency: <2GB Redis

### MEDICAL COMPLIANCE
- [ ] Data consistency: 100% Redis↔Supabase
- [ ] Audit trail preservation: Complete
- [ ] HIPAA compliance: Maintained
- [ ] PHI tokenization: Enforced

---

## DEPENDENCIES & REQUIREMENTS

### Python Packages
```
redisvl>=0.3.0
redis>=5.0.0
mem0ai
sentence-transformers
```

### Infrastructure
- Redis Stack 7.0+
- Supabase instance (existing)
- Vector embedding model (sentence-transformers)
- Monitoring stack (optional)

---

## ROLLBACK PLAN

### Emergency Rollback
1. Disable Redis layer via feature flag
2. Revert to Supabase-only operation
3. Preserve all critical medical data
4. Minimal service disruption

### Data Recovery
- All critical data remains in Supabase
- Redis TTL ensures no data lock-in
- Session data recoverable from audit logs
- Zero data loss guaranteed

---

## NEXT STEPS FOR IMPLEMENTATION

1. **Review and approve** this implementation plan
2. **Setup Redis Stack** development environment  
3. **Begin Fase 1** with semantic caching only
4. **Iterative testing** each phase before proceeding
5. **Production deployment** with gradual rollout

---

**Este documento sirve como guía completa para la implementación Redis en LPP-Detect, manteniendo la integridad del sistema existente mientras agrega capacidades AI avanzadas.**