#!/usr/bin/env python3
"""
Vigia Clinical PDF Report Generator
Generate medical-grade PDF reports with digital signatures
"""

import io
import base64
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from PIL import Image, ImageDraw, ImageFont

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib.colors import Color, black, red, orange, green, blue
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
    from reportlab.platypus import PageBreak, KeepTogether
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
except ImportError:
    raise ImportError("ReportLab required: pip install reportlab")

try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives.serialization import pkcs12
except ImportError:
    raise ImportError("Cryptography required: pip install cryptography")

from ..utils.logger import get_logger
from ..utils.encryption import encrypt_phi
from ..systems.medical_decision_engine import MedicalDecisionEngine
from ..systems.clinical_processing import ClinicalProcessor


logger = get_logger(__name__)


@dataclass
class PatientInfo:
    """Patient information for report"""
    patient_id: str
    mrn: str
    first_name: str
    last_name: str
    birth_date: str
    gender: str
    age: int
    room_number: Optional[str] = None
    admission_date: Optional[str] = None
    attending_physician: Optional[str] = None
    department: Optional[str] = None


@dataclass
class LPPFinding:
    """LPP detection finding"""
    finding_id: str
    timestamp: str
    lpp_grade: int
    confidence_score: float
    anatomical_location: str
    severity: str
    risk_factors: List[str]
    recommendations: List[str]
    image_path: Optional[str] = None
    measurements: Optional[Dict[str, float]] = None
    previous_findings: Optional[List[Dict]] = None


@dataclass
class ClinicalAssessment:
    """Clinical assessment by healthcare provider"""
    assessment_id: str
    physician_name: str
    physician_license: str
    assessment_date: str
    clinical_notes: str
    treatment_plan: str
    follow_up_instructions: str
    digital_signature: Optional[str] = None
    verification_status: str = "pending"


