"""
Workflow Orchestration Agent - Native ADK Implementation
=======================================================

Master WorkflowAgent for coordinating the complete medical analysis pipeline.
Orchestrates all other agents using deterministic workflows and A2A communication.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

from google.adk.agents import WorkflowAgent, AgentContext
from google.adk.core.types import AgentCapability
from google.adk.tools import Tool
from google.adk.workflows import Workflow, WorkflowStep, ConditionalStep, ParallelStep, SequentialStep

from .base import VigiaBaseAgent

logger = logging.getLogger(__name__)


class MedicalWorkflowType(Enum):
    """Types of medical workflows."""
    EMERGENCY_LPP_DETECTION = "emergency_lpp_detection"
    ROUTINE_ASSESSMENT = "routine_assessment"
    FOLLOW_UP_EVALUATION = "follow_up_evaluation"
    PROTOCOL_CONSULTATION = "protocol_consultation"
    CARE_COORDINATION = "care_coordination"


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"


class WorkflowOrchestrationAgent(VigiaBaseAgent, WorkflowAgent):
    """
    Master orchestration agent for medical workflows.
    
    Capabilities:
    - End-to-end medical case processing workflows
    - Multi-agent coordination using A2A protocol
    - Adaptive workflow routing based on medical urgency
    - Comprehensive audit trails and compliance tracking
    """
    
    def __init__(self, config=None):
        """Initialize Workflow Orchestration Agent."""
        
        capabilities = [
            AgentCapability.WORKFLOW_ORCHESTRATION,
            AgentCapability.MULTI_AGENT_COORDINATION,
            AgentCapability.MEDICAL_CASE_MANAGEMENT,
            AgentCapability.PROCESS_AUTOMATION
        ]
        
        # Initialize both base classes
        VigiaBaseAgent.__init__(
            self,
            agent_id="vigia-workflow-orchestration",
            agent_name="Vigia Medical Workflow Orchestrator",
            capabilities=capabilities,
            medical_specialties=["workflow_management", "case_coordination", "process_automation"],
            config=config
        )
        
        WorkflowAgent.__init__(self, config=config)
        
        # Workflow execution tracking
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_templates = self._initialize_workflow_templates()
        
        # Agent coordination registry
        self.agent_registry = {
            "image_analysis": "vigia-image-analysis",
            "clinical_assessment": "vigia-clinical-assessment", 
            "protocol_consultation": "vigia-protocol-agent",
            "communication": "vigia-communication-agent"
        }
        
        # Medical workflow SLAs (Service Level Agreements)
        self.workflow_slas = {
            MedicalWorkflowType.EMERGENCY_LPP_DETECTION: {
                "max_duration_minutes": 15,
                "escalation_threshold_minutes": 10,
                "priority": "critical"
            },
            MedicalWorkflowType.ROUTINE_ASSESSMENT: {
                "max_duration_minutes": 60,
                "escalation_threshold_minutes": 45,
                "priority": "medium"
            },
            MedicalWorkflowType.FOLLOW_UP_EVALUATION: {
                "max_duration_minutes": 30,
                "escalation_threshold_minutes": 25,
                "priority": "medium"
            }
        }
        
        logger.info("Workflow Orchestration Agent initialized with medical pipeline coordination")
    
    def _initialize_workflow_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize medical workflow templates."""
        return {
            "complete_lpp_analysis": {
                "name": "Complete LPP Analysis Pipeline",
                "description": "End-to-end pressure injury detection and clinical assessment",
                "steps": [
                    {"agent": "image_analysis", "action": "analyze_lpp_image", "timeout_minutes": 5},
                    {"agent": "clinical_assessment", "action": "assess_lpp_grade", "timeout_minutes": 10},
                    {"agent": "protocol_consultation", "action": "search_medical_protocols", "timeout_minutes": 5},
                    {"agent": "communication", "action": "send_medical_notification", "timeout_minutes": 2}
                ],
                "escalation_conditions": [
                    "lpp_grade >= 3",
                    "confidence < 0.6",
                    "step_timeout"
                ]
            },
            "urgent_lpp_intervention": {
                "name": "Urgent LPP Intervention Workflow",
                "description": "Expedited workflow for high-grade pressure injuries",
                "steps": [
                    {"agent": "image_analysis", "action": "analyze_lpp_image", "timeout_minutes": 3},
                    {"agent": "clinical_assessment", "action": "assess_lpp_grade", "timeout_minutes": 5, "parallel": True},
                    {"agent": "protocol_consultation", "action": "search_medical_protocols", "timeout_minutes": 3, "parallel": True},
                    {"agent": "communication", "action": "send_medical_notification", "timeout_minutes": 1, "priority": "emergency"}
                ],
                "auto_escalation": True,
                "requires_immediate_response": True
            },
            "preventive_assessment": {
                "name": "Preventive Care Assessment",
                "description": "Proactive assessment for at-risk patients",
                "steps": [
                    {"agent": "image_analysis", "action": "get_image_quality_metrics", "timeout_minutes": 2},
                    {"agent": "clinical_assessment", "action": "assess_risk_factors", "timeout_minutes": 8},
                    {"agent": "protocol_consultation", "action": "search_prevention_protocols", "timeout_minutes": 5},
                    {"agent": "communication", "action": "schedule_follow_up_notifications", "timeout_minutes": 2}
                ],
                "frequency": "daily",
                "prevention_focused": True
            }
        }
    
    def create_workflows(self) -> Dict[str, Workflow]:
        """Create medical orchestration workflows."""
        
        workflows = {}
        
        # Complete LPP Analysis Workflow
        lpp_analysis_workflow = Workflow(
            name="complete_lpp_analysis",
            description="End-to-end pressure injury analysis with multi-agent coordination"
        )
        
        # Step 1: Image Analysis (always first)
        image_analysis_step = WorkflowStep(
            name="image_analysis",
            function=self._execute_image_analysis,
            description="Analyze medical image for pressure injury detection",
            timeout_minutes=5
        )
        
        # Step 2: Conditional clinical assessment based on detection
        clinical_assessment_step = ConditionalStep(
            name="clinical_assessment_decision",
            condition=lambda context: context.get("lpp_detected", False),
            true_step=WorkflowStep("clinical_assessment", self._execute_clinical_assessment),
            false_step=WorkflowStep("preventive_assessment", self._execute_preventive_assessment),
            description="Route to clinical assessment or preventive care based on detection"
        )
        
        # Step 3: Parallel protocol and communication (for efficiency)
        parallel_step = ParallelStep(
            name="protocol_and_communication",
            steps=[
                WorkflowStep("protocol_consultation", self._execute_protocol_consultation),
                WorkflowStep("communication_preparation", self._prepare_notifications)
            ],
            description="Execute protocol consultation and prepare communications in parallel"
        )
        
        # Step 4: Final notification and documentation
        finalization_step = SequentialStep(
            name="finalization",
            steps=[
                WorkflowStep("send_notifications", self._execute_notifications),
                WorkflowStep("update_medical_record", self._update_medical_records),
                WorkflowStep("schedule_follow_up", self._schedule_follow_up)
            ],
            description="Complete workflow with notifications and documentation"
        )
        
        lpp_analysis_workflow.add_steps([
            image_analysis_step,
            clinical_assessment_step,
            parallel_step,
            finalization_step
        ])
        
        workflows["lpp_analysis"] = lpp_analysis_workflow
        
        # Emergency Escalation Workflow
        emergency_workflow = Workflow(
            name="emergency_lpp_intervention",
            description="Expedited workflow for critical pressure injury cases"
        )
        
        # Emergency workflow with immediate parallel execution
        emergency_parallel = ParallelStep(
            name="emergency_parallel_assessment",
            steps=[
                WorkflowStep("urgent_image_analysis", self._execute_urgent_image_analysis),
                WorkflowStep("immediate_clinical_alert", self._send_immediate_clinical_alert)
            ],
            description="Parallel urgent analysis and immediate alerting"
        )
        
        emergency_workflow.add_steps([
            emergency_parallel,
            WorkflowStep("emergency_protocol_consultation", self._execute_emergency_protocols),
            WorkflowStep("escalate_to_specialists", self._escalate_to_medical_specialists)
        ])
        
        workflows["emergency_intervention"] = emergency_workflow
        
        # Routine Monitoring Workflow
        monitoring_workflow = Workflow(
            name="routine_monitoring",
            description="Scheduled monitoring workflow for ongoing cases"
        )
        
        monitoring_workflow.add_steps([
            WorkflowStep("collect_monitoring_data", self._collect_monitoring_data),
            WorkflowStep("assess_progress", self._assess_healing_progress),
            ConditionalStep(
                "progress_evaluation",
                condition=lambda ctx: ctx.get("healing_progress") == "improving",
                true_step=WorkflowStep("continue_current_plan", self._continue_current_care_plan),
                false_step=WorkflowStep("escalate_care", self._escalate_care_plan)
            ),
            WorkflowStep("update_care_team", self._update_care_team)
        ])
        
        workflows["routine_monitoring"] = monitoring_workflow
        
        return workflows
    
    def create_tools(self) -> List[Tool]:
        """Create workflow orchestration tools."""
        
        tools = super().create_medical_tools()
        
        def execute_medical_workflow(
            workflow_type: str,
            patient_id: str,
            medical_case_data: dict,
            priority: str = "medium",
            custom_parameters: dict = None
        ) -> dict:
            """Execute a complete medical workflow with multi-agent coordination.
            
            Args:
                workflow_type: Type of medical workflow to execute
                patient_id: Patient identifier
                medical_case_data: Medical case data and context
                priority: Workflow execution priority
                custom_parameters: Optional custom workflow parameters
                
            Returns:
                dict: Workflow execution results and outcomes
            """
            try:
                # Generate unique workflow execution ID
                workflow_id = f"wf_{workflow_type}_{patient_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Initialize workflow tracking
                self.active_workflows[workflow_id] = {
                    "workflow_type": workflow_type,
                    "patient_id": patient_id,
                    "status": WorkflowStatus.PENDING,
                    "started_at": datetime.now().isoformat(),
                    "steps_completed": [],
                    "current_step": None,
                    "priority": priority
                }
                
                # Determine workflow based on medical urgency
                actual_workflow_type = self._determine_workflow_type(
                    workflow_type, medical_case_data, priority
                )
                
                # Get appropriate workflow
                workflows = self.create_workflows()
                workflow = workflows.get(actual_workflow_type)
                
                if not workflow:
                    return {
                        "status": "error",
                        "error": f"Workflow type {actual_workflow_type} not found"
                    }
                
                # Prepare workflow context
                workflow_context = AgentContext({
                    "workflow_id": workflow_id,
                    "patient_id": patient_id,
                    "medical_case_data": medical_case_data,
                    "priority": priority,
                    "custom_parameters": custom_parameters or {},
                    "agent_registry": self.agent_registry
                })
                
                # Execute workflow
                self.active_workflows[workflow_id]["status"] = WorkflowStatus.RUNNING
                workflow_result = self._execute_workflow_with_monitoring(workflow, workflow_context)
                
                # Update workflow status
                if workflow_result.get("status") == "success":
                    self.active_workflows[workflow_id]["status"] = WorkflowStatus.COMPLETED
                else:
                    self.active_workflows[workflow_id]["status"] = WorkflowStatus.FAILED
                
                self.active_workflows[workflow_id]["completed_at"] = datetime.now().isoformat()
                self.active_workflows[workflow_id]["result"] = workflow_result
                
                return {
                    "status": "success",
                    "workflow_id": workflow_id,
                    "workflow_type": actual_workflow_type,
                    "execution_result": workflow_result,
                    "duration_minutes": self._calculate_workflow_duration(workflow_id),
                    "sla_compliance": self._check_sla_compliance(workflow_id, actual_workflow_type)
                }
                
            except Exception as e:
                logger.error(f"Error executing medical workflow: {e}")
                if workflow_id in self.active_workflows:
                    self.active_workflows[workflow_id]["status"] = WorkflowStatus.FAILED
                    self.active_workflows[workflow_id]["error"] = str(e)
                
                return {"status": "error", "error": str(e)}
        
        tools.append(Tool(
            name="execute_medical_workflow",
            function=execute_medical_workflow,
            description="Execute complete medical workflow with multi-agent coordination"
        ))
        
        def monitor_active_workflows(patient_id: str = None) -> dict:
            """Monitor status of active medical workflows.
            
            Args:
                patient_id: Optional patient ID to filter workflows
                
            Returns:
                dict: Status of active workflows
            """
            try:
                active_workflows = {}
                overdue_workflows = []
                
                for workflow_id, workflow_data in self.active_workflows.items():
                    # Filter by patient if specified
                    if patient_id and workflow_data.get("patient_id") != patient_id:
                        continue
                    
                    # Check if workflow is still running
                    if workflow_data["status"] in [WorkflowStatus.RUNNING, WorkflowStatus.PENDING]:
                        active_workflows[workflow_id] = {
                            "patient_id": workflow_data["patient_id"],
                            "workflow_type": workflow_data["workflow_type"],
                            "status": workflow_data["status"].value,
                            "duration_minutes": self._calculate_workflow_duration(workflow_id),
                            "current_step": workflow_data.get("current_step"),
                            "priority": workflow_data.get("priority", "medium")
                        }
                        
                        # Check for overdue workflows
                        if self._is_workflow_overdue(workflow_id):
                            overdue_workflows.append(workflow_id)
                
                return {
                    "status": "success",
                    "active_workflows_count": len(active_workflows),
                    "active_workflows": active_workflows,
                    "overdue_workflows": overdue_workflows,
                    "monitoring_timestamp": datetime.now().isoformat()
                }
                
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        tools.append(Tool(
            name="monitor_active_workflows",
            function=monitor_active_workflows,
            description="Monitor status and performance of active medical workflows"
        ))
        
        def escalate_workflow(
            workflow_id: str,
            escalation_reason: str,
            escalation_level: str = "high"
        ) -> dict:
            """Escalate a medical workflow due to issues or delays.
            
            Args:
                workflow_id: Workflow identifier to escalate
                escalation_reason: Reason for escalation
                escalation_level: Level of escalation (medium, high, critical)
                
            Returns:
                dict: Escalation handling results
            """
            try:
                if workflow_id not in self.active_workflows:
                    return {
                        "status": "error",
                        "error": f"Workflow {workflow_id} not found"
                    }
                
                workflow_data = self.active_workflows[workflow_id]
                
                # Update workflow status
                workflow_data["status"] = WorkflowStatus.ESCALATED
                workflow_data["escalation"] = {
                    "reason": escalation_reason,
                    "level": escalation_level,
                    "escalated_at": datetime.now().isoformat()
                }
                
                # Execute escalation workflow
                escalation_result = self._execute_escalation_workflow(
                    workflow_id, escalation_reason, escalation_level
                )
                
                return {
                    "status": "success",
                    "workflow_id": workflow_id,
                    "escalation_level": escalation_level,
                    "escalation_result": escalation_result
                }
                
            except Exception as e:
                return {"status": "error", "error": str(e)}
        
        tools.append(Tool(
            name="escalate_workflow",
            function=escalate_workflow,
            description="Escalate medical workflow due to issues or critical conditions"
        ))
        
        return tools
    
    # Workflow execution methods
    async def _execute_image_analysis(self, context: AgentContext) -> Dict[str, Any]:
        """Execute image analysis step via A2A communication."""
        
        medical_case_data = context.get("medical_case_data", {})
        image_path = medical_case_data.get("image_path")
        patient_id = context.get("patient_id")
        
        if not image_path:
            return {"status": "error", "error": "No image path provided"}
        
        # Send A2A message to image analysis agent
        image_agent_id = self.agent_registry["image_analysis"]
        
        response = await self.send_medical_message(
            image_agent_id,
            "process_medical_case",
            {
                "case_id": context.get("workflow_id"),
                "patient_data": {
                    "image_path": image_path,
                    "patient_id": patient_id
                }
            },
            patient_id=patient_id,
            urgency=context.get("priority", "medium")
        )
        
        # Process response
        analysis_result = response.get("analysis", {})
        lpp_detected = analysis_result.get("lpp_detected", False)
        lpp_grade = analysis_result.get("lpp_grade", 0)
        
        # Update context for next steps
        context.update({
            "lpp_detected": lpp_detected,
            "lpp_grade": lpp_grade,
            "image_analysis_result": response
        })
        
        return {
            "status": "success",
            "lpp_detected": lpp_detected,
            "lpp_grade": lpp_grade,
            "analysis_result": response
        }
    
    async def _execute_clinical_assessment(self, context: AgentContext) -> Dict[str, Any]:
        """Execute clinical assessment step via A2A communication."""
        
        # Send to clinical assessment agent
        clinical_agent_id = self.agent_registry["clinical_assessment"]
        
        response = await self.send_medical_message(
            clinical_agent_id,
            "process_medical_case",
            {
                "case_id": context.get("workflow_id"),
                "patient_data": {
                    "image_analysis": context.get("image_analysis_result", {}),
                    "patient_history": context.get("medical_case_data", {}).get("patient_history", {}),
                    "patient_id": context.get("patient_id")
                }
            },
            patient_id=context.get("patient_id"),
            urgency="high" if context.get("lpp_grade", 0) >= 3 else "medium"
        )
        
        context.update({"clinical_assessment_result": response})
        
        return {"status": "success", "assessment_result": response}
    
    async def _execute_protocol_consultation(self, context: AgentContext) -> Dict[str, Any]:
        """Execute protocol consultation step via A2A communication."""
        
        # Send to protocol agent
        protocol_agent_id = self.agent_registry["protocol_consultation"]
        
        response = await self.send_medical_message(
            protocol_agent_id,
            "process_medical_case",
            {
                "case_id": context.get("workflow_id"),
                "patient_data": {
                    "consultation_request": {
                        "lpp_grade": context.get("lpp_grade", 0),
                        "requires_advanced_protocols": context.get("lpp_grade", 0) >= 2
                    },
                    "patient_context": context.get("medical_case_data", {}).get("patient_history", {}),
                    "patient_id": context.get("patient_id")
                }
            },
            patient_id=context.get("patient_id"),
            urgency="medium"
        )
        
        context.update({"protocol_consultation_result": response})
        
        return {"status": "success", "protocol_result": response}
    
    async def _execute_notifications(self, context: AgentContext) -> Dict[str, Any]:
        """Execute notification step via A2A communication."""
        
        # Send to communication agent
        comm_agent_id = self.agent_registry["communication"]
        
        # Determine notification type based on results
        lpp_grade = context.get("lpp_grade", 0)
        if lpp_grade >= 3:
            notification_type = "escalation_alert"
        elif lpp_grade >= 1:
            notification_type = "lpp_detection_alert"
        else:
            notification_type = "routine_update"
        
        response = await self.send_medical_message(
            comm_agent_id,
            "process_medical_case",
            {
                "case_id": context.get("workflow_id"),
                "patient_data": {
                    "communication_request": {
                        "type": notification_type,
                        "priority": "critical" if lpp_grade >= 4 else "high" if lpp_grade >= 3 else "medium"
                    },
                    "medical_data": {
                        "lpp_grade": lpp_grade,
                        "case_id": context.get("workflow_id"),
                        "image_analysis": context.get("image_analysis_result", {}),
                        "clinical_assessment": context.get("clinical_assessment_result", {}),
                        "protocols": context.get("protocol_consultation_result", {})
                    },
                    "patient_id": context.get("patient_id")
                }
            },
            patient_id=context.get("patient_id"),
            urgency="critical" if lpp_grade >= 4 else "high"
        )
        
        return {"status": "success", "notification_result": response}
    
    def _determine_workflow_type(
        self,
        requested_type: str,
        medical_case_data: dict,
        priority: str
    ) -> str:
        """Determine actual workflow type based on medical urgency."""
        
        # Check for emergency conditions
        if priority == "critical" or priority == "emergency":
            return "emergency_intervention"
        
        # Check medical data for urgency indicators
        patient_history = medical_case_data.get("patient_history", {})
        if (patient_history.get("high_risk", False) or 
            patient_history.get("critical_condition", False)):
            return "emergency_intervention"
        
        # Default to requested type or routine
        return requested_type if requested_type in ["lpp_analysis", "routine_monitoring"] else "lpp_analysis"
    
    def _calculate_workflow_duration(self, workflow_id: str) -> float:
        """Calculate workflow duration in minutes."""
        
        workflow_data = self.active_workflows.get(workflow_id, {})
        started_at = workflow_data.get("started_at")
        
        if not started_at:
            return 0.0
        
        start_time = datetime.fromisoformat(started_at)
        duration = datetime.now() - start_time
        
        return duration.total_seconds() / 60.0
    
    def _is_workflow_overdue(self, workflow_id: str) -> bool:
        """Check if workflow is overdue based on SLA."""
        
        workflow_data = self.active_workflows.get(workflow_id, {})
        workflow_type = workflow_data.get("workflow_type")
        
        try:
            workflow_enum = MedicalWorkflowType(workflow_type)
            sla = self.workflow_slas.get(workflow_enum, {})
            max_duration = sla.get("max_duration_minutes", 60)
            
            return self._calculate_workflow_duration(workflow_id) > max_duration
        except ValueError:
            return False
    
    async def process_medical_case(
        self,
        case_id: str,
        patient_data: Dict[str, Any],
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        Process medical case using workflow orchestration.
        
        Args:
            case_id: Unique case identifier
            patient_data: Complete medical case data
            context: Agent execution context
            
        Returns:
            Orchestrated workflow execution results
        """
        
        # Store case for tracking
        self.active_cases[case_id] = {
            "patient_id": patient_data.get("patient_id", case_id),
            "started_at": datetime.now().isoformat(),
            "status": "processing"
        }
        
        # Determine workflow type and priority
        workflow_request = patient_data.get("workflow_request", {})
        workflow_type = workflow_request.get("type", "lpp_analysis")
        priority = workflow_request.get("priority", "medium")
        
        # Execute workflow using tools
        tools = self.create_tools()
        execute_tool = next(tool for tool in tools if tool.name == "execute_medical_workflow")
        
        result = execute_tool.function(
            workflow_type,
            patient_data.get("patient_id", case_id),
            patient_data,
            priority
        )
        
        # Update case status
        self.active_cases[case_id]["status"] = "completed"
        self.active_cases[case_id]["completed_at"] = datetime.now().isoformat()
        self.active_cases[case_id]["result"] = result
        
        return result