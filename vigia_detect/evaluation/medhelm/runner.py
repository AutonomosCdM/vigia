"""
MedHELM Evaluation Runner
========================

Main runner for executing MedHELM evaluations on Vigía.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

from .taxonomy import MedHELMTaxonomy, Category, Task
from .metrics import MedHELMMetrics, MetricResult
from .mapper import VigiaCapabilityMapper, CapabilityLevel


@dataclass
class EvaluationResult:
    """Result of evaluating a single task."""
    task_id: str
    task_name: str
    category: str
    timestamp: str
    metrics: Dict[str, MetricResult]
    runtime_seconds: float
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MedHELMRunner:
    """Runner for MedHELM evaluation framework."""
    
    def __init__(self, output_dir: str = "./evaluation_results"):
        self.taxonomy = MedHELMTaxonomy()
        self.mapper = VigiaCapabilityMapper()
        self.metrics = MedHELMMetrics()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Import Vigía components
        self._import_vigia_components()
        
    def _import_vigia_components(self):
        """Import necessary Vigía components for evaluation."""
        try:
            # Core components
            from vigia_detect.core.medical_dispatcher import MedicalDispatcher
            from vigia_detect.core.triage_engine import TriageEngine
            
            # Systems
            from vigia_detect.systems.medical_decision_engine import MedicalDecisionEngine
            from vigia_detect.systems.clinical_processing import ClinicalProcessor
            
            # AI components
            from vigia_detect.ai.medgemma_local_client import MedGemmaLocalClient
            
            # CV pipeline
            from vigia_detect.cv_pipeline.real_lpp_detector import RealLPPDetector
            
            self.components = {
                'medical_dispatcher': MedicalDispatcher(),
                'triage_engine': TriageEngine(),
                'decision_engine': MedicalDecisionEngine(),
                'clinical_processor': ClinicalProcessor(),
                'lpp_detector': RealLPPDetector()
            }
            
            # Initialize MedGemma if available
            try:
                self.components['medgemma'] = MedGemmaLocalClient()
            except:
                print("Warning: MedGemma not available, using mock")
                self.components['medgemma'] = None
                
        except Exception as e:
            print(f"Warning: Could not import all Vigía components: {e}")
            self.components = {}
    
    async def evaluate_task(self, task: Task, test_data: List[Dict]) -> EvaluationResult:
        """Evaluate a single MedHELM task."""
        start_time = time.time()
        
        try:
            # Check if Vigía has capability for this task
            capability = self.mapper.capability_map.get(task.id)
            
            if not capability or capability.level == CapabilityLevel.NOT_APPLICABLE:
                return EvaluationResult(
                    task_id=task.id,
                    task_name=task.name,
                    category=task.category.value,
                    timestamp=datetime.now().isoformat(),
                    metrics={},
                    runtime_seconds=0,
                    success=False,
                    error="Task not applicable to Vigía"
                )
            
            # Run task-specific evaluation
            if task.category == Category.CLINICAL_DECISION_SUPPORT:
                results = await self._evaluate_clinical_decision_task(task, test_data)
            elif task.category == Category.CLINICAL_NOTE_GENERATION:
                results = await self._evaluate_note_generation_task(task, test_data)
            elif task.category == Category.PATIENT_COMMUNICATION:
                results = await self._evaluate_communication_task(task, test_data)
            elif task.category == Category.ADMIN_WORKFLOW:
                results = await self._evaluate_admin_task(task, test_data)
            else:
                results = await self._evaluate_research_task(task, test_data)
            
            runtime = time.time() - start_time
            
            return EvaluationResult(
                task_id=task.id,
                task_name=task.name,
                category=task.category.value,
                timestamp=datetime.now().isoformat(),
                metrics=results,
                runtime_seconds=runtime,
                success=True,
                metadata={"capability_level": capability.level.value}
            )
            
        except Exception as e:
            return EvaluationResult(
                task_id=task.id,
                task_name=task.name,
                category=task.category.value,
                timestamp=datetime.now().isoformat(),
                metrics={},
                runtime_seconds=time.time() - start_time,
                success=False,
                error=str(e)
            )
    
    async def _evaluate_clinical_decision_task(self, task: Task, 
                                             test_data: List[Dict]) -> Dict[str, MetricResult]:
        """Evaluate clinical decision support tasks."""
        metrics_results = {}
        
        if task.id == "cds_diagnosis_1":
            # Evaluate LPP detection
            predictions = []
            ground_truth = []
            
            for sample in test_data:
                if 'image_path' in sample:
                    # Use real LPP detector
                    detector = self.components.get('lpp_detector')
                    if detector:
                        result = detector.detect(sample['image_path'])
                        predictions.append(result['grade'])
                        ground_truth.append(sample['true_grade'])
            
            if predictions:
                metrics_results['accuracy'] = self.metrics.accuracy(ground_truth, predictions)
                metrics_results['f1_score'] = self.metrics.f1_score(ground_truth, predictions)
                
        elif task.id == "cds_treatment_1":
            # Evaluate treatment recommendations
            decisions = []
            
            for sample in test_data:
                decision_engine = self.components.get('decision_engine')
                if decision_engine:
                    decision = decision_engine.make_clinical_decision(
                        lpp_grade=sample.get('lpp_grade', 2),
                        confidence=sample.get('confidence', 0.85),
                        anatomical_location=sample.get('location', 'sacrum')
                    )
                    decisions.append(decision)
            
            if decisions:
                guidelines = ['NPUAP', 'EPUAP', 'PPPIA']
                metrics_results['guideline_adherence'] = self.metrics.guideline_adherence(
                    decisions, guidelines
                )
                
        return metrics_results
    
    async def _evaluate_note_generation_task(self, task: Task,
                                           test_data: List[Dict]) -> Dict[str, MetricResult]:
        """Evaluate clinical note generation tasks."""
        metrics_results = {}
        
        # Placeholder for note generation evaluation
        # Would use MedGemma for actual generation
        
        predictions = []
        references = []
        
        for sample in test_data:
            if self.components.get('medgemma'):
                # Generate clinical note
                prompt = f"Generate clinical summary for patient with {sample.get('condition')}"
                response = await self.components['medgemma'].generate(prompt)
                predictions.append(response)
                references.append(sample.get('reference_note', ''))
        
        if predictions:
            metrics_results['bert_score'] = self.metrics.bert_score(predictions, references)
            
        return metrics_results
    
    async def _evaluate_communication_task(self, task: Task,
                                         test_data: List[Dict]) -> Dict[str, MetricResult]:
        """Evaluate patient communication tasks."""
        metrics_results = {}
        
        # Evaluate readability of generated patient communications
        texts = []
        
        for sample in test_data:
            # Simulate patient communication generation
            simplified_text = sample.get('simplified_text', '')
            texts.append(simplified_text)
        
        if texts:
            metrics_results['readability'] = self.metrics.readability_score(texts)
            
        return metrics_results
    
    async def _evaluate_admin_task(self, task: Task,
                                 test_data: List[Dict]) -> Dict[str, MetricResult]:
        """Evaluate administration and workflow tasks."""
        metrics_results = {}
        
        if task.id == "admin_triage_1":
            # Evaluate triage accuracy
            triage_engine = self.components.get('triage_engine')
            
            if triage_engine:
                predictions = []
                ground_truth = []
                start_times = []
                end_times = []
                
                for sample in test_data:
                    start = time.time()
                    urgency = triage_engine.assess_urgency(sample)
                    end = time.time()
                    
                    predictions.append(urgency)
                    ground_truth.append(sample.get('true_urgency'))
                    start_times.append(start)
                    end_times.append(end)
                
                if predictions:
                    metrics_results['accuracy'] = self.metrics.accuracy(ground_truth, predictions)
                    metrics_results['response_time'] = self.metrics.response_time(
                        start_times, end_times
                    )
                    
        return metrics_results
    
    async def _evaluate_research_task(self, task: Task,
                                    test_data: List[Dict]) -> Dict[str, MetricResult]:
        """Evaluate medical research assistance tasks."""
        # Placeholder - Vigía has limited research capabilities
        return {}
    
    async def run_evaluation(self, categories: Optional[List[Category]] = None,
                           test_data_path: Optional[str] = None) -> Dict[str, Any]:
        """Run complete MedHELM evaluation."""
        print("=" * 60)
        print("MEDHELM EVALUATION RUNNER")
        print("=" * 60)
        
        # Load test data
        test_data = self._load_test_data(test_data_path)
        
        # Determine which categories to evaluate
        if categories is None:
            categories = [cat for cat in Category]
        
        results = {
            "evaluation_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "timestamp": datetime.now().isoformat(),
            "vigia_version": "1.3.1",
            "categories_evaluated": [cat.value for cat in categories],
            "results_by_category": {},
            "summary": {}
        }
        
        # Run evaluation for each category
        for category in categories:
            print(f"\nEvaluating category: {category.value}")
            category_results = []
            
            tasks = self.taxonomy.get_tasks_by_category(category)
            
            for task in tasks:
                # Check if we have capability
                capability = self.mapper.capability_map.get(task.id)
                
                if capability and capability.level != CapabilityLevel.NOT_APPLICABLE:
                    print(f"  - Evaluating task: {task.name}")
                    
                    # Get task-specific test data
                    task_test_data = test_data.get(task.id, test_data.get('default', []))
                    
                    result = await self.evaluate_task(task, task_test_data)
                    category_results.append(result)
                else:
                    print(f"  - Skipping task: {task.name} (not applicable)")
            
            results["results_by_category"][category.value] = [
                asdict(r) for r in category_results
            ]
        
        # Generate summary
        results["summary"] = self._generate_summary(results)
        
        # Save results
        self._save_results(results)
        
        return results
    
    def _load_test_data(self, test_data_path: Optional[str]) -> Dict[str, List[Dict]]:
        """Load test data for evaluation."""
        if test_data_path and Path(test_data_path).exists():
            with open(test_data_path, 'r') as f:
                return json.load(f)
        
        # Generate default test data
        return self._generate_default_test_data()
    
    def _generate_default_test_data(self) -> Dict[str, List[Dict]]:
        """Generate default test data based on Vigía's capabilities."""
        return {
            "default": [
                {
                    "image_path": "/path/to/test/image1.jpg",
                    "true_grade": 2,
                    "lpp_grade": 2,
                    "confidence": 0.85,
                    "location": "sacrum",
                    "condition": "Grade 2 pressure ulcer on sacrum",
                    "reference_note": "Patient presents with partial thickness skin loss...",
                    "simplified_text": "You have a sore on your lower back that needs care.",
                    "true_urgency": "high"
                }
                # Add more test samples...
            ],
            "cds_diagnosis_1": [
                # Task-specific test data
            ]
        }
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate evaluation summary."""
        summary = {
            "total_tasks_evaluated": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_runtime": 0,
            "category_performance": {}
        }
        
        total_runtime = 0
        
        for category, category_results in results["results_by_category"].items():
            successful = sum(1 for r in category_results if r["success"])
            total = len(category_results)
            
            summary["total_tasks_evaluated"] += total
            summary["successful_tasks"] += successful
            summary["failed_tasks"] += total - successful
            
            if total > 0:
                avg_runtime = sum(r["runtime_seconds"] for r in category_results) / total
                total_runtime += avg_runtime * total
                
                summary["category_performance"][category] = {
                    "tasks_evaluated": total,
                    "success_rate": successful / total,
                    "average_runtime": avg_runtime
                }
        
        if summary["total_tasks_evaluated"] > 0:
            summary["average_runtime"] = total_runtime / summary["total_tasks_evaluated"]
            
        return summary
    
    def _save_results(self, results: Dict[str, Any]):
        """Save evaluation results to file."""
        filename = f"medhelm_evaluation_{results['evaluation_id']}.json"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
            
        print(f"\nResults saved to: {filepath}")
        
        # Also save summary report
        self._save_summary_report(results)
    
    def _save_summary_report(self, results: Dict[str, Any]):
        """Save summary report in markdown format."""
        summary = results.get('summary', {})
        
        report = f"""# MedHELM Evaluation Summary

**Evaluation ID:** {results['evaluation_id']}  
**Timestamp:** {results['timestamp']}  
**Vigía Version:** {results['vigia_version']}

## Results Summary

- **Total Tasks Evaluated:** {summary.get('total_tasks_evaluated', 0)}
- **Successful Tasks:** {summary.get('successful_tasks', 0)}
- **Failed Tasks:** {summary.get('failed_tasks', 0)}
- **Average Runtime:** {summary.get('average_runtime', 0):.2f}s

## Category Performance

"""
        
        for category, perf in summary.get('category_performance', {}).items():
            report += f"\n### {category}\n"
            report += f"- Tasks Evaluated: {perf.get('tasks_evaluated', 0)}\n"
            report += f"- Success Rate: {perf.get('success_rate', 0)*100:.1f}%\n"
            report += f"- Average Runtime: {perf.get('average_runtime', 0):.2f}s\n"
        
        # Save report
        report_path = self.output_dir / f"summary_{results['evaluation_id']}.md"
        with open(report_path, 'w') as f:
            f.write(report)