# Redis + MedGemma Integration Documentation

## Overview
This document describes the integration between Redis caching/vector search and MedGemma local AI for the Vigia medical system.

## Architecture

### Components
1. **MedGemma Local Client** - On-premise medical AI analysis
2. **Redis Semantic Cache** - Intelligent query caching with TTL
3. **Redis Vector Search** - Medical protocol similarity search
4. **Medical Knowledge Base** - Enhanced protocols for LPP

### Data Flow
```
User Query → Cache Check → Protocol Search → MedGemma Analysis → Cache Storage → Response
```

## Setup Instructions

### Prerequisites
- Python 3.11+
- Redis 7.0+ (local or cloud)
- 16GB+ RAM for MedGemma models
- Ollama (recommended) or Hugging Face access

### Installation

#### 1. Install MedGemma via Ollama (Recommended)
```bash
# Install Ollama and MedGemma
python scripts/setup_medgemma_ollama.py --install-ollama
python scripts/setup_medgemma_ollama.py --model 27b --install
python scripts/setup_medgemma_ollama.py --model 27b --test
```

#### 2. Configure Redis
```bash
# Setup Redis with medical protocols
python scripts/setup_redis_simple.py

# Or for advanced setup with vector indices
python scripts/setup_redis_development.py
```

#### 3. Run Integration Demo
```bash
# Test complete integration
python examples/redis_integration_demo.py
```

## Usage Examples

### Basic Medical Query
```python
from examples.redis_integration_demo import RedisGemmaIntegrationDemo

demo = RedisGemmaIntegrationDemo()
await demo.initialize()

# Process medical query with caching
result = await demo.process_medical_query(
    "Paciente de 75 años con eritema no blanqueable en sacro"
)

print(f"Urgency: {result['urgency']}")
print(f"Recommendations: {result['recommendations']}")
```

### Protocol Search
```python
# Search relevant protocols
protocols = await demo.get_relevant_protocols(
    query="prevención de lesiones por presión",
    category="prevention"
)
```

### MedGemma Analysis
```python
# Direct analysis with MedGemma
analysis = await demo.analyze_with_medgemma(
    query="LPP grado 2 con signos de infección",
    protocols=protocols
)
```

## Configuration

### Environment Variables
```bash
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password
REDIS_SSL=false

# Cache Settings
REDIS_CACHE_TTL=3600  # 1 hour default
REDIS_CACHE_INDEX=lpp_semantic_cache

# Vector Search
REDIS_VECTOR_INDEX=lpp_protocols
REDIS_VECTOR_DIM=768

# MedGemma
MEDGEMMA_ENABLED=true
MEDGEMMA_MODEL=alibayram/medgemma
```

### Medical Protocols Structure
```python
protocol = {
    "id": "lpp_prevention_001",
    "title": "Protocolo de Prevención de LPP",
    "content": "...",
    "category": "prevention|treatment|emergency",
    "urgency": "routine|urgent|emergency",
    "evidence_level": "A|B|C"
}
```

## Testing

### Run Complete Test Suite
```bash
# Execute all tests
./scripts/run_redis_medgemma_tests.sh

# Run specific test
python -m pytest tests/test_redis_medgemma_final.py::TestRedisGemmaIntegration::test_cache_miss_and_hit -v

# Run with coverage
python -m pytest tests/test_redis_medgemma_final.py --cov --cov-report=html
```

### Test Categories
- **Unit Tests**: Cache operations, protocol search, MedGemma analysis
- **Integration Tests**: Complete medical query workflow
- **Medical Scenarios**: Prevention, treatment, emergency cases
- **Error Handling**: Connection failures, invalid data

## Performance Optimization

### Cache Strategy
- **TTL**: 30 minutes for clinical queries, 1 hour for protocols
- **Semantic Matching**: 85% similarity threshold for cache hits
- **Key Hashing**: Consistent hashing for query distribution

### MedGemma Optimization
- **Model Selection**: 4B for quick responses, 27B for complex analysis
- **Batch Processing**: Group similar queries for efficiency
- **Local Caching**: Model weights cached after first load

## Medical Compliance

### Privacy & Security
- **Local Processing**: All AI analysis runs on-premise
- **No External APIs**: MedGemma operates without internet
- **Encrypted Cache**: Redis configured with password + SSL
- **Audit Trail**: All queries logged for compliance

### Medical Standards
- **LPP Grading**: Follows international pressure injury classification
- **Evidence Levels**: Protocols tagged with A/B/C evidence
- **Urgency Classification**: routine/urgent/emergency triaging
- **Human Oversight**: Complex cases flagged for review

## Troubleshooting

### Common Issues

#### Redis Connection Failed
```bash
# Check Redis status
redis-cli ping

# Verify credentials
python scripts/test_redis_connection.py
```

#### MedGemma Not Available
```bash
# Check Ollama installation
ollama list

# Reinstall model
ollama pull alibayram/medgemma
```

#### Cache Miss on Similar Queries
- Adjust similarity threshold (default 0.85)
- Check embedding generation
- Verify query normalization

## API Reference

### RedisGemmaIntegrationDemo
```python
class RedisGemmaIntegrationDemo:
    async def initialize() -> bool
    async def process_medical_query(query: str) -> Dict[str, Any]
    async def get_cached_response(query: str) -> Optional[Dict]
    async def get_relevant_protocols(query: str, category: str = None) -> List[Dict]
    async def analyze_with_medgemma(query: str, protocols: List) -> Dict[str, Any]
    async def cache_response(query: str, response: Dict[str, Any])
```

### Response Format
```json
{
    "query": "original query",
    "analysis": "MedGemma analysis text",
    "recommendations": ["rec1", "rec2", "rec3"],
    "urgency": "routine|moderate|urgent|emergency",
    "confidence": 0.9,
    "protocols_consulted": 3,
    "source": "medgemma|cached|fallback",
    "cache_hit": false,
    "processing_steps": ["cache_lookup", "protocol_search", "medgemma_analysis"]
}
```

## Future Enhancements

### Planned Features
1. **Multi-language Support**: Spanish/English medical terminology
2. **Image Analysis**: Direct DICOM/PNG processing with MedGemma multimodal
3. **Protocol Learning**: Dynamic protocol updates from medical literature
4. **Distributed Caching**: Redis cluster for high availability

### Research Directions
- Fine-tuning MedGemma on institution-specific protocols
- Active learning from clinician feedback
- Integration with medical knowledge graphs
- Real-time protocol updates from medical databases

## References

### Medical Standards
- International NPUAP/EPUAP Pressure Ulcer Guidelines
- Chilean Ministry of Health LPP Protocols
- RNAO Best Practice Guidelines

### Technical Documentation
- [MedGemma Paper](https://arxiv.org/abs/2412.11108)
- [Redis Vector Similarity](https://redis.io/docs/stack/search/reference/vectors/)
- [Ollama Documentation](https://ollama.ai/docs)

## Support

For issues or questions:
- Check `logs/` directory for detailed errors
- Run diagnostics: `python scripts/verify_services.py`
- Review test results: `./scripts/run_redis_medgemma_tests.sh`

---
Last Updated: January 2025
Version: 1.0.0