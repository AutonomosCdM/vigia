# 🔌 Vigía MCP Integration Template

## Quick Start Guide para Añadir MCPs al Proyecto Vigía

### 📋 Checklist de Integración MCP

#### 1. Configuración Base (.mcp.json)
```json
{
  "mcpServers": {
    "your-mcp-name": {
      "command": "npx",
      "args": ["-y", "your-mcp-package"],
      "description": "Description for medical/Vigía context",
      "env": {
        "API_KEY": "${YOUR_API_KEY}",
        "SECRET": "${YOUR_SECRET}"
      }
    }
  }
}
```

#### 2. Variables de Entorno
```bash
# Añadir a config/.env.mcp
YOUR_API_KEY=your_api_key_here
YOUR_SECRET=your_secret_here

# Añadir a config/.env.example
YOUR_API_KEY=your_api_key_example
YOUR_SECRET=your_secret_example
```

#### 3. Docker Integration
```yaml
# En deploy/docker/docker-compose.mcp-hub.yml
services:
  mcp-your-service:
    image: your-mcp-image
    environment:
      - API_KEY=${YOUR_API_KEY}
      - SECRET=${YOUR_SECRET}
    volumes:
      - ./data/your-service:/data
    networks:
      - vigia-mcp-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 🏥 Compliance Médico

#### HIPAA Requirements
- [ ] PHI data encryption at rest and in transit
- [ ] Access control and audit logging
- [ ] Data retention policies (7 years medical)
- [ ] Emergency access protocols

#### Integration with Vigía ADK
```python
# vigia_detect/agents/adk/your_agent.py
from vigia_detect.agents.adk.base import VigiaBaseAgent
from google.adk.agents import AgentCapability

class YourMCPAgent(VigiaBaseAgent):
    def __init__(self):
        super().__init__(
            agent_id="your_mcp_agent",
            agent_name="Your MCP Agent",
            capabilities=[
                AgentCapability.EXTERNAL_COMMUNICATION,
                AgentCapability.MEDICAL_NOTIFICATION
            ]
        )
    
    async def handle_medical_alert(self, alert_data):
        """Handle medical alerts through MCP"""
        # Your MCP integration logic here
        pass
```

### 🧪 Testing Template

#### Test File Structure
```python
# tests/mcp/test_your_mcp_integration.py
import pytest
from vigia_detect.mcp.your_mcp_client import YourMCPClient

class TestYourMCPIntegration:
    
    @pytest.mark.mcp
    @pytest.mark.asyncio
    async def test_mcp_connection(self):
        """Test MCP server connection"""
        client = YourMCPClient()
        assert await client.health_check()
    
    @pytest.mark.mcp
    @pytest.mark.medical
    @pytest.mark.asyncio 
    async def test_hipaa_compliance(self):
        """Test HIPAA compliance for PHI data"""
        # Test PHI encryption and access control
        pass
    
    @pytest.mark.mcp
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_medical_workflow_integration(self):
        """Test integration with Vigía medical workflows"""
        # Test ADK agent integration
        pass
```

### 📝 Documentation Requirements

#### API Reference
```python
class YourMCPClient:
    """
    MCP Client for [Service Name] integration with Vigía medical system.
    
    Medical Compliance:
    - HIPAA: ✅ PHI encryption and audit trails
    - Evidence-based: ✅ Medical decision integration
    - Emergency protocols: ✅ Critical alert handling
    
    Example:
        client = YourMCPClient()
        await client.send_medical_alert(alert_data)
    """
```

### 🚀 Deployment Checklist

#### Pre-deployment
- [ ] .mcp.json configuration updated
- [ ] Environment variables configured
- [ ] Docker services defined
- [ ] Tests passing (unit, integration, medical)
- [ ] HIPAA compliance verified
- [ ] Documentation updated

#### Post-deployment
- [ ] Health checks passing
- [ ] Audit logs working
- [ ] Medical workflows integrated
- [ ] Emergency protocols tested
- [ ] Performance monitoring active

### 🔧 Available MCPs in Vigía

#### Production Ready
1. **Docker MCP** - Container management
2. **Twilio MCP** - WhatsApp medical notifications
3. **Slack MCP** - Team communication  
4. **Asana MCP** - Project management
5. **GitHub MCP** - Code management
6. **Brave Search MCP** - Web search

#### Configuration Examples
```bash
# Test MCP functionality
npx @your-mcp-package --test

# Validate HIPAA compliance
python scripts/testing/validate_mcp_hipaa.py your-mcp

# Integration test
python -m pytest tests/mcp/test_your_mcp_integration.py -v
```

### 🏃‍♂️ Quick Commands

```bash
# Add new MCP
./scripts/setup/add-mcp.sh your-mcp-name your-mcp-package

# Test MCP integration  
./scripts/testing/test-mcp.sh your-mcp-name

# Deploy MCP
./scripts/deployment/deploy-mcp.sh your-mcp-name

# Monitor MCP health
./scripts/monitoring/mcp-health.sh
```

---

**⚡ YOLO Mode**: Para desarrollo rápido, usar template y saltarse validaciones no críticas. Para producción médica, seguir checklist completo.