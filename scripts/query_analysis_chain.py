#!/usr/bin/env python3
"""
Query Analysis Chain Utility
============================

Utility script to query and analyze the complete agent analysis chains
for medical case traceability and compliance.

Usage:
    python scripts/query_analysis_chain.py --case-session case_20250622_190054
    python scripts/query_analysis_chain.py --batman-token batman_demo_ea2ecf4b
    python scripts/query_analysis_chain.py --agent-type risk_assessment
    python scripts/query_analysis_chain.py --analysis-id 12345 --trace-pathway
"""

import argparse
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

async def query_case_analysis_chain(case_session: str) -> None:
    """Query complete analysis chain for a medical case"""
    print(f"🔍 Querying Analysis Chain for Case: {case_session}")
    print("=" * 60)
    
    # This would use the AgentAnalysisClient in production
    # For demo purposes, we'll simulate the query
    
    mock_analysis_chain = [
        {
            "analysis_id": "img_001",
            "agent_type": "image_analysis",
            "timestamp": "2025-06-22T19:00:54Z",
            "confidence_scores": {"detection": 0.85, "anatomical": 0.92},
            "output_summary": "LPP Grade 2 detected in sacral region",
            "processing_time_ms": 3200
        },
        {
            "analysis_id": "risk_002", 
            "agent_type": "risk_assessment",
            "timestamp": "2025-06-22T19:00:57Z",
            "confidence_scores": {"overall": 0.88, "braden": 0.95},
            "output_summary": "High risk (78%) - escalation required",
            "processing_time_ms": 1800,
            "parent_analysis_id": "img_001"
        },
        {
            "analysis_id": "voice_003",
            "agent_type": "voice_analysis", 
            "timestamp": "2025-06-22T19:01:00Z",
            "confidence_scores": {"voice": 0.82, "pain": 0.75},
            "output_summary": "Pain score 0.65, elevated stress",
            "processing_time_ms": 2100
        },
        {
            "analysis_id": "monai_004",
            "agent_type": "monai_review",
            "timestamp": "2025-06-22T19:01:02Z", 
            "confidence_scores": {"validation": 0.90, "quality": 0.88},
            "output_summary": "Model performance good, segmentation precise",
            "processing_time_ms": 1500,
            "parent_analysis_id": "img_001"
        },
        {
            "analysis_id": "diag_005",
            "agent_type": "diagnostic",
            "timestamp": "2025-06-22T19:01:05Z",
            "confidence_scores": {"synthesis": 0.89, "treatment": 0.92},
            "output_summary": "Final diagnosis: LPP Grade 2 - immediate intervention",
            "processing_time_ms": 2800,
            "parent_analysis_id": "risk_002"
        }
    ]
    
    # Display analysis chain
    print("📋 ANALYSIS CHAIN SUMMARY")
    print("-" * 40)
    
    total_time = 0
    for i, analysis in enumerate(mock_analysis_chain, 1):
        print(f"{i}. {analysis['agent_type'].upper().replace('_', ' ')}")
        print(f"   ID: {analysis['analysis_id']}")
        print(f"   Time: {analysis['timestamp']}")
        print(f"   Summary: {analysis['output_summary']}")
        print(f"   Processing: {analysis['processing_time_ms']}ms")
        if analysis.get('parent_analysis_id'):
            print(f"   Parent: {analysis['parent_analysis_id']}")
        
        # Show confidence scores
        confidence_str = ", ".join([f"{k}: {v:.2f}" for k, v in analysis['confidence_scores'].items()])
        print(f"   Confidence: {confidence_str}")
        print()
        
        total_time += analysis['processing_time_ms']
    
    print(f"📊 CHAIN STATISTICS")
    print("-" * 40)
    print(f"Total Analyses: {len(mock_analysis_chain)}")
    print(f"Total Processing Time: {total_time}ms ({total_time/1000:.1f}s)")
    print(f"Average Confidence: {sum(sum(a['confidence_scores'].values()) for a in mock_analysis_chain) / sum(len(a['confidence_scores']) for a in mock_analysis_chain):.3f}")
    print()

