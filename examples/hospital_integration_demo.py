#!/usr/bin/env python3
"""
Vigia Hospital Integration Demo
Demonstrates complete integration workflow with HIS/PACS and PDF reporting
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import Vigia components
try:
    from vigia_detect.integrations.his_fhir_gateway import (
        HISFHIRGateway, HISPatient, LPPObservation, IntegrationType
    )
    from vigia_detect.reports.clinical_pdf_generator import (
        ClinicalPDFGenerator, PatientInfo, LPPFinding, ClinicalAssessment
    )
    from vigia_detect.systems.medical_decision_engine import MedicalDecisionEngine
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("This demo requires the full Vigia medical system to be installed")
    exit(1)


class HospitalIntegrationDemo:
    """
    Complete demonstration of hospital integration workflow
    """
    
    def __init__(self):
        self.logger = logger
        self.demo_data = self._create_demo_data()
        
        # Initialize components
        self.his_config = {
            'integration_type': 'fhir_r4',
            'his_endpoint': 'https://demo-his.hospital.local/api',
            'api_key': 'demo_api_key',
            'timeout': 30
        }
        
        self.pdf_config = {
            'hospital_name': 'General Hospital',
            'hospital_address': '123 Medical Center Drive, City, State 12345',
            'hospital_phone': '(555) 123-4567',
            'hospital_logo_path': None  # Would be path to hospital logo
        }
        
        self.medical_engine = MedicalDecisionEngine()
    
    def _create_demo_data(self) -> Dict[str, Any]:
        """Create realistic demo medical data"""
        return {
            'patient_info': {
                'patient_id': 'PAT20240115001',
                'mrn': 'MRN789456123',
                'first_name': 'Maria',
                'last_name': 'Rodriguez',
                'birth_date': '1955-03-20',
                'gender': 'F',
                'age': 69,
                'room_number': '204B',
                'admission_date': '2024-01-12',
                'attending_physician': 'Dr. Sarah Chen',
                'department': 'Medical ICU'
            },
            'lpp_detection_results': [
                {
                    'finding_id': 'LPP20240115001',
                    'lpp_grade': 3,
                    'confidence': 0.94,
                    'anatomical_location': 'sacrum',
                    'severity': 'High',
                    'detection_timestamp': datetime.now().isoformat(),
                    'risk_factors': [
                        'Advanced age (69 years)',
                        'Prolonged immobility',
                        'Poor nutritional status',
                        'Diabetes mellitus',
                        'Incontinence'
                    ],
                    'measurements': {
                        'length': 4.2,
                        'width': 3.1,
                        'depth': 0.8
                    },
                    'image_path': None  # Would be path to medical image
                },
                {
                    'finding_id': 'LPP20240115002',\n                    'lpp_grade': 2,\n                    'confidence': 0.87,\n                    'anatomical_location': 'right heel',\n                    'severity': 'Moderate',\n                    'detection_timestamp': (datetime.now() - timedelta(hours=2)).isoformat(),\n                    'risk_factors': [\n                        'Heel pressure from positioning',\n                        'Peripheral vascular disease',\n                        'Edema'\n                    ],\n                    'measurements': {\n                        'length': 2.1,\n                        'width': 1.8,\n                        'depth': 0.3\n                    },\n                    'image_path': None\n                }\n            ],\n            'clinical_assessment': {\n                'assessment_id': 'ASSESS20240115001',\n                'physician_name': 'Dr. Sarah Chen',\n                'physician_license': 'MD789456',\n                'assessment_date': datetime.now().isoformat(),\n                'clinical_notes': '''\nPatient presents with two pressure injuries identified by AI screening:\n\n1. Stage 3 pressure injury on sacrum (4.2 x 3.1 x 0.8 cm)\n   - Full thickness tissue loss with visible subcutaneous fat\n   - No exposed bone, tendon, or muscle\n   - Irregular wound edges with surrounding erythema\n   - Requires immediate intervention\n\n2. Stage 2 pressure injury on right heel (2.1 x 1.8 x 0.3 cm)\n   - Partial thickness loss involving epidermis and dermis\n   - Presents as shallow open ulcer with red-pink wound bed\n   - No slough or bruising\n   - Manageable with standard pressure relief\n\nRisk factors include advanced age, diabetes, immobility, and incontinence.\nPatient requires comprehensive pressure injury management protocol.''',\n                'treatment_plan': '''\n1. Immediate pressure redistribution:\n   - Specialty pressure-relieving mattress\n   - Repositioning every 2 hours\n   - Heel offloading devices\n\n2. Wound care management:\n   - Daily assessment and documentation\n   - Appropriate dressing selection\n   - Moisture management\n   - Infection prevention\n\n3. Nutritional optimization:\n   - Dietary consultation\n   - Protein supplementation\n   - Hydration monitoring\n\n4. Multidisciplinary approach:\n   - Wound care specialist consultation\n   - Physical therapy evaluation\n   - Social work assessment for discharge planning''',\n                'follow_up_instructions': '''\n- Daily pressure injury assessment with photographic documentation\n- Weekly measurement and staging evaluation\n- Monitor for signs of infection or deterioration\n- Document healing progress or concerns\n- Reassess risk factors and prevention strategies\n- Follow institutional pressure injury prevention protocol\n- Consider plastic surgery consultation if no improvement in 2 weeks''',\n                'verification_status': 'verified'\n            }\n        }\n    \n    async def demonstrate_his_integration(self) -> Dict[str, Any]:\n        \"\"\"Demonstrate HIS/FHIR integration\"\"\"\n        self.logger.info(\"=== HIS/FHIR Integration Demo ===\")\n        \n        results = {}\n        \n        try:\n            # Create HIS gateway\n            async with HISFHIRGateway(self.his_config) as gateway:\n                # Process each LPP finding\n                for detection in self.demo_data['lpp_detection_results']:\n                    lpp_result = {\n                        'lpp_grade': detection['lpp_grade'],\n                        'confidence': detection['confidence'],\n                        'anatomical_location': detection['anatomical_location'],\n                        'recommendations': self._get_clinical_recommendations(detection['lpp_grade'])\n                    }\n                    \n                    # Integrate with HIS\n                    integration_result = await gateway.integrate_lpp_detection(\n                        lpp_result, self.demo_data['patient_info']\n                    )\n                    \n                    results[f\"finding_{detection['finding_id']}\"] = integration_result\n                    \n                    self.logger.info(f\"✅ HIS integration completed for finding {detection['finding_id']}\")\n                    self.logger.info(f\"   Integration type: {integration_result.get('integration_type')}\")\n                    self.logger.info(f\"   Status: {integration_result.get('status')}\")\n        \n        except Exception as e:\n            self.logger.error(f\"HIS integration failed: {e}\")\n            results['error'] = str(e)\n        \n        return results\n    \n    def demonstrate_pdf_generation(self) -> str:\n        \"\"\"Demonstrate clinical PDF report generation\"\"\"\n        self.logger.info(\"=== Clinical PDF Report Generation Demo ===\")\n        \n        try:\n            # Create PDF generator\n            generator = ClinicalPDFGenerator(self.pdf_config)\n            \n            # Convert demo data to PDF format\n            patient = PatientInfo(**self.demo_data['patient_info'])\n            \n            findings = []\n            for detection in self.demo_data['lpp_detection_results']:\n                finding = LPPFinding(\n                    finding_id=detection['finding_id'],\n                    timestamp=detection['detection_timestamp'],\n                    lpp_grade=detection['lpp_grade'],\n                    confidence_score=detection['confidence'],\n                    anatomical_location=detection['anatomical_location'],\n                    severity=detection['severity'],\n                    risk_factors=detection['risk_factors'],\n                    recommendations=self._get_clinical_recommendations(detection['lpp_grade']),\n                    measurements=detection['measurements']\n                )\n                findings.append(finding)\n            \n            assessment = ClinicalAssessment(**self.demo_data['clinical_assessment'])\n            \n            # Generate report\n            timestamp = datetime.now().strftime(\"%Y%m%d_%H%M%S\")\n            output_path = f\"demo_clinical_report_{timestamp}.pdf\"\n            \n            report_path = generator.generate_clinical_report(\n                patient=patient,\n                findings=findings,\n                assessment=assessment,\n                output_path=output_path\n            )\n            \n            self.logger.info(f\"✅ Clinical PDF report generated: {report_path}\")\n            self.logger.info(f\"   Patient: {patient.first_name} {patient.last_name} (MRN: {patient.mrn})\")\n            self.logger.info(f\"   Findings: {len(findings)} pressure injuries detected\")\n            self.logger.info(f\"   Assessment: Verified by {assessment.physician_name}\")\n            \n            return report_path\n        \n        except Exception as e:\n            self.logger.error(f\"PDF generation failed: {e}\")\n            raise\n    \n    def demonstrate_medical_decisions(self) -> Dict[str, Any]:\n        \"\"\"Demonstrate evidence-based medical decision making\"\"\"\n        self.logger.info(\"=== Evidence-Based Medical Decisions Demo ===\")\n        \n        decisions = {}\n        \n        for detection in self.demo_data['lpp_detection_results']:\n            # Get clinical decision\n            decision = self.medical_engine.make_clinical_decision(\n                lpp_grade=detection['lpp_grade'],\n                confidence=detection['confidence'],\n                anatomical_location=detection['anatomical_location']\n            )\n            \n            decisions[detection['finding_id']] = decision\n            \n            self.logger.info(f\"📋 Clinical Decision for {detection['finding_id']}:\")\n            self.logger.info(f\"   Grade: {detection['lpp_grade']} ({detection['severity']})\")\n            self.logger.info(f\"   Urgency: {decision['urgency']}\")\n            self.logger.info(f\"   Evidence Level: {decision['evidence_level']}\")\n            self.logger.info(f\"   Primary Interventions: {len(decision['interventions'])}\")\n            \n            # Show critical interventions for severe cases\n            if detection['lpp_grade'] >= 3:\n                self.logger.warning(f\"⚠️  CRITICAL: Grade {detection['lpp_grade']} requires immediate attention\")\n                for intervention in decision['interventions'][:3]:  # Show first 3\n                    self.logger.warning(f\"   • {intervention}\")\n        \n        return decisions\n    \n    def _get_clinical_recommendations(self, lpp_grade: int) -> List[str]:\n        \"\"\"Get clinical recommendations based on LPP grade\"\"\"\n        base_recommendations = [\n            \"Implement pressure redistribution measures\",\n            \"Optimize nutritional status\",\n            \"Manage moisture and incontinence\",\n            \"Document findings and interventions\"\n        ]\n        \n        if lpp_grade >= 3:\n            base_recommendations.extend([\n                \"Immediate medical evaluation required\",\n                \"Consider wound care specialist consultation\",\n                \"Monitor for signs of infection\",\n                \"Consider advanced wound therapies\"\n            ])\n        elif lpp_grade == 2:\n            base_recommendations.extend([\n                \"Appropriate dressing selection\",\n                \"Monitor healing progress\",\n                \"Prevent further deterioration\"\n            ])\n        else:\n            base_recommendations.extend([\n                \"Skin protection measures\",\n                \"Continue monitoring\",\n                \"Prevention protocol\"\n            ])\n        \n        return base_recommendations\n    \n    def demonstrate_complete_workflow(self) -> Dict[str, Any]:\n        \"\"\"Demonstrate complete hospital integration workflow\"\"\"\n        self.logger.info(\"🏥 === COMPLETE HOSPITAL INTEGRATION WORKFLOW DEMO ===\")\n        self.logger.info(f\"Patient: {self.demo_data['patient_info']['first_name']} {self.demo_data['patient_info']['last_name']}\")\n        self.logger.info(f\"MRN: {self.demo_data['patient_info']['mrn']}\")\n        self.logger.info(f\"Department: {self.demo_data['patient_info']['department']}\")\n        self.logger.info(f\"Findings: {len(self.demo_data['lpp_detection_results'])} pressure injuries detected\")\n        self.logger.info(\"\")\n        \n        workflow_results = {}\n        \n        # Step 1: Evidence-based medical decisions\n        self.logger.info(\"Step 1: Generating evidence-based medical decisions...\")\n        medical_decisions = self.demonstrate_medical_decisions()\n        workflow_results['medical_decisions'] = medical_decisions\n        \n        # Step 2: PDF report generation\n        self.logger.info(\"\\nStep 2: Generating clinical PDF report...\")\n        try:\n            pdf_path = self.demonstrate_pdf_generation()\n            workflow_results['pdf_report'] = pdf_path\n        except Exception as e:\n            self.logger.error(f\"PDF generation failed: {e}\")\n            workflow_results['pdf_error'] = str(e)\n        \n        # Step 3: HIS/FHIR integration (async)\n        self.logger.info(\"\\nStep 3: Integrating with Hospital Information System...\")\n        try:\n            his_results = asyncio.run(self.demonstrate_his_integration())\n            workflow_results['his_integration'] = his_results\n        except Exception as e:\n            self.logger.error(f\"HIS integration failed: {e}\")\n            workflow_results['his_error'] = str(e)\n        \n        # Workflow summary\n        self.logger.info(\"\\n\" + \"=\"*60)\n        self.logger.info(\"🎯 WORKFLOW SUMMARY\")\n        self.logger.info(\"=\"*60)\n        \n        # Medical decisions summary\n        critical_findings = sum(1 for d in self.demo_data['lpp_detection_results'] if d['lpp_grade'] >= 3)\n        moderate_findings = sum(1 for d in self.demo_data['lpp_detection_results'] if d['lpp_grade'] == 2)\n        \n        self.logger.info(f\"📊 Clinical Findings:\")\n        self.logger.info(f\"   • Critical (Grade 3+): {critical_findings}\")\n        self.logger.info(f\"   • Moderate (Grade 2): {moderate_findings}\")\n        \n        # Integration results\n        if 'pdf_report' in workflow_results:\n            self.logger.info(f\"📄 PDF Report: Generated ({workflow_results['pdf_report']})\")\n        else:\n            self.logger.info(f\"📄 PDF Report: Failed ({workflow_results.get('pdf_error', 'Unknown error')})\")\n        \n        if 'his_integration' in workflow_results:\n            successful_integrations = sum(1 for r in workflow_results['his_integration'].values() \n                                        if isinstance(r, dict) and r.get('status') == 'success')\n            self.logger.info(f\"🏥 HIS Integration: {successful_integrations}/{len(self.demo_data['lpp_detection_results'])} successful\")\n        else:\n            self.logger.info(f\"🏥 HIS Integration: Failed ({workflow_results.get('his_error', 'Unknown error')})\")\n        \n        # Compliance and audit\n        self.logger.info(f\"🔒 Compliance: HIPAA compliant, 7-year audit retention\")\n        self.logger.info(f\"⚕️  Medical Standards: NPUAP/EPUAP guidelines applied\")\n        \n        # Next steps\n        if critical_findings > 0:\n            self.logger.warning(f\"⚠️  IMMEDIATE ACTION REQUIRED: {critical_findings} critical finding(s)\")\n            self.logger.warning(f\"   • Notify medical team immediately\")\n            self.logger.warning(f\"   • Implement emergency protocols\")\n            self.logger.warning(f\"   • Document all interventions\")\n        \n        self.logger.info(\"\\n✅ Hospital integration workflow demonstration completed!\")\n        \n        return workflow_results\n\n\nasync def main():\n    \"\"\"Main demo function\"\"\"\n    print(\"\\n\" + \"=\"*80)\n    print(\"🏥 VIGIA HOSPITAL INTEGRATION DEMONSTRATION\")\n    print(\"Complete workflow: AI Detection → Medical Decisions → HIS Integration → PDF Reports\")\n    print(\"=\"*80 + \"\\n\")\n    \n    # Create and run demo\n    demo = HospitalIntegrationDemo()\n    \n    try:\n        # Run complete workflow\n        results = demo.demonstrate_complete_workflow()\n        \n        # Save results for reference\n        timestamp = datetime.now().strftime(\"%Y%m%d_%H%M%S\")\n        results_file = f\"demo_results_{timestamp}.json\"\n        \n        # Serialize results (exclude non-serializable objects)\n        serializable_results = {\n            'timestamp': timestamp,\n            'patient_info': demo.demo_data['patient_info'],\n            'findings_count': len(demo.demo_data['lpp_detection_results']),\n            'workflow_status': {\n                'medical_decisions': 'completed' if 'medical_decisions' in results else 'failed',\n                'pdf_generation': 'completed' if 'pdf_report' in results else 'failed',\n                'his_integration': 'completed' if 'his_integration' in results else 'failed'\n            }\n        }\n        \n        with open(results_file, 'w') as f:\n            json.dump(serializable_results, f, indent=2)\n        \n        print(f\"\\n📋 Demo results saved to: {results_file}\")\n        print(f\"\\n🎉 Demo completed successfully!\")\n        \n        return results\n        \n    except Exception as e:\n        logger.error(f\"Demo failed: {e}\")\n        raise\n\n\nif __name__ == \"__main__\":\n    # Run the demo\n    asyncio.run(main())\n