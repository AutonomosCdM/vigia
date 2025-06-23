#!/usr/bin/env python3
"""
Basic MedHELM Implementation Test
================================

Quick test to verify MedHELM evaluation framework is working.
"""

import sys
from pathlib import Path

# Add vigia_detect to path
sys.path.insert(0, str(Path(__file__).parent))

def test_taxonomy():
    """Test MedHELM taxonomy."""
    print("Testing MedHELM Taxonomy...")
    
    from vigia_detect.evaluation.medhelm import MedHELMTaxonomy
    
    taxonomy = MedHELMTaxonomy()
    summary = taxonomy.summary()
    
    print(f"✅ Categories: {summary['total_categories']}")
    print(f"✅ Subcategories: {summary['total_subcategories']}")
    print(f"✅ Tasks: {summary['total_tasks']}")
    
    for cat, count in summary['tasks_per_category'].items():
        print(f"  - {cat}: {count} tasks")
    
    return True

def test_mapper():
    """Test Vigía capability mapper."""
    print("\nTesting Capability Mapper...")
    
    from vigia_detect.evaluation.medhelm import VigiaCapabilityMapper
    
    mapper = VigiaCapabilityMapper()
    summary = mapper.get_capability_summary()
    
    print(f"✅ Coverage: {summary['coverage_percentage']:.1f}%")
    print(f"✅ Capability levels:")
    
    for level, count in summary['by_level'].items():
        print(f"  - {level}: {count}")
    
    # Show strong capabilities
    strong = mapper.get_strong_capabilities()
    print(f"\n✅ Strong capabilities: {len(strong)}")
    
    for cap in strong[:3]:
        print(f"  - {cap.task_id}: {cap.evidence[:50]}...")
    
    return True

def test_metrics():
    """Test MedHELM metrics."""
    print("\nTesting Metrics...")
    
    from vigia_detect.evaluation.medhelm import MedHELMMetrics
    
    metrics = MedHELMMetrics()
    
    # Test accuracy
    y_true = [1, 2, 3, 2, 1]
    y_pred = [1, 2, 3, 2, 2]
    
    result = metrics.accuracy(y_true, y_pred)
    print(f"✅ Accuracy: {result.value:.2f}")
    
    # Test clinical relevance
    predictions = [
        {"diagnosis": "Grade 2 LPP", "confidence": 0.85, "evidence": "NPUAP guidelines"},
        {"diagnosis": "Grade 3 LPP", "confidence": 0.90, "evidence": "Clinical observation"}
    ]
    ground_truth = [
        {"diagnosis": "Grade 2 LPP"},
        {"diagnosis": "Grade 3 LPP"}
    ]
    
    result = metrics.clinical_relevance(predictions, ground_truth)
    print(f"✅ Clinical relevance: {result.value:.2f}")
    
    return True

def test_visualization():
    """Test visualization capabilities."""
    print("\nTesting Visualization...")
    
    from vigia_detect.evaluation.medhelm import VigiaCapabilityMapper
    from vigia_detect.evaluation.medhelm.visualizer import MedHELMVisualizer
    
    mapper = VigiaCapabilityMapper()
    visualizer = MedHELMVisualizer()
    
    # Generate heatmap data
    heatmap_data = mapper.generate_heatmap_data()
    print(f"✅ Generated heatmap data: {len(heatmap_data)} entries")
    
    # Test capability summary
    summary = mapper.get_capability_summary()
    print(f"✅ Capability summary ready for visualization")
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("MEDHELM IMPLEMENTATION TEST")
    print("=" * 60)
    
    tests = [
        test_taxonomy,
        test_mapper,
        test_metrics,
        test_visualization
    ]
    
    failed = 0
    
    for test in tests:
        try:
            if not test():
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    
    if failed == 0:
        print("✅ ALL TESTS PASSED!")
        print("\nYou can now run the full evaluation with:")
        print("  python evaluate_medhelm.py --quick --visualize")
    else:
        print(f"❌ {failed} tests failed")
    
    return failed

if __name__ == "__main__":
    exit(main())