async def trace_decision_pathway(analysis_id: str) -> None:
    """Trace decision pathway from specific analysis"""
    print(f"🎯 Tracing Decision Pathway from Analysis: {analysis_id}")
    print("=" * 60)
    
    # Mock decision pathway trace
    pathway = {
        "target_analysis": {
            "analysis_id": analysis_id,
            "agent_type": "diagnostic",
            "decision": "LPP Grade 2 - immediate intervention required"
        },
        "decision_flow": [
            "image_analysis: Detected LPP Grade 2 with 85% confidence",
            "risk_assessment: High risk (78%) with escalation required", 
            "voice_analysis: Pain indicators present (65% pain score)",
            "monai_review: AI model validation confirms findings",
            ">>> diagnostic: Final synthesis - immediate intervention <<<"
        ],
        "confidence_evolution": [
            {"agent": "image_analysis", "confidence": 0.85},
            {"agent": "risk_assessment", "confidence": 0.88},
            {"agent": "voice_analysis", "confidence": 0.82},
            {"agent": "monai_review", "confidence": 0.90},
            {"agent": "diagnostic", "confidence": 0.89}
        ],
        "evidence_accumulation": [
            {"agent": "image_analysis", "evidence_count": 2, "new_evidence": ["NPUAP_Classification", "MONAI_Segmentation"]},
            {"agent": "risk_assessment", "evidence_count": 5, "new_evidence": ["Braden_Scale", "Norton_Scale", "Risk_Meta_Analysis"]},
            {"agent": "voice_analysis", "evidence_count": 7, "new_evidence": ["Voice_Biomarkers", "Pain_Assessment"]},
            {"agent": "monai_review", "evidence_count": 9, "new_evidence": ["MONAI_Validation", "AI_Quality_Assessment"]},
            {"agent": "diagnostic", "evidence_count": 12, "new_evidence": ["Treatment_Guidelines", "Multimodal_Assessment", "Evidence_Based_Management"]}
        ]
    }
    
    print("🔄 DECISION FLOW")
    print("-" * 40)
    for step in pathway["decision_flow"]:
        if ">>>" in step:
            print(f"🎯 {step}")
        else:
            print(f"   → {step}")
    print()
    
    print("📈 CONFIDENCE EVOLUTION")
    print("-" * 40)
    for entry in pathway["confidence_evolution"]:
        agent = entry["agent"].replace("_", " ").title()
        confidence = entry["confidence"]
        bar = "█" * int(confidence * 20)
        print(f"{agent:20} {confidence:.3f} |{bar:<20}|")
    print()
    
    print("📚 EVIDENCE ACCUMULATION")
    print("-" * 40)
    for entry in pathway["evidence_accumulation"]:
        agent = entry["agent"].replace("_", " ").title()
        total = entry["evidence_count"]
        new = len(entry["new_evidence"])
        print(f"{agent:20} Total: {total:2d} (+{new} new)")
        for evidence in entry["new_evidence"]:
            print(f"                     + {evidence}")
        print()

async def analyze_agent_performance(agent_type: str) -> None:
    """Analyze performance metrics for specific agent type"""
    print(f"📊 Performance Analysis for: {agent_type.upper().replace('_', ' ')}")
    print("=" * 60)
    
    # Mock performance metrics
    performance = {
        "agent_type": agent_type,
        "analysis_period": "30 days",
        "total_analyses": 1247,
        "success_rate": 94.8,
        "failure_rate": 3.2,
        "escalation_rate": 8.5,
        "average_processing_time_ms": 2150,
        "average_confidence": 0.856,
        "common_escalation_triggers": [
            ("high_risk_score_detected", 89),
            ("confidence_below_threshold", 34), 
            ("inconsistent_findings", 12),
            ("technical_error", 8),
            ("manual_review_requested", 6)
        ],
        "daily_average": 41.6,
        "performance_trend": "improving"
    }
    
    print("🎯 OVERALL METRICS")
    print("-" * 40)
    print(f"Total Analyses: {performance['total_analyses']:,}")
    print(f"Success Rate: {performance['success_rate']:.1f}%")
    print(f"Failure Rate: {performance['failure_rate']:.1f}%") 
    print(f"Escalation Rate: {performance['escalation_rate']:.1f}%")
    print(f"Daily Average: {performance['daily_average']:.1f} analyses/day")
    print(f"Performance Trend: {performance['performance_trend'].upper()}")
    print()
    
    print("⚡ PERFORMANCE METRICS")
    print("-" * 40)
    print(f"Average Processing Time: {performance['average_processing_time_ms']}ms")
    print(f"Average Confidence: {performance['average_confidence']:.3f}")
    print()
    
    print("⚠️  ESCALATION TRIGGERS")
    print("-" * 40)
    for trigger, count in performance['common_escalation_triggers']:
        trigger_name = trigger.replace("_", " ").title()
        print(f"{trigger_name:25} {count:3d} cases")
    print()

