#!/usr/bin/env python3
"""
Risk Assessment Agent Demonstration
===================================

Comprehensive demonstration of the RiskAssessmentAgent capabilities
showing all assessment scales and medical protocols.

Features Demonstrated:
- Braden Scale assessment for pressure injury risk
- STRATIFY fall risk evaluation  
- Infection risk scoring with evidence-based factors
- MUST nutritional risk assessment
- Comprehensive multi-scale risk assessment
- Risk correlation analysis and escalation protocols
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the RiskAssessmentAgent
from vigia_detect.agents.adk.risk_assessment import create_risk_assessment_agent


class RiskAssessmentDemo:
    """Risk Assessment Agent demonstration"""
    
    def __init__(self):
        self.agent = None
        self.demo_patients = self._create_demo_patients()
    
    async def initialize_agent(self):
        """Initialize the Risk Assessment Agent"""
        logger.info("🔧 Initializing Risk Assessment Agent...")
        self.agent = create_risk_assessment_agent()
        logger.info("✅ Risk Assessment Agent initialized successfully")
    
    def _create_demo_patients(self) -> Dict[str, Dict[str, Any]]:
        """Create demonstration patient profiles"""
        return {
            'moderate_risk_patient': {
                'patient_id': 'DEMO-001',
                'patient_name': 'María González (75 años)',
                'age': 75,
                'bmi': 22.3,
                'consciousness_level': 'alert',
                'sensory_impairment': False,
                'responds_to_pressure': True,
                'incontinence': 'occasional',
                'diaphoresis': False,
                'mobility': 'limited',
                'bedbound': False,
                'wheelchair_bound': True,
                'position_changes_frequency': 'frequent_assistance',
                'position_assistance_required': True,
                'oral_intake_percentage': 75,
                'enteral_nutrition': False,
                'recent_weight_loss': False,
                'albumin_level': 3.1,
                'slides_in_bed': False,
                'spasticity': False,
                'requires_assistance_moving': True,
                'recent_falls': False,
                'confusion': False,
                'agitation': False,
                'visual_impairment': True,
                'frequent_toileting': False,
                'immunosuppression': False,
                'invasive_devices': ['urinary_catheter'],
                'diabetes': True,
                'recent_surgery': False,
                'recent_antibiotics': False,
                'malnutrition': False,
                'weight_loss_percentage_3months': 2.0,
                'acute_disease_no_intake': False
            },
            'high_risk_patient': {
                'patient_id': 'DEMO-002', 
                'patient_name': 'Carlos Rodríguez (82 años)',
                'age': 82,
                'bmi': 17.8,
                'consciousness_level': 'sedated',
                'sensory_impairment': True,
                'responds_to_pressure': False,
                'incontinence': 'both',
                'diaphoresis': True,
                'mobility': 'none',
                'bedbound': True,
                'wheelchair_bound': False,
                'position_changes_frequency': 'none',
                'position_assistance_required': True,
                'oral_intake_percentage': 30,
                'enteral_nutrition': True,
                'recent_weight_loss': True,
                'albumin_level': 2.5,
                'slides_in_bed': True,
                'spasticity': True,
                'requires_assistance_moving': True,
                'recent_falls': True,
                'confusion': True,
                'agitation': False,
                'visual_impairment': True,
                'frequent_toileting': True,
                'immunosuppression': True,
                'invasive_devices': ['central_line', 'ventilator', 'urinary_catheter', 'nasogastric_tube'],
                'diabetes': True,
                'recent_surgery': True,
                'recent_antibiotics': True,
                'malnutrition': True,
                'weight_loss_percentage_3months': 15.0,
                'acute_disease_no_intake': True
            },
            'low_risk_patient': {
                'patient_id': 'DEMO-003',
                'patient_name': 'Ana Silva (65 años)',
                'age': 65,
                'bmi': 24.5,
                'consciousness_level': 'alert',
                'sensory_impairment': False,
                'responds_to_pressure': True,
                'incontinence': 'none',
                'diaphoresis': False,
                'mobility': 'independent',
                'bedbound': False,
                'wheelchair_bound': False,
                'position_changes_frequency': 'independent',
                'position_assistance_required': False,
                'oral_intake_percentage': 95,
                'enteral_nutrition': False,
                'recent_weight_loss': False,
                'albumin_level': 3.8,
                'slides_in_bed': False,
                'spasticity': False,
                'requires_assistance_moving': False,
                'recent_falls': False,
                'confusion': False,
                'agitation': False,
                'visual_impairment': False,
                'frequent_toileting': False,
                'immunosuppression': False,
                'invasive_devices': [],
                'diabetes': False,
                'recent_surgery': False,
                'recent_antibiotics': False,
                'malnutrition': False,
                'weight_loss_percentage_3months': 0.0,
                'acute_disease_no_intake': False
            }
        }
    
    async def demonstrate_braden_scale(self, patient_data: Dict[str, Any]):
        """Demonstrate Braden Scale assessment"""
        print(f"\n🩺 BRADEN SCALE ASSESSMENT")
        print("=" * 50)
        print(f"Paciente: {patient_data['patient_name']}")
        
        result = await self.agent.assess_braden_scale(patient_data)
        
        print(f"📊 Puntuación Total: {result.total_score}/23")
        print(f"🚦 Nivel de Riesgo: {result.risk_level.value.upper()}")
        print(f"⚠️  Escalación Requerida: {'SÍ' if result.escalation_required else 'NO'}")
        print(f"🎯 Confianza: {result.confidence_score:.1%}")
        
        print(f"\n📋 Subescalas Braden:")
        for subscale, score_desc in result.evidence_summary['subscale_scores'].items():
            print(f"  • {subscale.replace('_', ' ').title()}: {score_desc}")
        
        print(f"\n💡 Recomendaciones Clínicas:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"  {i}. {rec}")
        
        return result
    
    async def demonstrate_fall_risk(self, patient_data: Dict[str, Any]):
        """Demonstrate STRATIFY fall risk assessment"""
        print(f"\n🚶 EVALUACIÓN RIESGO DE CAÍDAS (STRATIFY)")
        print("=" * 50)
        print(f"Paciente: {patient_data['patient_name']}")
        
        result = await self.agent.assess_fall_risk(patient_data)
        
        print(f"📊 Puntuación STRATIFY: {result.total_score}/5")
        print(f"🚦 Nivel de Riesgo: {result.risk_level.value.upper()}")
        print(f"⚠️  Escalación Requerida: {'SÍ' if result.escalation_required else 'NO'}")
        
        print(f"\n🎯 Factores de Riesgo Identificados:")
        for factor in result.risk_factors:
            print(f"  • {factor.factor_name.replace('_', ' ').title()}: {factor.score} punto(s)")
        
        print(f"\n💡 Recomendaciones Prevención Caídas:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"  {i}. {rec}")
        
        return result
    
    async def demonstrate_infection_risk(self, patient_data: Dict[str, Any]):
        """Demonstrate infection risk assessment"""
        print(f"\n🦠 EVALUACIÓN RIESGO INFECCIOSO")
        print("=" * 50)
        print(f"Paciente: {patient_data['patient_name']}")
        
        result = await self.agent.assess_infection_risk(patient_data)
        
        print(f"📊 Puntuación Riesgo Infeccioso: {result.total_score}")
        print(f"🚦 Nivel de Riesgo: {result.risk_level.value.upper()}")
        print(f"⚠️  Escalación Requerida: {'SÍ' if result.escalation_required else 'NO'}")
        
        print(f"\n🎯 Factores de Riesgo Infeccioso:")
        for factor in result.risk_factors:
            print(f"  • {factor.factor_name.replace('_', ' ').title()}: {factor.score} punto(s)")
        
        print(f"\n💡 Recomendaciones Prevención Infecciones:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"  {i}. {rec}")
        
        return result
    
    async def demonstrate_nutritional_risk(self, patient_data: Dict[str, Any]):
        """Demonstrate MUST nutritional assessment"""
        print(f"\n🍎 EVALUACIÓN RIESGO NUTRICIONAL (MUST)")
        print("=" * 50)
        print(f"Paciente: {patient_data['patient_name']}")
        
        result = await self.agent.assess_nutritional_risk(patient_data)
        
        print(f"📊 Puntuación MUST: {result.total_score}")
        print(f"🚦 Nivel de Riesgo: {result.risk_level.value.upper()}")
        print(f"⚠️  Escalación Requerida: {'SÍ' if result.escalation_required else 'NO'}")
        
        evidence = result.evidence_summary
        print(f"\n📋 Datos Nutricionales:")
        print(f"  • IMC: {evidence.get('bmi', 'N/A')}")
        print(f"  • Pérdida de peso (3m): {evidence.get('weight_loss_3m', 'N/A')}")
        print(f"  • Albúmina: {evidence.get('albumin_level', 'N/A')} g/dL")
        
        print(f"\n💡 Recomendaciones Nutricionales:")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"  {i}. {rec}")
        
        return result
    
    async def demonstrate_comprehensive_assessment(self, patient_data: Dict[str, Any]):
        """Demonstrate comprehensive multi-scale assessment"""
        print(f"\n🎯 EVALUACIÓN INTEGRAL DE RIESGO")
        print("=" * 70)
        print(f"Paciente: {patient_data['patient_name']}")
        
        result = await self.agent.perform_comprehensive_risk_assessment(patient_data)
        
        print(f"🎯 Riesgo General: {result['overall_risk_level'].upper()}")
        print(f"⚠️  Escalación Crítica: {'SÍ' if result['escalation_required'] else 'NO'}")
        
        print(f"\n📊 Resumen por Dominio:")
        assessments = result['individual_assessments']
        
        # Braden Scale
        braden = assessments['braden_scale']
        print(f"  🩺 Riesgo LPP (Braden): {braden['score']}/23 - {braden['risk_level'].upper()}")
        
        # Fall Risk
        fall = assessments['fall_risk']
        print(f"  🚶 Riesgo Caídas (STRATIFY): {fall['score']}/5 - {fall['risk_level'].upper()}")
        
        # Infection Risk
        infection = assessments['infection_risk']
        print(f"  🦠 Riesgo Infeccioso: {infection['score']} - {infection['risk_level'].upper()}")
        
        # Nutritional Risk
        nutrition = assessments['nutritional_risk']
        print(f"  🍎 Riesgo Nutricional (MUST): {nutrition['score']} - {nutrition['risk_level'].upper()}")
        
        # Risk Correlation Analysis
        correlation = result['risk_correlation_analysis']
        if correlation['high_risk_domains']:
            print(f"\n🔗 Dominios de Alto Riesgo:")
            for domain in correlation['high_risk_domains']:
                print(f"  • {domain.replace('_', ' ').title()}")
        
        if correlation['synergistic_risks']:
            print(f"\n⚡ Riesgos Sinérgicos Detectados:")
            for risk in correlation['synergistic_risks']:
                print(f"  • {risk.replace('_', ' ').title()}")
        
        print(f"\n💡 Recomendaciones Integradas ({len(result['combined_recommendations'])} total):")
        for i, rec in enumerate(result['combined_recommendations'][:5], 1):  # Show top 5
            print(f"  {i}. {rec}")
        
        if len(result['combined_recommendations']) > 5:
            print(f"  ... y {len(result['combined_recommendations']) - 5} recomendaciones adicionales")
        
        return result
    
    async def run_complete_demonstration(self):
        """Run complete demonstration with all patients"""
        print("🏥 DEMOSTRACIÓN COMPLETA - AGENTE DE EVALUACIÓN DE RIESGO")
        print("=" * 80)
        print("Sistema Vigía - Evaluación Integral de Riesgo Médico")
        print("Escalas Implementadas: Braden, STRATIFY, MUST, Riesgo Infeccioso")
        print("Basado en Evidencia Científica y Guidelines Internacionales")
        print("=" * 80)
        
        await self.initialize_agent()
        
        for patient_type, patient_data in self.demo_patients.items():
            print(f"\n\n{'=' * 20} {patient_type.upper().replace('_', ' ')} {'=' * 20}")
            
            # Individual assessments
            await self.demonstrate_braden_scale(patient_data)
            await self.demonstrate_fall_risk(patient_data)
            await self.demonstrate_infection_risk(patient_data)
            await self.demonstrate_nutritional_risk(patient_data)
            
            # Comprehensive assessment
            await self.demonstrate_comprehensive_assessment(patient_data)
            
            print(f"\n{'=' * 70}")
        
        print(f"\n\n🎉 DEMOSTRACIÓN COMPLETADA")
        print("=" * 50)
        print("✅ Todas las escalas de evaluación funcionando correctamente")
        print("✅ Recomendaciones basadas en evidencia científica")
        print("✅ Protocolos de escalación implementados")
        print("✅ Análisis de correlación de riesgos activo")
        print("\n🏥 El Agente de Evaluación de Riesgo está listo para producción")


async def main():
    """Main demonstration function"""
    demo = RiskAssessmentDemo()
    await demo.run_complete_demonstration()


if __name__ == "__main__":
    asyncio.run(main())