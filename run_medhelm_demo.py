#!/usr/bin/env python3
"""
MedHELM Demo - Quick demonstration without full Vigía components
"""

import json
from pathlib import Path
from datetime import datetime

from vigia_detect.evaluation.medhelm import (
    MedHELMTaxonomy,
    VigiaCapabilityMapper,
    MedHELMMetrics
)
from vigia_detect.evaluation.medhelm.visualizer import MedHELMVisualizer
from vigia_detect.evaluation.medhelm.test_data_generator import MedHELMTestDataGenerator


def main():
    print("=" * 60)
    print("MEDHELM EVALUATION DEMO")
    print("=" * 60)
    
    # 1. Show Vigía capabilities
    print("\n📊 Vigía Capability Analysis")
    mapper = VigiaCapabilityMapper()
    summary = mapper.get_capability_summary()
    
    print(f"\nCapability Coverage: {summary['coverage_percentage']:.1f}%")
    print("\nCapability Distribution:")
    for level, count in summary['by_level'].items():
        print(f"  - {level}: {count} tasks")
    
    print("\nStrong Capabilities:")
    for cap in mapper.get_strong_capabilities()[:3]:
        task = mapper.taxonomy.tasks[cap.task_id]
        print(f"  - {task.name}")
        print(f"    Evidence: {cap.evidence}")
    
    # 2. Generate test data
    print("\n📋 Generating Test Data")
    generator = MedHELMTestDataGenerator()
    test_data = {
        "clinical_decision": generator.generate_clinical_decision_data(5),
        "communication": generator.generate_communication_data(5),
        "admin": generator.generate_admin_workflow_data(5)
    }
    
    print(f"  - Generated {sum(len(v) for v in test_data.values())} test samples")
    
    # 3. Simulate evaluation results
    print("\n🔬 Simulating Evaluation")
    
    mock_results = {
        "evaluation_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "timestamp": datetime.now().isoformat(),
        "vigia_version": "1.3.1",
        "categories_evaluated": ["Clinical Decision Support", "Patient Communication"],
        "results_by_category": {
            "Clinical Decision Support": [
                {
                    "task_id": "cds_diagnosis_1",
                    "task_name": "Differential Diagnosis Generation",
                    "success": True,
                    "metrics": {
                        "accuracy": {"value": 0.978},
                        "f1_score": {"value": 0.965}
                    },
                    "runtime_seconds": 1.2
                }
            ],
            "Patient Communication": [
                {
                    "task_id": "comm_explain_1",
                    "task_name": "Medical Explanation Simplification",
                    "success": True,
                    "metrics": {
                        "readability": {"value": 72.5}
                    },
                    "runtime_seconds": 0.8
                }
            ]
        },
        "summary": {
            "total_tasks_evaluated": 2,
            "successful_tasks": 2,
            "failed_tasks": 0,
            "average_runtime": 1.0,
            "category_performance": {
                "Clinical Decision Support": {
                    "tasks_evaluated": 1,
                    "success_rate": 1.0,
                    "average_runtime": 1.2
                },
                "Patient Communication": {
                    "tasks_evaluated": 1,
                    "success_rate": 1.0,
                    "average_runtime": 0.8
                }
            }
        }
    }
    
    # 4. Generate visualizations
    print("\n📈 Generating Visualizations")
    output_dir = Path("./evaluation_results/demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    visualizer = MedHELMVisualizer(str(output_dir))
    
    # Heatmap
    heatmap_data = mapper.generate_heatmap_data()
    heatmap_path = visualizer.create_capability_heatmap(heatmap_data)
    print(f"  ✅ Capability heatmap: {heatmap_path}")
    
    # Coverage pie chart
    pie_path = visualizer.create_coverage_pie_chart(summary)
    print(f"  ✅ Coverage pie chart: {pie_path}")
    
    # Performance comparison
    perf_path = visualizer.create_performance_comparison(mock_results)
    if perf_path:
        print(f"  ✅ Performance comparison: {perf_path}")
    
    # Executive dashboard
    dashboard_path = visualizer.create_executive_dashboard(mock_results, summary)
    print(f"  ✅ Executive dashboard: {dashboard_path}")
    
    # 5. Save demo report
    report_path = output_dir / "medhelm_demo_report.md"
    
    report = f"""# MedHELM Evaluation Demo Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

This demo shows Vigía's MedHELM evaluation capabilities:

- **Coverage:** {summary['coverage_percentage']:.1f}% of applicable tasks
- **Strong Capabilities:** {summary['by_level']['strong']} tasks
- **Key Strengths:** Clinical Decision Support, Patient Communication

## Visualizations Generated

1. **Capability Heatmap** - Shows coverage across MedHELM categories
2. **Coverage Pie Chart** - Distribution of capability levels
3. **Performance Comparison** - Vigía performance by category
4. **Executive Dashboard** - Comprehensive overview

## Next Steps

Run full evaluation with:
```bash
python evaluate_medhelm.py --visualize
```

For more details, see: `docs/medHelm_evaluation/MEDHELM_EVALUATION_IMPLEMENTATION.md`
"""
    
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\n📝 Demo report saved to: {report_path}")
    
    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETE!")
    print("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit(main())