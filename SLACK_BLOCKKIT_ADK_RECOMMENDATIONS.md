# Slack Block Kit ADK Compliance Recommendations

## Overview
The current Slack Block Kit implementation needs significant refactoring to comply with Google ADK standards used throughout the Vigia project.

## 1. Create SlackBlockKitAgent (HIGH PRIORITY)

Create a new ADK agent to handle all Slack Block Kit operations:

```python
# File: vigia_detect/agents/adk/slack_blockkit.py
"""
Slack Block Kit Agent - Native ADK Implementation
===============================================

WorkflowAgent for Slack Block Kit medical interface workflows.
Handles medical UI generation and interactive component processing.
"""

from google.adk.agents import WorkflowAgent, AgentContext
from google.adk.core.types import AgentCapability
from google.adk.tools import Tool, ToolConfig
from google.adk.workflows import Workflow, WorkflowStep
from google.adk.events import EventHandler, AgentEvent

from .base import VigiaBaseAgent

class SlackBlockKitAgent(VigiaBaseAgent, WorkflowAgent):
    """
    Slack Block Kit medical interface agent using deterministic workflows.
    
    Capabilities:
    - Medical Block Kit component generation
    - Interactive component handling
    - HIPAA-compliant UI rendering
    - Medical workflow UI orchestration
    """
    
    def __init__(self, config=None):
        capabilities = [
            AgentCapability.COMMUNICATION,
            AgentCapability.USER_INTERFACE,
            AgentCapability.NOTIFICATION_MANAGEMENT,
            AgentCapability.WORKFLOW_ORCHESTRATION
        ]
        
        VigiaBaseAgent.__init__(
            self,
            agent_id="vigia-slack-blockkit-agent",
            agent_name="Vigia Slack Block Kit Agent",
            capabilities=capabilities,
            medical_specialties=["slack_interface", "block_kit_components", "medical_ui"],
            config=config
        )
        
        WorkflowAgent.__init__(self, config=config)
```

## 2. Convert to ADK Tools (HIGH PRIORITY)

Transform static methods into proper ADK Tools:

```python
class BlockKitMedicalTool(Tool):
    """ADK Tool for generating medical Block Kit components"""
    
    def __init__(self):
        super().__init__(
            name="generate_medical_blocks",
            description="Generate HIPAA-compliant Slack Block Kit components for medical alerts",
            config=ToolConfig(
                cache_results=True,
                timeout_seconds=10,
                retry_attempts=2
            )
        )
    
    async def execute(self, context: AgentContext) -> Dict[str, Any]:
        """Generate Block Kit components based on medical context"""
        block_type = context.get("block_type")
        medical_data = context.get("medical_data", {})
        
        if block_type == "lpp_alert":
            return self._generate_lpp_alert_blocks(medical_data)
        elif block_type == "patient_history":
            return self._generate_patient_history_blocks(medical_data)
        # ... other block types

class BlockKitInteractionTool(Tool):
    """ADK Tool for handling Block Kit interactions"""
    
    def __init__(self):
        super().__init__(
            name="handle_block_interactions",
            description="Process Slack Block Kit interactive components with medical context",
            config=ToolConfig(timeout_seconds=15)
        )
    
    async def execute(self, context: AgentContext) -> AgentResponse:
        """Handle Block Kit interactions using ADK patterns"""
        interaction_data = context.get("interaction_data", {})
        action_id = interaction_data.get("action_id")
        
        # Return proper AgentResponse instead of dict
        return AgentResponse(
            message_id=context.get("message_id"),
            status="success",
            data=self._process_interaction(action_id, interaction_data)
        )
```

## 3. Implement ADK Event Handling (MEDIUM PRIORITY)

Replace FastAPI webhook handler with ADK EventHandler:

```python
class SlackEventHandler(EventHandler):
    """ADK EventHandler for Slack webhook events"""
    
    def __init__(self, slack_agent: SlackBlockKitAgent):
        super().__init__(
            event_types=["slack_webhook", "block_interaction", "modal_submission"]
        )
        self.slack_agent = slack_agent
    
    async def handle_event(self, event: AgentEvent) -> AgentResponse:
        """Handle Slack events using ADK patterns"""
        
        if event.event_type == "block_interaction":
            return await self._handle_block_interaction(event)
        elif event.event_type == "modal_submission":
            return await self._handle_modal_submission(event)
        
        return AgentResponse(
            message_id=event.event_id,
            status="unhandled",
            data={"event_type": event.event_type}
        )
    
    async def _handle_block_interaction(self, event: AgentEvent) -> AgentResponse:
        """Handle Block Kit button/action interactions"""
        
        # Use agent's tools instead of direct method calls
        context = AgentContext({
            "interaction_data": event.data,
            "message_id": event.event_id
        })
        
        interaction_tool = self.slack_agent.get_tool("handle_block_interactions")
        return await interaction_tool.execute(context)
```

## 4. Update MCP Gateway Integration (HIGH PRIORITY)

Modify MCP gateway to use A2A agent communication:

