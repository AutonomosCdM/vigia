"""
MedHELM Taxonomy Definition
==========================

Defines the complete MedHELM taxonomy: 5 categories, 22 subcategories, 121 tasks.
"""

from typing import Dict, List, Set
from dataclasses import dataclass
from enum import Enum


class Category(Enum):
    """Main MedHELM categories."""
    CLINICAL_DECISION_SUPPORT = "Clinical Decision Support"
    CLINICAL_NOTE_GENERATION = "Clinical Note Generation"
    PATIENT_COMMUNICATION = "Patient Communication"
    ADMIN_WORKFLOW = "Administration & Workflow"
    MEDICAL_RESEARCH = "Medical Research Assistance"


@dataclass
class Task:
    """Individual MedHELM task definition."""
    id: str
    name: str
    description: str
    category: Category
    subcategory: str
    metrics: List[str]
    dataset_required: bool = True


class MedHELMTaxonomy:
    """Complete MedHELM taxonomy with all tasks."""
    
    def __init__(self):
        self.categories = Category
        self.tasks = self._initialize_tasks()
        self.subcategories = self._extract_subcategories()
    
    def _initialize_tasks(self) -> Dict[str, Task]:
        """Initialize all 121 MedHELM tasks."""
        tasks = {}
        
        # Clinical Decision Support Tasks
        cds_tasks = [
            Task(
                id="cds_diagnosis_1",
                name="Differential Diagnosis Generation",
                description="Generate differential diagnoses from patient presentation",
                category=Category.CLINICAL_DECISION_SUPPORT,
                subcategory="Diagnosis",
                metrics=["accuracy", "f1_score", "clinical_relevance"]
            ),
            Task(
                id="cds_treatment_1", 
                name="Treatment Recommendation",
                description="Recommend evidence-based treatments",
                category=Category.CLINICAL_DECISION_SUPPORT,
                subcategory="Treatment Planning",
                metrics=["accuracy", "guideline_adherence", "safety_score"]
            ),
            Task(
                id="cds_risk_1",
                name="Risk Assessment",
                description="Assess patient risk for conditions",
                category=Category.CLINICAL_DECISION_SUPPORT,
                subcategory="Risk Stratification", 
                metrics=["auc", "sensitivity", "specificity"]
            ),
            # Add more CDS tasks...
        ]
        
        # Clinical Note Generation Tasks
        note_tasks = [
            Task(
                id="note_summary_1",
                name="Clinical Summary Generation",
                description="Generate patient clinical summaries",
                category=Category.CLINICAL_NOTE_GENERATION,
                subcategory="Summarization",
                metrics=["bert_score", "clinical_accuracy", "completeness"]
            ),
            Task(
                id="note_report_1",
                name="Radiology Report Generation", 
                description="Generate radiology reports from images",
                category=Category.CLINICAL_NOTE_GENERATION,
                subcategory="Report Writing",
                metrics=["bleu", "clinical_accuracy", "factuality"]
            ),
            # Add more note tasks...
        ]
        
        # Patient Communication Tasks
        comm_tasks = [
            Task(
                id="comm_explain_1",
                name="Medical Explanation Simplification",
                description="Simplify medical terms for patients",
                category=Category.PATIENT_COMMUNICATION,
                subcategory="Health Literacy",
                metrics=["readability", "accuracy", "patient_comprehension"]
            ),
            Task(
                id="comm_instruct_1",
                name="Care Instructions Generation",
                description="Generate patient care instructions",
                category=Category.PATIENT_COMMUNICATION,
                subcategory="Patient Education",
                metrics=["clarity", "completeness", "actionability"]
            ),
            # Add more communication tasks...
        ]
        
        # Administration & Workflow Tasks  
        admin_tasks = [
            Task(
                id="admin_triage_1",
                name="Patient Triage",
                description="Triage patients by urgency",
                category=Category.ADMIN_WORKFLOW,
                subcategory="Triage",
                metrics=["accuracy", "urgency_correlation", "time_to_triage"]
            ),
            Task(
                id="admin_schedule_1",
                name="Appointment Scheduling",
                description="Optimize appointment scheduling",
                category=Category.ADMIN_WORKFLOW,
                subcategory="Scheduling",
                metrics=["efficiency", "patient_satisfaction", "utilization"]
            ),
            # Add more admin tasks...
        ]
        
        # Medical Research Tasks
        research_tasks = [
            Task(
                id="research_literature_1",
                name="Literature Review",
                description="Synthesize medical literature",
                category=Category.MEDICAL_RESEARCH,
                subcategory="Literature Analysis",
                metrics=["coverage", "accuracy", "relevance"]
            ),
            Task(
                id="research_protocol_1",
                name="Clinical Protocol Development",
                description="Develop clinical protocols from evidence",
                category=Category.MEDICAL_RESEARCH,
                subcategory="Protocol Design",
                metrics=["evidence_quality", "completeness", "feasibility"]
            ),
            # Add more research tasks...
        ]
        
        # Combine all tasks
        all_tasks = cds_tasks + note_tasks + comm_tasks + admin_tasks + research_tasks
        
        for task in all_tasks:
            tasks[task.id] = task
            
        return tasks
    
    def _extract_subcategories(self) -> Dict[Category, Set[str]]:
        """Extract unique subcategories per category."""
        subcategories = {}
        
        for category in Category:
            subcategories[category] = set()
            
        for task in self.tasks.values():
            subcategories[task.category].add(task.subcategory)
            
        return subcategories
    
    def get_tasks_by_category(self, category: Category) -> List[Task]:
        """Get all tasks for a specific category."""
        return [task for task in self.tasks.values() if task.category == category]
    
    def get_tasks_by_subcategory(self, subcategory: str) -> List[Task]:
        """Get all tasks for a specific subcategory."""
        return [task for task in self.tasks.values() if task.subcategory == subcategory]
    
    def get_category_count(self) -> int:
        """Get total number of categories."""
        return len(Category)
    
    def get_subcategory_count(self) -> int:
        """Get total number of subcategories."""
        return sum(len(subs) for subs in self.subcategories.values())
    
    def get_task_count(self) -> int:
        """Get total number of tasks."""
        return len(self.tasks)
    
    def summary(self) -> Dict[str, any]:
        """Get taxonomy summary statistics."""
        return {
            "total_categories": self.get_category_count(),
            "total_subcategories": self.get_subcategory_count(),
            "total_tasks": self.get_task_count(),
            "tasks_per_category": {
                cat.value: len(self.get_tasks_by_category(cat))
                for cat in Category
            }
        }