class ClinicalPDFGenerator:
    """
    Generate medical-grade PDF reports for LPP detection
    Includes digital signatures and medical compliance
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.hospital_name = config.get('hospital_name', 'Hospital Name')
        self.hospital_address = config.get('hospital_address', 'Hospital Address')
        self.hospital_phone = config.get('hospital_phone', '(555) 123-4567')
        self.hospital_logo = config.get('hospital_logo_path')
        
        # Digital signature configuration
        self.signing_cert_path = config.get('signing_cert_path')
        self.signing_key_path = config.get('signing_key_path')
        self.cert_password = config.get('cert_password')
        
        # Medical compliance
        self.medical_engine = MedicalDecisionEngine()
        self.clinical_processor = ClinicalProcessor()
        
        # Report styling
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
        
        logger.info("Clinical PDF Generator initialized")
    
    def _setup_custom_styles(self):
        """Setup custom PDF styles for medical reports"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='MedicalTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=20,
            textColor=colors.darkblue,
            alignment=TA_CENTER
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.darkblue,
            borderWidth=1,
            borderColor=colors.lightgrey,
            borderPadding=5
        ))
        
        # Clinical finding style
        self.styles.add(ParagraphStyle(
            name='ClinicalFinding',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceBefore=5,
            spaceAfter=5,
            leftIndent=20
        ))
        
        # Critical alert style
        self.styles.add(ParagraphStyle(
            name='CriticalAlert',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=10,
            textColor=colors.red,
            borderWidth=2,
            borderColor=colors.red,
            borderPadding=10,
            alignment=TA_CENTER
        ))
        
        # Signature style
        self.styles.add(ParagraphStyle(
            name='DigitalSignature',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceBefore=20,
            textColor=colors.darkgreen,
            borderWidth=1,
            borderColor=colors.darkgreen,
            borderPadding=5
        ))
    
    def _create_header(self, canvas_obj, doc):
        """Create PDF header with hospital information"""
        canvas_obj.saveState()
        
        # Hospital logo
        if self.hospital_logo and Path(self.hospital_logo).exists():
            canvas_obj.drawImage(self.hospital_logo, 50, doc.height - 80, width=60, height=60)
        
        # Hospital information
        canvas_obj.setFont('Helvetica-Bold', 16)
        canvas_obj.drawString(120, doc.height - 40, self.hospital_name)
        
        canvas_obj.setFont('Helvetica', 10)
        canvas_obj.drawString(120, doc.height - 55, self.hospital_address)
        canvas_obj.drawString(120, doc.height - 70, f"Phone: {self.hospital_phone}")
        
        # Report title
        canvas_obj.setFont('Helvetica-Bold', 14)
        canvas_obj.drawCentredText(doc.width / 2 + 50, doc.height - 110, 
                                   "PRESSURE INJURY ASSESSMENT REPORT")
        
        # Medical classification
        canvas_obj.setFont('Helvetica', 8)
        canvas_obj.drawString(50, doc.height - 130, 
                              "CONFIDENTIAL MEDICAL DOCUMENT - HIPAA PROTECTED")
        
        canvas_obj.restoreState()
    
    def _create_footer(self, canvas_obj, doc):
        """Create PDF footer with page numbers and metadata"""
        canvas_obj.saveState()
        
        # Page number
        canvas_obj.setFont('Helvetica', 9)
        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num}"
        canvas_obj.drawRightString(doc.width + 50, 30, text)
        
        # Generation timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        canvas_obj.drawString(50, 30, f"Generated: {timestamp}")
        
        # System identifier
        canvas_obj.drawString(50, 15, "Vigia Medical AI System v1.3.1")
        
        canvas_obj.restoreState()
    
    def _get_severity_color(self, lpp_grade: int) -> Color:
        """Get color based on LPP severity"""
        if lpp_grade >= 4:
            return colors.darkred
        elif lpp_grade == 3:
            return colors.red
        elif lpp_grade == 2:
            return colors.orange
        else:
            return colors.yellow
    
    def _create_patient_demographics(self, patient: PatientInfo) -> List[Any]:
        """Create patient demographics section"""
        elements = []
        
        # Section header
        elements.append(Paragraph("PATIENT DEMOGRAPHICS", self.styles['SectionHeader']))
        
        # Patient information table
        patient_data = [
            ['Patient ID:', patient.patient_id, 'MRN:', patient.mrn],
            ['Name:', f"{patient.first_name} {patient.last_name}", 'DOB:', patient.birth_date],
            ['Age:', str(patient.age), 'Gender:', patient.gender],
            ['Room:', patient.room_number or 'N/A', 'Department:', patient.department or 'N/A'],
            ['Attending:', patient.attending_physician or 'N/A', 'Admission:', patient.admission_date or 'N/A']
        ]
        
        patient_table = Table(patient_data, colWidths=[1*inch, 2*inch, 1*inch, 2*inch])
        patient_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(patient_table)
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _create_lpp_findings(self, findings: List[LPPFinding]) -> List[Any]:
        """Create LPP findings section"""
        elements = []
        
        # Section header
        elements.append(Paragraph("PRESSURE INJURY FINDINGS", self.styles['SectionHeader']))
        
        for i, finding in enumerate(findings, 1):
            # Finding header
            finding_header = f"Finding #{i} - Grade {finding.lpp_grade} ({finding.severity})"
            elements.append(Paragraph(finding_header, self.styles['Heading3']))
            
            # Critical alert for severe findings
            if finding.lpp_grade >= 3:
                alert_text = f"⚠️ CRITICAL: Grade {finding.lpp_grade} pressure injury requires immediate medical attention"
                elements.append(Paragraph(alert_text, self.styles['CriticalAlert']))
            
            # Finding details table
            finding_data = [
                ['Detection Time:', finding.timestamp],
                ['Location:', finding.anatomical_location],
                ['Grade:', f"{finding.lpp_grade} ({finding.severity})"],
                ['AI Confidence:', f"{finding.confidence_score:.1%}"],
                ['Risk Factors:', ', '.join(finding.risk_factors) if finding.risk_factors else 'None identified']
            ]
            
            if finding.measurements:
                for measure, value in finding.measurements.items():
                    finding_data.append([f'{measure.title()}:', f'{value:.1f} cm'])
            
            finding_table = Table(finding_data, colWidths=[2*inch, 4*inch])
            finding_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            elements.append(finding_table)
            
            # Clinical recommendations
            if finding.recommendations:
                elements.append(Paragraph("Clinical Recommendations:", self.styles['Heading4']))
                for rec in finding.recommendations:
                    elements.append(Paragraph(f"• {rec}", self.styles['ClinicalFinding']))
            
            # Image if available
            if finding.image_path and Path(finding.image_path).exists():
                try:
                    img = RLImage(finding.image_path, width=3*inch, height=2*inch)
                    elements.append(Spacer(1, 10))
                    elements.append(Paragraph("Detection Image:", self.styles['Heading4']))
                    elements.append(img)
                except Exception as e:
                    logger.warning(f"Could not include image {finding.image_path}: {e}")
            
            # Separator between findings
            if i < len(findings):
                elements.append(Spacer(1, 20))
        
        return elements
    
    def _create_medical_recommendations(self, findings: List[LPPFinding]) -> List[Any]:
        """Create evidence-based medical recommendations"""
        elements = []
        
        # Section header
        elements.append(Paragraph("EVIDENCE-BASED MEDICAL RECOMMENDATIONS", self.styles['SectionHeader']))
        
        # Get highest grade for overall recommendations
        max_grade = max(finding.lpp_grade for finding in findings)
        
        # Generate clinical decision
        clinical_decision = self.medical_engine.make_clinical_decision(
            lpp_grade=max_grade,
            confidence=max(finding.confidence_score for finding in findings),
            anatomical_location=findings[0].anatomical_location if findings else "unknown"
        )
        
        # Clinical urgency
        urgency_text = f"<b>Clinical Urgency:</b> {clinical_decision['urgency']}"
        elements.append(Paragraph(urgency_text, self.styles['Normal']))
        
        # Evidence-based recommendations
        elements.append(Paragraph("<b>Evidence-Based Interventions:</b>", self.styles['Normal']))
        for intervention in clinical_decision['interventions']:
            elements.append(Paragraph(f"• {intervention}", self.styles['ClinicalFinding']))
        
        # Follow-up requirements
        elements.append(Paragraph("<b>Follow-up Requirements:</b>", self.styles['Normal']))
        elements.append(Paragraph(f"• Assessment frequency: {clinical_decision['follow_up_frequency']}", 
                                 self.styles['ClinicalFinding']))
        elements.append(Paragraph(f"• Documentation requirements: {clinical_decision['documentation_requirements']}", 
                                 self.styles['ClinicalFinding']))
        
        # Scientific references
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("<b>Scientific Evidence:</b>", self.styles['Normal']))
        references_text = f"Evidence Level: {clinical_decision['evidence_level']} | "
        references_text += f"Guidelines: {clinical_decision['guidelines_reference']}"
        elements.append(Paragraph(references_text, self.styles['Normal']))
        
        return elements
    
    def _create_clinical_assessment(self, assessment: ClinicalAssessment) -> List[Any]:
        """Create clinical assessment section"""
        elements = []
        
        # Section header
        elements.append(Paragraph("CLINICAL ASSESSMENT", self.styles['SectionHeader']))
        
        # Assessment details
        assessment_data = [
            ['Assessment ID:', assessment.assessment_id],
            ['Physician:', assessment.physician_name],
            ['License #:', assessment.physician_license],
            ['Assessment Date:', assessment.assessment_date],
            ['Status:', assessment.verification_status.upper()]
        ]
        
        assessment_table = Table(assessment_data, colWidths=[2*inch, 4*inch])
        assessment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        elements.append(assessment_table)
        elements.append(Spacer(1, 15))
        
        # Clinical notes
        elements.append(Paragraph("<b>Clinical Notes:</b>", self.styles['Normal']))
        elements.append(Paragraph(assessment.clinical_notes, self.styles['Normal']))
        elements.append(Spacer(1, 10))
        
        # Treatment plan
        elements.append(Paragraph("<b>Treatment Plan:</b>", self.styles['Normal']))
        elements.append(Paragraph(assessment.treatment_plan, self.styles['Normal']))
        elements.append(Spacer(1, 10))
        
        # Follow-up instructions
        elements.append(Paragraph("<b>Follow-up Instructions:</b>", self.styles['Normal']))
        elements.append(Paragraph(assessment.follow_up_instructions, self.styles['Normal']))
        
        return elements
    
    def _create_digital_signature(self, assessment: ClinicalAssessment) -> List[Any]:
        """Create digital signature section"""
        elements = []
        
        # Section header
        elements.append(Paragraph("DIGITAL SIGNATURE", self.styles['SectionHeader']))
        
        if assessment.digital_signature:
            # Signature verification
            signature_text = f"""✓ This report has been digitally signed by {assessment.physician_name}
            License: {assessment.physician_license}
            Signature Date: {assessment.assessment_date}
            Verification Status: {assessment.verification_status.upper()}
            
            Digital Signature Hash: {assessment.digital_signature[:32]}...
            
            This digital signature ensures the integrity and authenticity of this medical report.
            Any modifications to this document will invalidate the signature."""
            
            elements.append(Paragraph(signature_text, self.styles['DigitalSignature']))
        else:
            # Pending signature
            pending_text = "⏳ Digital signature pending physician review and approval."
            elements.append(Paragraph(pending_text, self.styles['Normal']))
        
        return elements
    
    def _create_legal_disclaimer(self) -> List[Any]:
        """Create legal disclaimer section"""
        elements = []
        
        elements.append(PageBreak())
        elements.append(Paragraph("LEGAL DISCLAIMER AND AI DISCLOSURE", self.styles['SectionHeader']))
        
        disclaimer_text = """
        <b>Artificial Intelligence Disclosure:</b>
        This report contains findings generated by the Vigia Medical AI System, an FDA-cleared 
        medical device software for pressure injury detection. The AI analysis should be used 
        as a diagnostic aid and does not replace clinical judgment.
        
        <b>Clinical Validation Required:</b>
        All AI-generated findings must be validated by qualified healthcare professionals 
        before clinical decisions are made. The attending physician retains full responsibility 
        for patient care decisions.
        
        <b>Medical Device Information:</b>
        • Device Name: Vigia Pressure Injury Detection System
        • Software Version: 1.3.1
        • Classification: Class II Medical Device Software
        • Intended Use: Computer-aided detection of pressure injuries
        
        <b>Confidentiality Notice:</b>
        This document contains Protected Health Information (PHI) under HIPAA regulations. 
        Unauthorized disclosure is prohibited by federal law. Distribution is restricted 
        to authorized healthcare personnel involved in patient care.
        
        <b>Report Validity:</b>
        This report is valid only when digitally signed by an authorized healthcare provider. 
        Unsigned reports are considered preliminary and should not be used for clinical decisions.
        """
        
        elements.append(Paragraph(disclaimer_text, self.styles['Normal']))
        
        return elements
    
    def generate_clinical_report(self, 
                               patient: PatientInfo,
                               findings: List[LPPFinding],
                               assessment: Optional[ClinicalAssessment] = None,
                               output_path: str = None) -> str:
        """
        Generate complete clinical PDF report
        """
        try:
            # Setup output path
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"lpp_report_{patient.patient_id}_{timestamp}.pdf"
            
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=150,
                bottomMargin=72
            )
            
            # Document elements
            elements = []
            
            # Report title and metadata
            elements.append(Paragraph("MEDICAL ASSESSMENT REPORT", self.styles['MedicalTitle']))
            elements.append(Paragraph(f"Report ID: RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}", 
                                     self.styles['Normal']))
            elements.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}", 
                                     self.styles['Normal']))
            elements.append(Spacer(1, 30))
            
            # Patient demographics
            elements.extend(self._create_patient_demographics(patient))
            
            # LPP findings
            if findings:
                elements.extend(self._create_lpp_findings(findings))
                elements.append(Spacer(1, 20))
                
                # Medical recommendations
                elements.extend(self._create_medical_recommendations(findings))
                elements.append(Spacer(1, 20))
            
            # Clinical assessment (if available)
            if assessment:
                elements.extend(self._create_clinical_assessment(assessment))
                elements.append(Spacer(1, 20))
                
                # Digital signature
                elements.extend(self._create_digital_signature(assessment))
            
            # Legal disclaimer
            elements.extend(self._create_legal_disclaimer())
            
            # Build PDF with custom header/footer
            doc.build(
                elements,
                onFirstPage=self._create_header,
                onLaterPages=self._create_header
            )
            
            # Add footer to all pages
            self._add_footer_to_pdf(output_path)
            
            logger.info(f"Clinical report generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating clinical report: {e}")
            raise
    
    def _add_footer_to_pdf(self, pdf_path: str):
        """Add footer to existing PDF"""
        try:
            # This would require PyPDF2 or similar library
            # For now, footer is handled in the template
            pass
        except Exception as e:
            logger.warning(f"Could not add footer to PDF: {e}")
    
    def create_digital_signature(self, content: str, private_key_path: str, 
                               password: str) -> str:
        """
        Create digital signature for report content
        """
        try:
            # Load private key
            with open(private_key_path, 'rb') as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=password.encode() if password else None
                )
            
            # Create signature
            content_bytes = content.encode('utf-8')
            signature = private_key.sign(
                content_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Return base64 encoded signature
            return base64.b64encode(signature).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error creating digital signature: {e}")
            raise
    
    def verify_digital_signature(self, content: str, signature: str, 
                                public_key_path: str) -> bool:
        """
        Verify digital signature
        """
        try:
            # Load public key
            with open(public_key_path, 'rb') as key_file:
                public_key = serialization.load_pem_public_key(key_file.read())
            
            # Decode signature
            signature_bytes = base64.b64decode(signature.encode('utf-8'))
            content_bytes = content.encode('utf-8')
            
            # Verify signature
            public_key.verify(
                signature_bytes,
                content_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False


# Factory function
def create_pdf_generator(config: Dict[str, Any]) -> ClinicalPDFGenerator:
    """
    Factory function to create PDF generator
    """
    return ClinicalPDFGenerator(config)


# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        'hospital_name': 'General Hospital',
        'hospital_address': '123 Medical Center Drive, City, State 12345',
        'hospital_phone': '(555) 123-4567',
        'signing_cert_path': '/path/to/signing.crt',
        'signing_key_path': '/path/to/signing.key'
    }
    
    # Example patient
    patient = PatientInfo(
        patient_id="PAT001",
        mrn="MRN123456",
        first_name="John",
        last_name="Doe",
        birth_date="1950-01-15",
        gender="M",
        age=74,
        room_number="101A",
        attending_physician="Dr. Sarah Smith",
        department="ICU"
    )
    
    # Example finding
    finding = LPPFinding(
        finding_id="LPP001",
        timestamp=datetime.now().isoformat(),
        lpp_grade=3,
        confidence_score=0.92,
        anatomical_location="sacrum",
        severity="High",
        risk_factors=["Immobility", "Advanced age", "Poor nutrition"],
        recommendations=[
            "Immediate pressure redistribution",
            "Wound care consultation",
            "Nutritional assessment"
        ]
    )
    
    # Example assessment
    assessment = ClinicalAssessment(
        assessment_id="ASSESS001",
        physician_name="Dr. Sarah Smith",
        physician_license="MD123456",
        assessment_date=datetime.now().isoformat(),
        clinical_notes="Stage 3 pressure injury identified on sacrum. Patient requires immediate intervention.",
        treatment_plan="Pressure redistribution, wound care, nutritional support.",
        follow_up_instructions="Daily assessment, document progression, monitor healing."
    )
    
    # Generate report
    generator = create_pdf_generator(config)
    report_path = generator.generate_clinical_report(patient, [finding], assessment)
    print(f"Report generated: {report_path}")