```python
# In MCPGateway class
async def send_lpp_alert_slack(self, case_id: str, patient_code: str, lpp_grade: int,
                              confidence: float, location: str, service: str, bed: str,
                              channel: str = '#medical-alerts') -> MCPResponse:
    """Send LPP alert using ADK Slack Block Kit agent"""
    
    # Discover Slack Block Kit agent via A2A
    slack_agent = await self.router.discover_medical_agent(
        capability=AgentCapability.USER_INTERFACE,
        specialty="slack_interface"
    )
    
    if not slack_agent:
        return MCPResponse(
            request_id="slack_alert",
            service="slack",
            tool="send_alert",
            status="error",
            error="Slack Block Kit agent not available"
        )
    
    # Send medical message to Slack agent
    medical_data = {
        "case_id": case_id,
        "patient_code": patient_code,
        "lpp_grade": lpp_grade,
        "confidence": confidence,
        "location": location,
        "service": service,
        "bed": bed,
        "channel": channel
    }
    
    response = await self.router.send_medical_message(
        target_agent_id=slack_agent.agent_id,
        message_type="generate_lpp_alert",
        medical_data=medical_data,
        patient_id=patient_code,
        urgency="high" if lpp_grade >= 3 else "medium"
    )
    
    return MCPResponse(
        request_id="slack_alert",
        service="slack",
        tool="send_alert", 
        status="success" if response.get("status") == "success" else "error",
        data=response
    )
```

## 5. Implement ADK Workflows (MEDIUM PRIORITY)

Create workflows for Slack operations:

```python
def create_workflows(self) -> Dict[str, Workflow]:
    """Create Slack Block Kit workflows"""
    
    workflows = {}
    
    # Medical Alert UI Workflow
    medical_alert_ui_workflow = Workflow(
        name="medical_alert_ui_generation",
        description="Workflow for generating medical alert UI components"
    )
    
    medical_alert_ui_workflow.add_steps([
        WorkflowStep("validate_medical_data", self._validate_medical_data),
        WorkflowStep("generate_blocks", self._generate_alert_blocks),
        WorkflowStep("apply_hipaa_compliance", self._apply_hipaa_anonymization),
        WorkflowStep("send_to_slack", self._send_block_kit_message)
    ])
    
    workflows["medical_alert_ui"] = medical_alert_ui_workflow
    
    # Interactive Component Workflow  
    interaction_workflow = Workflow(
        name="block_kit_interaction_handling",
        description="Workflow for processing Block Kit interactions"
    )
    
    interaction_workflow.add_steps([
        WorkflowStep("parse_interaction", self._parse_interaction_data),
        ConditionalStep(
            "route_interaction",
            condition=lambda ctx: ctx.get("interaction_type") == "button",
            true_step=WorkflowStep("handle_button", self._handle_button_interaction),
            false_step=WorkflowStep("handle_modal", self._handle_modal_interaction)
        ),
        WorkflowStep("log_interaction", self._log_interaction_audit)
    ])
    
    workflows["interaction_handling"] = interaction_workflow
    
    return workflows
```

## 6. Update Test Structure (MEDIUM PRIORITY)

Align tests with ADK patterns:

```python
# tests/adk/test_slack_blockkit_agent.py
class TestSlackBlockKitAgent:
    """Test Slack Block Kit agent ADK compliance"""
    
    @pytest.fixture
    def slack_agent(self):
        """Create Slack Block Kit agent for testing"""
        return SlackBlockKitAgent()
    
    async def test_agent_capabilities(self, slack_agent):
        """Test agent has correct capabilities"""
        assert AgentCapability.USER_INTERFACE in slack_agent.capabilities
        assert AgentCapability.COMMUNICATION in slack_agent.capabilities
        assert "slack_interface" in slack_agent.medical_specialties
    
    async def test_medical_block_tool(self, slack_agent):
        """Test medical block generation tool"""
        context = AgentContext({
            "block_type": "lpp_alert",
            "medical_data": {
                "case_id": "TEST_001",
                "lpp_grade": 2,
                "confidence": 0.85
            }
        })
        
        tool = slack_agent.get_tool("generate_medical_blocks")
        result = await tool.execute(context)
        
        assert result["status"] == "success"
        assert "blocks" in result
        assert len(result["blocks"]) >= 6
    
    async def test_a2a_communication(self, slack_agent):
        """Test A2A communication with other medical agents"""
        
        # Test agent discovery
        communication_agent = await slack_agent.discover_medical_agent(
            capability=AgentCapability.COMMUNICATION,
            specialty="clinical_communication"
        )
        
        assert communication_agent is not None
        
        # Test medical message sending
        response = await slack_agent.send_medical_message(
            target_agent_id=communication_agent.agent_id,
            message_type="ui_generation_request",
            medical_data={"case_id": "TEST_001"},
            urgency="medium"
        )
        
        assert response["status"] == "success"
```

## 7. Implementation Priority

### Phase 1 (Week 1) - Core ADK Integration
1. Create `SlackBlockKitAgent` class inheriting from `VigiaBaseAgent` and `WorkflowAgent`
2. Convert Block Kit generation methods to ADK Tools
3. Update MCP gateway to use A2A communication

### Phase 2 (Week 2) - Event Handling & Workflows  
4. Implement ADK EventHandler for Slack webhooks
5. Create ADK Workflows for UI generation and interaction handling
6. Add proper AgentMessage/AgentResponse patterns

### Phase 3 (Week 3) - Testing & Refinement
7. Update test structure to align with ADK testing patterns
8. Add comprehensive ADK compliance tests
9. Refactor remaining direct method calls

## Benefits of ADK Compliance

1. **Consistent Architecture**: Aligns with project's native ADK implementation
2. **Agent Discovery**: Enables other agents to discover Slack capabilities  
3. **A2A Communication**: Proper agent-to-agent medical messaging
4. **Workflow Orchestration**: Deterministic UI generation workflows
5. **Tool Reusability**: Block Kit tools can be used by other agents
6. **Better Testing**: ADK testing patterns provide better coverage
7. **Medical Compliance**: Proper audit trails through ADK agent base

## Current Compliance Score: 3/10
**Target Compliance Score: 9/10** (after implementing recommendations)

The current implementation lacks fundamental ADK patterns but has good medical logic that can be preserved during refactoring.