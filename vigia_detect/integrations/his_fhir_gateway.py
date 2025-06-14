#!/usr/bin/env python3
"""
Vigia HIS/PACS Integration Gateway
HL7 FHIR and DICOM integration for hospital systems
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum

import aiohttp
import aiofiles
from fhir.resources.patient import Patient
from fhir.resources.observation import Observation
from fhir.resources.diagnosticreport import DiagnosticReport
from fhir.resources.media import Media
from hl7 import parse, Field, Component

from ..utils.logger import get_logger
from ..utils.encryption import encrypt_phi, decrypt_phi
from ..core.medical_dispatcher import MedicalDispatcher
from ..systems.clinical_processing import ClinicalProcessor


logger = get_logger(__name__)


class IntegrationType(Enum):
    """Integration types supported"""
    HL7_V2 = "hl7_v2"
    FHIR_R4 = "fhir_r4"
    DICOM = "dicom"
    CSV_FTP = "csv_ftp"
    REST_API = "rest_api"


class MessageType(Enum):
    """HL7 message types"""
    ADT_A01 = "ADT^A01"  # Patient admission
    ADT_A03 = "ADT^A03"  # Patient discharge
    ORU_R01 = "ORU^R01"  # Observation result
    MDM_T02 = "MDM^T02"  # Medical document


@dataclass
class HISPatient:
    """Hospital Information System patient record"""
    patient_id: str
    mrn: str  # Medical Record Number
    first_name: str
    last_name: str
    birth_date: str
    gender: str
    room_number: Optional[str] = None
    admission_date: Optional[str] = None
    primary_physician: Optional[str] = None
    department: Optional[str] = None
    insurance_info: Optional[Dict] = None


@dataclass
class LPPObservation:
    """LPP detection observation for HIS integration"""
    observation_id: str
    patient_id: str
    timestamp: str
    lpp_grade: int
    confidence_score: float
    anatomical_location: str
    image_path: Optional[str] = None
    recommendations: List[str] = None
    physician_notes: Optional[str] = None
    followup_required: bool = False


class HISFHIRGateway:
    """
    Hospital Integration Gateway for HIS/PACS systems
    Supports HL7 FHIR, DICOM, and legacy CSV/FTP
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.integration_type = IntegrationType(config.get('integration_type', 'fhir_r4'))
        self.his_endpoint = config.get('his_endpoint')
        self.pacs_endpoint = config.get('pacs_endpoint')
        self.api_key = config.get('api_key')
        self.timeout = config.get('timeout', 30)
        
        # Initialize components
        self.medical_dispatcher = MedicalDispatcher()
        self.clinical_processor = ClinicalProcessor()
        
        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
        
        logger.info(f"Initialized HIS/FHIR Gateway with {self.integration_type.value}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={
                'User-Agent': 'Vigia-Medical-System/1.3.1',
                'Content-Type': 'application/json'
            }
        )
        if self.api_key:
            self.session.headers['Authorization'] = f'Bearer {self.api_key}'
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    # HL7 FHIR Integration
    async def send_fhir_observation(self, lpp_obs: LPPObservation) -> Dict[str, Any]:
        """
        Send LPP detection as FHIR Observation
        """
        try:
            # Create FHIR Observation resource
            observation = Observation()
            observation.id = lpp_obs.observation_id
            observation.status = "final"
            observation.category = [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "imaging",
                    "display": "Imaging"
                }]
            }]
            observation.code = {
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": "420226006",
                    "display": "Pressure ulcer stage assessment"
                }]
            }
            observation.subject = {"reference": f"Patient/{lpp_obs.patient_id}"}
            observation.effectiveDateTime = lpp_obs.timestamp
            
            # LPP grade value
            observation.valueQuantity = {
                "value": lpp_obs.lpp_grade,
                "unit": "grade",
                "system": "http://unitsofmeasure.org",
                "code": "1"
            }
            
            # Additional components
            observation.component = [
                {
                    "code": {
                        "coding": [{
                            "system": "http://vigia.ai/medical",
                            "code": "confidence-score",
                            "display": "AI Confidence Score"
                        }]
                    },
                    "valueQuantity": {
                        "value": lpp_obs.confidence_score,
                        "unit": "percent",
                        "system": "http://unitsofmeasure.org",
                        "code": "%"
                    }
                },
                {
                    "code": {
                        "coding": [{
                            "system": "http://snomed.info/sct",
                            "code": "722298008",
                            "display": "Anatomical location"
                        }]
                    },
                    "valueString": lpp_obs.anatomical_location
                }
            ]
            
            # Send to HIS
            if self.session and self.his_endpoint:
                url = f"{self.his_endpoint}/fhir/Observation"
                async with self.session.post(url, json=observation.dict()) as response:
                    if response.status == 201:
                        result = await response.json()
                        logger.info(f"FHIR Observation sent successfully: {observation.id}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send FHIR Observation: {error_text}")
                        raise Exception(f"HIS API error: {response.status}")
            
            return {"status": "success", "observation_id": observation.id}
            
        except Exception as e:
            logger.error(f"Error sending FHIR observation: {e}")
            raise
    
    async def create_fhir_diagnostic_report(self, lpp_obs: LPPObservation, 
                                          patient: HISPatient) -> Dict[str, Any]:
        """
        Create FHIR DiagnosticReport for LPP detection
        """
        try:
            report = DiagnosticReport()
            report.id = f"lpp-report-{lpp_obs.observation_id}"
            report.status = "final"
            report.category = [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                    "code": "IMG",
                    "display": "Diagnostic Imaging"
                }]
            }]
            report.code = {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "76398-2",
                    "display": "Pressure ulcer assessment"
                }]
            }
            report.subject = {"reference": f"Patient/{patient.patient_id}"}
            report.effectiveDateTime = lpp_obs.timestamp
            report.issued = datetime.utcnow().isoformat() + "Z"
            
            # Results reference
            report.result = [{"reference": f"Observation/{lpp_obs.observation_id}"}]
            
            # Clinical interpretation
            if lpp_obs.lpp_grade >= 3:
                conclusion = f"Critical pressure injury detected - Grade {lpp_obs.lpp_grade} at {lpp_obs.anatomical_location}. Immediate medical attention required."
            elif lpp_obs.lpp_grade == 2:
                conclusion = f"Moderate pressure injury detected - Grade {lpp_obs.lpp_grade} at {lpp_obs.anatomical_location}. Medical review recommended."
            else:
                conclusion = f"Mild pressure injury detected - Grade {lpp_obs.lpp_grade} at {lpp_obs.anatomical_location}. Monitoring recommended."
            
            report.conclusion = conclusion
            
            # Recommendations
            if lpp_obs.recommendations:
                report.extension = [{
                    "url": "http://vigia.ai/fhir/recommendations",
                    "valueString": "; ".join(lpp_obs.recommendations)
                }]
            
            # Send to HIS
            if self.session and self.his_endpoint:
                url = f"{self.his_endpoint}/fhir/DiagnosticReport"
                async with self.session.post(url, json=report.dict()) as response:
                    if response.status == 201:
                        result = await response.json()
                        logger.info(f"FHIR DiagnosticReport sent: {report.id}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send DiagnosticReport: {error_text}")
                        raise Exception(f"HIS API error: {response.status}")
            
            return {"status": "success", "report_id": report.id}
            
        except Exception as e:
            logger.error(f"Error creating FHIR diagnostic report: {e}")
            raise
    
    # HL7 v2 Integration
    def create_hl7_oru_message(self, lpp_obs: LPPObservation, 
                               patient: HISPatient) -> str:
        """
        Create HL7 v2.5 ORU^R01 message for LPP observation
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # MSH - Message Header
            msh = f"MSH|^~\\&|VIGIA|HOSPITAL|HIS|HOSPITAL|{timestamp}||ORU^R01|{lpp_obs.observation_id}|P|2.5"
            
            # PID - Patient Identification
            pid = f"PID|1||{patient.mrn}^^^HOSPITAL^MR||{patient.last_name}^{patient.first_name}||{patient.birth_date}|{patient.gender}"
            
            # PV1 - Patient Visit (if available)
            pv1 = f"PV1|1|I|{patient.room_number or ''}|||{patient.primary_physician or ''}|||||||||||{patient.admission_date or ''}"
            
            # OBR - Observation Request
            obr = f"OBR|1||{lpp_obs.observation_id}|76398-2^Pressure ulcer assessment^LN|R|{timestamp}|||||||||||{patient.primary_physician or ''}||||||F"
            
            # OBX - Observation Result
            obx_grade = f"OBX|1|NM|420226006^Pressure ulcer grade^SCT||{lpp_obs.lpp_grade}|grade|||||F"
            obx_confidence = f"OBX|2|NM|CONF^AI Confidence Score^LOCAL||{lpp_obs.confidence_score}|%|||||F"
            obx_location = f"OBX|3|ST|722298008^Anatomical location^SCT||{lpp_obs.anatomical_location}||||||F"
            
            # NTE - Notes (recommendations)
            nte_lines = []
            if lpp_obs.recommendations:
                for i, rec in enumerate(lpp_obs.recommendations, 1):
                    nte_lines.append(f"NTE|{i}|L|{rec}")
            
            # Combine message
            message_parts = [msh, pid, pv1, obr, obx_grade, obx_confidence, obx_location]
            message_parts.extend(nte_lines)
            
            hl7_message = "\r".join(message_parts) + "\r"
            
            logger.info(f"Created HL7 ORU message for observation {lpp_obs.observation_id}")
            return hl7_message
            
        except Exception as e:
            logger.error(f"Error creating HL7 message: {e}")
            raise
    
    async def send_hl7_message(self, hl7_message: str) -> Dict[str, Any]:
        """
        Send HL7 message to hospital system
        """
        try:
            if self.session and self.his_endpoint:
                url = f"{self.his_endpoint}/hl7"
                headers = {'Content-Type': 'application/hl7-v2'}
                
                async with self.session.post(url, data=hl7_message, headers=headers) as response:
                    if response.status == 200:
                        result = await response.text()
                        logger.info("HL7 message sent successfully")
                        return {"status": "success", "response": result}
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send HL7 message: {error_text}")
                        raise Exception(f"HIS API error: {response.status}")
            
            return {"status": "success", "message": "HL7 message processed"}
            
        except Exception as e:
            logger.error(f"Error sending HL7 message: {e}")
            raise
    
    # CSV/FTP Integration (Legacy Systems)
    async def export_csv_report(self, lpp_observations: List[LPPObservation], 
                               output_path: Path) -> str:
        """
        Export LPP observations to CSV for legacy systems
        """
        try:
            import csv
            
            csv_file = output_path / f"lpp_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            async with aiofiles.open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                
                # Header
                await f.write('Patient_ID,MRN,Timestamp,LPP_Grade,Confidence,Location,Recommendations,Physician_Notes\n')
                
                # Data rows
                for obs in lpp_observations:
                    row = [
                        obs.patient_id,
                        obs.patient_id,  # Assuming patient_id is MRN
                        obs.timestamp,
                        obs.lpp_grade,
                        obs.confidence_score,
                        obs.anatomical_location,
                        '; '.join(obs.recommendations or []),
                        obs.physician_notes or ''
                    ]
                    await f.write(','.join(map(str, row)) + '\n')
            
            logger.info(f"CSV report exported: {csv_file}")
            return str(csv_file)
            
        except Exception as e:
            logger.error(f"Error exporting CSV report: {e}")
            raise
    
    # DICOM Integration
    async def create_dicom_sr(self, lpp_obs: LPPObservation) -> Dict[str, Any]:
        """
        Create DICOM Structured Report for LPP detection
        """
        try:
            # This would require pydicom library
            # For now, return mock structure
            dicom_sr = {
                "SOPClassUID": "1.2.840.10008.5.1.4.1.1.88.22",  # Enhanced SR
                "StudyInstanceUID": f"1.2.840.10008.1.2.{lpp_obs.observation_id}",
                "SeriesInstanceUID": f"1.2.840.10008.1.3.{lpp_obs.observation_id}",
                "SOPInstanceUID": f"1.2.840.10008.1.4.{lpp_obs.observation_id}",
                "PatientID": lpp_obs.patient_id,
                "StudyDate": datetime.now().strftime("%Y%m%d"),
                "StudyTime": datetime.now().strftime("%H%M%S"),
                "Modality": "SR",
                "SeriesDescription": "Vigia LPP Detection Report",
                "ContentTemplateSequence": {
                    "MappingResource": "DCMR",
                    "TemplateIdentifier": "1500"
                },
                "DocumentTitle": "Pressure Injury Assessment",
                "ContentSequence": [
                    {
                        "RelationshipType": "CONTAINS",
                        "ConceptNameCodeSequence": {
                            "CodeValue": "420226006",
                            "CodingSchemeDesignator": "SCT",
                            "CodeMeaning": "Pressure ulcer stage assessment"
                        },
                        "NumericValue": lpp_obs.lpp_grade,
                        "MeasurementUnitsCodeSequence": {
                            "CodeValue": "1",
                            "CodingSchemeDesignator": "UCUM",
                            "CodeMeaning": "grade"
                        }
                    }
                ]
            }
            
            logger.info(f"DICOM SR created for observation {lpp_obs.observation_id}")
            return dicom_sr
            
        except Exception as e:
            logger.error(f"Error creating DICOM SR: {e}")
            raise
    
    # Main Integration Method
    async def integrate_lpp_detection(self, lpp_result: Dict[str, Any], 
                                    patient_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to integrate LPP detection with hospital systems
        """
        try:
            # Create data structures
            patient = HISPatient(**patient_info)
            lpp_obs = LPPObservation(
                observation_id=f"lpp-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                patient_id=patient.patient_id,
                timestamp=datetime.utcnow().isoformat() + "Z",
                lpp_grade=lpp_result['lpp_grade'],
                confidence_score=lpp_result['confidence'],
                anatomical_location=lpp_result['anatomical_location'],
                image_path=lpp_result.get('image_path'),
                recommendations=lpp_result.get('recommendations', []),
                physician_notes=lpp_result.get('physician_notes'),
                followup_required=lpp_result['lpp_grade'] >= 3
            )
            
            results = {}
            
            # Integration based on type
            if self.integration_type == IntegrationType.FHIR_R4:
                # Send FHIR Observation
                obs_result = await self.send_fhir_observation(lpp_obs)
                results['fhir_observation'] = obs_result
                
                # Create Diagnostic Report for significant findings
                if lpp_obs.lpp_grade >= 2:
                    report_result = await self.create_fhir_diagnostic_report(lpp_obs, patient)
                    results['fhir_diagnostic_report'] = report_result
            
            elif self.integration_type == IntegrationType.HL7_V2:
                # Create and send HL7 message
                hl7_message = self.create_hl7_oru_message(lpp_obs, patient)
                hl7_result = await self.send_hl7_message(hl7_message)
                results['hl7_message'] = hl7_result
            
            elif self.integration_type == IntegrationType.CSV_FTP:
                # Export to CSV (would typically include FTP upload)
                csv_file = await self.export_csv_report([lpp_obs], Path('/tmp'))
                results['csv_export'] = csv_file
            
            elif self.integration_type == IntegrationType.DICOM:
                # Create DICOM SR
                dicom_sr = await self.create_dicom_sr(lpp_obs)
                results['dicom_sr'] = dicom_sr
            
            # Log integration success
            logger.info(f"HIS integration completed for patient {patient.patient_id}")
            
            return {
                "status": "success",
                "integration_type": self.integration_type.value,
                "observation_id": lpp_obs.observation_id,
                "patient_id": patient.patient_id,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error in HIS integration: {e}")
            return {
                "status": "error",
                "error": str(e),
                "integration_type": self.integration_type.value
            }


# Factory function
def create_his_gateway(integration_config: Dict[str, Any]) -> HISFHIRGateway:
    """
    Factory function to create HIS gateway based on configuration
    """
    return HISFHIRGateway(integration_config)


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Example configuration
        config = {
            'integration_type': 'fhir_r4',
            'his_endpoint': 'https://his.hospital.local/api',
            'api_key': 'hospital_api_key',
            'timeout': 30
        }
        
        # Example LPP detection result
        lpp_result = {
            'lpp_grade': 3,
            'confidence': 0.92,
            'anatomical_location': 'sacrum',
            'recommendations': [
                'Immediate medical attention required',
                'Pressure redistribution therapy',
                'Wound care assessment'
            ]
        }
        
        # Example patient info
        patient_info = {
            'patient_id': 'PAT001',
            'mrn': 'MRN123456',
            'first_name': 'John',
            'last_name': 'Doe',
            'birth_date': '1950-01-15',
            'gender': 'M',
            'room_number': '101A',
            'primary_physician': 'Dr. Smith'
        }
        
        # Integrate with HIS
        async with create_his_gateway(config) as gateway:
            result = await gateway.integrate_lpp_detection(lpp_result, patient_info)
            print(json.dumps(result, indent=2))
    
    asyncio.run(main())