async def query_cross_agent_correlations(case_session: str) -> None:
    """Analyze correlations between agents in a case"""
    print(f"🔗 Cross-Agent Correlations for Case: {case_session}")
    print("=" * 60)
    
    # Mock correlation analysis
    correlations = {
        "agent_types_involved": ["image_analysis", "risk_assessment", "voice_analysis", "monai_review", "diagnostic"],
        "total_analyses": 5,
        "confidence_correlations": {
            "image_analysis": 0.85,
            "risk_assessment": 0.88,
            "voice_analysis": 0.82,
            "monai_review": 0.90,
            "diagnostic": 0.89
        },
        "evidence_overlap": {
            "image_analysis_risk_assessment": 15.2,
            "image_analysis_diagnostic": 28.7,
            "risk_assessment_diagnostic": 45.8,
            "voice_analysis_diagnostic": 12.3,
            "monai_review_diagnostic": 22.1
        },
        "decision_agreement": {
            "primary_diagnosis": {"agreement_rate": 92.5, "unique_values": ["lpp_grade_2"], "total_instances": 3},
            "risk_level": {"agreement_rate": 87.2, "unique_values": ["high", "elevated"], "total_instances": 2},
            "urgency": {"agreement_rate": 95.1, "unique_values": ["immediate"], "total_instances": 4}
        },
        "temporal_efficiency": "efficient"
    }
    
    print("🎯 CONFIDENCE CORRELATIONS")
    print("-" * 40)
    for agent, confidence in correlations["confidence_correlations"].items():
        agent_name = agent.replace("_", " ").title()
        bar = "█" * int(confidence * 20)
        print(f"{agent_name:20} {confidence:.3f} |{bar:<20}|")
    print()
    
    print("🔗 EVIDENCE OVERLAP (% shared)")
    print("-" * 40)
    for pair, overlap in correlations["evidence_overlap"].items():
        pair_name = pair.replace("_", " vs ").replace("analysis", "").title()
        print(f"{pair_name:35} {overlap:5.1f}%")
    print()
    
    print("🤝 DECISION AGREEMENT")
    print("-" * 40)
    for field, data in correlations["decision_agreement"].items():
        field_name = field.replace("_", " ").title()
        agreement = data["agreement_rate"]
        print(f"{field_name:20} {agreement:5.1f}% agreement")
        print(f"                     Values: {', '.join(data['unique_values'])}")
    print()
    
    print(f"⚡ Temporal Efficiency: {correlations['temporal_efficiency'].upper()}")

async def main():
    """Main query interface"""
    parser = argparse.ArgumentParser(description="Query agent analysis chains")
    parser.add_argument("--case-session", help="Query specific case session")
    parser.add_argument("--batman-token", help="Query by Batman token")
    parser.add_argument("--agent-type", help="Analyze specific agent type performance")
    parser.add_argument("--analysis-id", help="Trace decision pathway from analysis ID")
    parser.add_argument("--trace-pathway", action="store_true", help="Trace decision pathway")
    parser.add_argument("--correlations", action="store_true", help="Show cross-agent correlations")
    
    args = parser.parse_args()
    
    if args.case_session:
        await query_case_analysis_chain(args.case_session)
        if args.correlations:
            print()
            await query_cross_agent_correlations(args.case_session)
    
    elif args.batman_token:
        print(f"🦇 Querying all analyses for Batman Token: {args.batman_token}")
        print("This would show all medical cases for this patient (tokenized)")
        print()
    
    elif args.agent_type:
        await analyze_agent_performance(args.agent_type)
    
    elif args.analysis_id and args.trace_pathway:
        await trace_decision_pathway(args.analysis_id)
    
    else:
        # Interactive mode
        print("🔬 Agent Analysis Query Interface")
        print("=================================")
        print()
        print("Available queries:")
        print("1. Case analysis chain")
        print("2. Agent performance analysis") 
        print("3. Decision pathway tracing")
        print("4. Cross-agent correlations")
        print()
        
        choice = input("Select query type (1-4): ").strip()
        
        if choice == "1":
            case_session = input("Enter case session ID: ").strip()
            if case_session:
                await query_case_analysis_chain(case_session)
        
        elif choice == "2":
            agent_type = input("Enter agent type (risk_assessment, image_analysis, etc.): ").strip()
            if agent_type:
                await analyze_agent_performance(agent_type)
        
        elif choice == "3":
            analysis_id = input("Enter analysis ID to trace from: ").strip()
            if analysis_id:
                await trace_decision_pathway(analysis_id)
        
        elif choice == "4":
            case_session = input("Enter case session ID: ").strip()
            if case_session:
                await query_cross_agent_correlations(case_session)

if __name__ == "__main__":
    asyncio.run(main())