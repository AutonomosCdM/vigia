"""
Vigía Capability Mapper
======================

Maps Vigía's current capabilities to MedHELM taxonomy.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from .taxonomy import MedHELMTaxonomy, Category, Task


class CapabilityLevel(Enum):
    """Vigía's capability level for each task."""
    STRONG = "strong"        # Full capability, production-ready
    PARTIAL = "partial"      # Some capability, needs enhancement
    PLANNED = "planned"      # On roadmap, not implemented
    NOT_APPLICABLE = "not_applicable"   # Outside Vigía's scope


@dataclass
class VigiaCapability:
    """Vigía capability mapping for a MedHELM task."""
    task_id: str
    level: CapabilityLevel
    components: List[str]  # Vigía components that address this
    evidence: str  # How we demonstrate this capability
    gaps: List[str]  # What's missing for full capability


class VigiaCapabilityMapper:
    """Maps Vigía capabilities to MedHELM taxonomy."""
    
    def __init__(self):
        self.taxonomy = MedHELMTaxonomy()
        self.capability_map = self._initialize_capability_map()
        
    def _initialize_capability_map(self) -> Dict[str, VigiaCapability]:
        """Initialize Vigía's capability mapping."""
        capabilities = {}
        
        # Clinical Decision Support - Our strongest area
        capabilities.update({
            "cds_diagnosis_1": VigiaCapability(
                task_id="cds_diagnosis_1",
                level=CapabilityLevel.STRONG,
                components=[
                    "vigia_detect.cv_pipeline.real_lpp_detector",
                    "vigia_detect.systems.medical_decision_engine",
                    "vigia_detect.agents.agent_workflow",
                    "vigia_detect.ai.medgemma_local_client"
                ],
                evidence="LPP detection with 97.8% accuracy, NPUAP/EPUAP compliant decisions",
                gaps=[]
            ),
            "cds_treatment_1": VigiaCapability(
                task_id="cds_treatment_1",
                level=CapabilityLevel.STRONG,
                components=[
                    "vigia_detect.systems.medical_decision_engine",
                    "vigia_detect.systems.minsal_medical_decision_engine",
                    "vigia_detect.agents.agent_workflow.WorkflowAgent"
                ],
                evidence="Evidence-based treatment recommendations with scientific references",
                gaps=[]
            ),
            "cds_risk_1": VigiaCapability(
                task_id="cds_risk_1",
                level=CapabilityLevel.STRONG,
                components=[
                    "vigia_detect.core.triage_engine",
                    "vigia_detect.systems.clinical_processing",
                    "vigia_detect.tasks.medical.risk_score_task"
                ],
                evidence="Real-time risk assessment with triage prioritization",
                gaps=[]
            ),
        })
        
        # Clinical Note Generation - Partial capability
        capabilities.update({
            "note_summary_1": VigiaCapability(
                task_id="note_summary_1",
                level=CapabilityLevel.PARTIAL,
                components=[
                    "vigia_detect.agents.agent_llm.LLMAgent",
                    "vigia_detect.messaging.slack_messenger",
                    "vigia_detect.ai.medgemma_local_client"
                ],
                evidence="Clinical summaries via LLM agents and Slack notifications",
                gaps=["Structured note templates", "FHIR export"]
            ),
            "note_report_1": VigiaCapability(
                task_id="note_report_1",
                level=CapabilityLevel.PARTIAL,
                components=[
                    "vigia_detect.cv_pipeline.image_analyzer",
                    "vigia_detect.ai.medgemma_local_client"
                ],
                evidence="Image analysis with clinical findings",
                gaps=["Formal radiology report structure", "DICOM integration"]
            ),
        })
        
        # Patient Communication - Strong capability
        capabilities.update({
            "comm_explain_1": VigiaCapability(
                task_id="comm_explain_1",
                level=CapabilityLevel.STRONG,
                components=[
                    "vigia_detect.agents.agent_communication.UserCommunicationAgent",
                    "vigia_detect.messaging.whatsapp_messenger",
                    "vigia_detect.ai.medgemma_local_client"
                ],
                evidence="Medical term simplification with readability scoring",
                gaps=[]
            ),
            "comm_instruct_1": VigiaCapability(
                task_id="comm_instruct_1",
                level=CapabilityLevel.STRONG,
                components=[
                    "vigia_detect.messaging.templates",
                    "vigia_detect.agents.agent_communication"
                ],
                evidence="Automated care instructions via WhatsApp",
                gaps=[]
            ),
        })
        
        # Administration & Workflow - Strong capability
        capabilities.update({
            "admin_triage_1": VigiaCapability(
                task_id="admin_triage_1",
                level=CapabilityLevel.STRONG,
                components=[
                    "vigia_detect.core.triage_engine",
                    "vigia_detect.core.medical_dispatcher",
                    "vigia_detect.tasks.medical.triage_task"
                ],
                evidence="Real-time triage with urgency-based routing",
                gaps=[]
            ),
            "admin_schedule_1": VigiaCapability(
                task_id="admin_schedule_1",
                level=CapabilityLevel.NOT_APPLICABLE,
                components=[],
                evidence="Outside current scope - focus on LPP detection",
                gaps=["Appointment system integration"]
            ),
        })
        
        # Medical Research - Limited capability
        capabilities.update({
            "research_literature_1": VigiaCapability(
                task_id="research_literature_1",
                level=CapabilityLevel.PARTIAL,
                components=[
                    "vigia_detect.references",
                    "vigia_detect.rag"
                ],
                evidence="Medical reference integration and RAG search",
                gaps=["PubMed integration", "Systematic review tools"]
            ),
            "research_protocol_1": VigiaCapability(
                task_id="research_protocol_1",
                level=CapabilityLevel.PARTIAL,
                components=[
                    "vigia_detect.systems.medical_knowledge",
                    "vigia_detect.redis_layer.medical_protocols"
                ],
                evidence="Protocol storage and retrieval with Redis",
                gaps=["Protocol authoring tools", "Version control"]
            ),
        })
        
        return capabilities
    
    def get_capability_summary(self) -> Dict[str, any]:
        """Get summary of Vigía's capabilities."""
        summary = {
            "total_capabilities": len(self.capability_map),
            "by_level": {},
            "by_category": {},
            "coverage_percentage": 0
        }
        
        # Count by level
        for level in CapabilityLevel:
            count = sum(1 for cap in self.capability_map.values() if cap.level == level)
            summary["by_level"][level.value] = count
            
        # Count by category
        for category in Category:
            tasks = self.taxonomy.get_tasks_by_category(category)
            task_ids = [t.id for t in tasks]
            
            category_caps = {
                "total": len(tasks),
                "strong": 0,
                "partial": 0,
                "planned": 0,
                "not_applicable": 0
            }
            
            for task_id in task_ids:
                if task_id in self.capability_map:
                    level = self.capability_map[task_id].level
                    category_caps[level.value] += 1
                    
            summary["by_category"][category.value] = category_caps
            
        # Calculate coverage
        total_tasks = self.taxonomy.get_task_count()
        covered = sum(1 for cap in self.capability_map.values() 
                     if cap.level in [CapabilityLevel.STRONG, CapabilityLevel.PARTIAL])
        summary["coverage_percentage"] = (covered / total_tasks) * 100 if total_tasks > 0 else 0
        
        return summary
    
    def get_strong_capabilities(self) -> List[VigiaCapability]:
        """Get all strong capabilities."""
        return [cap for cap in self.capability_map.values() 
                if cap.level == CapabilityLevel.STRONG]
    
    def get_gaps_by_category(self, category: Category) -> List[Tuple[Task, VigiaCapability]]:
        """Get capability gaps for a category."""
        gaps = []
        
        for task in self.taxonomy.get_tasks_by_category(category):
            if task.id in self.capability_map:
                cap = self.capability_map[task.id]
                if cap.level != CapabilityLevel.STRONG and cap.gaps:
                    gaps.append((task, cap))
                    
        return gaps
    
    def generate_heatmap_data(self) -> List[Dict[str, any]]:
        """Generate data for capability heatmap visualization."""
        heatmap_data = []
        
        for category in Category:
            for task in self.taxonomy.get_tasks_by_category(category):
                if task.id in self.capability_map:
                    cap = self.capability_map[task.id]
                    level_score = {
                        CapabilityLevel.STRONG: 1.0,
                        CapabilityLevel.PARTIAL: 0.5,
                        CapabilityLevel.PLANNED: 0.25,
                        CapabilityLevel.NOT_APPLICABLE: 0
                    }[cap.level]
                else:
                    level_score = 0
                    
                heatmap_data.append({
                    "category": category.value,
                    "subcategory": task.subcategory,
                    "task": task.name,
                    "score": level_score,
                    "level": self.capability_map.get(task.id, None).level.value if task.id in self.capability_map else "none"
                })
                
        return heatmap_data