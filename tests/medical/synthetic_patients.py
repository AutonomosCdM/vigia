"""
Synthetic Patient Data Generator for Medical Testing
===================================================

Generates 100+ synthetic patient profiles for comprehensive LPP testing.
All data is synthetic and compliant with HIPAA regulations.

References:
- NPUAP/EPUAP/PPPIA Clinical Guidelines
- Braden Scale Risk Assessment
- International LPP Classification System
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import random
from datetime import datetime, timedelta
import uuid


class LPPGradeSynthetic(Enum):
    """LPP Grades based on NPUAP/EPUAP/PPPIA Guidelines"""
    NO_LESION = 0
    GRADE_1 = 1  # Non-blanchable erythema
    GRADE_2 = 2  # Partial thickness skin loss
    GRADE_3 = 3  # Full thickness skin loss
    GRADE_4 = 4  # Full thickness tissue loss
    UNSTAGEABLE = 5  # Depth unknown
    SUSPECTED_DTI = 6  # Deep tissue injury


class RiskLevel(Enum):
    """Risk levels based on Braden Scale and clinical factors"""
    LOW = "low"           # Braden 19-23, minimal risk factors
    MODERATE = "moderate" # Braden 15-18, some risk factors
    HIGH = "high"         # Braden 13-14, multiple risk factors
    CRITICAL = "critical" # Braden ≤12, severe risk factors


class MobilityLevel(Enum):
    """Mobility assessment levels"""
    FULLY_MOBILE = "fully_mobile"
    SLIGHTLY_LIMITED = "slightly_limited"
    VERY_LIMITED = "very_limited"
    COMPLETELY_IMMOBILE = "completely_immobile"


class AnatomicalLocation(Enum):
    """Common LPP anatomical locations"""
    SACRUM = "sacrum"
    COCCYX = "coccyx"
    HEEL = "heel"
    ANKLE = "ankle"
    ELBOW = "elbow"
    SHOULDER = "shoulder"
    OCCIPUT = "occiput"
    TROCHANTER = "trochanter"
    ISCHIAL_TUBEROSITY = "ischial_tuberosity"


@dataclass
class SyntheticPatient:
    """Synthetic patient with comprehensive medical profile"""
    
    # Identifiers
    patient_id: str
    patient_code: str
    hospital_id: str
    
    # Demographics (synthetic)
    age: int
    sex: str
    ethnicity: str
    
    # Physical characteristics
    weight_kg: float
    height_cm: float
    bmi: float
    
    # Mobility and risk factors
    mobility_level: MobilityLevel
    braden_score: int
    risk_level: RiskLevel
    
    # Medical conditions
    diabetes: bool
    hypertension: bool
    malnutrition: bool
    incontinence: bool
    compromised_circulation: bool
    immunosuppression: bool
    
    # Medications affecting healing
    anticoagulants: bool
    corticosteroids: bool
    chemotherapy: bool
    
    # Current LPP status
    has_lpp: bool
    lpp_grade: Optional[LPPGradeSynthetic]
    lpp_location: Optional[AnatomicalLocation]
    lpp_duration_days: Optional[int]
    previous_lpp_history: bool
    
    # Laboratory values
    hemoglobin_g_dl: float
    albumin_g_dl: float
    total_protein_g_dl: float
    
    # Clinical context
    admission_date: datetime
    hospital_unit: str
    primary_diagnosis: str
    length_of_stay_days: int
    
    # Expected outcomes (for testing)
    expected_urgency: str
    expected_intervention: str
    expected_notification_priority: str


class SyntheticPatientGenerator:
    """Generates comprehensive synthetic patient datasets"""
    
    def __init__(self, seed: int = 42):
        """Initialize generator with random seed for reproducibility"""
        random.seed(seed)
        self.patient_counter = 0
        
        # Hospital IDs for multi-tenant testing
        self.hospital_ids = [
            "CLC-001", "HDIGITAL-002", "HMETRO-003",
            "HSALV-004", "HUCCHILE-005", "HDIPRECA-006"
        ]
        
        # Hospital units
        self.hospital_units = [
            "UCI", "UTI", "Medicina Interna", "Geriatría",
            "Traumatología", "Neurología", "Cardiología",
            "Oncología", "Cuidados Paliativos"
        ]
        
        # Primary diagnoses
        self.primary_diagnoses = [
            "Fractura de cadera", "ACV isquémico", "Insuficiencia cardíaca",
            "Diabetes descompensada", "Neumonía", "Sepsis",
            "Cáncer metastásico", "Demencia avanzada", "Lesión medular",
            "Insuficiencia renal crónica"
        ]
    
    def generate_patient_code(self, hospital_id: str) -> str:
        """Generate realistic patient code"""
        self.patient_counter += 1
        hospital_prefix = hospital_id.split("-")[0][:2]
        year = datetime.now().year
        return f"{hospital_prefix}-{year}-{self.patient_counter:03d}"
    
    def calculate_braden_score(self, mobility: MobilityLevel, age: int, 
                              conditions: Dict[str, bool]) -> int:
        """Calculate realistic Braden score based on patient factors"""
        base_score = 20  # Start with good score
        
        # Mobility impact
        mobility_impact = {
            MobilityLevel.FULLY_MOBILE: 0,
            MobilityLevel.SLIGHTLY_LIMITED: -2,
            MobilityLevel.VERY_LIMITED: -4,
            MobilityLevel.COMPLETELY_IMMOBILE: -6
        }
        base_score += mobility_impact[mobility]
        
        # Age impact
        if age > 80:
            base_score -= 3
        elif age > 65:
            base_score -= 1
        
        # Condition impacts
        if conditions.get('diabetes'): base_score -= 2
        if conditions.get('malnutrition'): base_score -= 2
        if conditions.get('incontinence'): base_score -= 1
        if conditions.get('compromised_circulation'): base_score -= 2
        if conditions.get('immunosuppression'): base_score -= 1
        
        return max(6, min(23, base_score))  # Braden scale range
    
    def determine_risk_level(self, braden_score: int) -> RiskLevel:
        """Determine risk level based on Braden score"""
        if braden_score >= 19:
            return RiskLevel.LOW
        elif braden_score >= 15:
            return RiskLevel.MODERATE
        elif braden_score >= 13:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    def generate_lpp_status(self, risk_level: RiskLevel, age: int) -> Dict[str, Any]:
        """Generate realistic LPP status based on risk factors"""
        # Probability of having LPP based on risk level
        lpp_probabilities = {
            RiskLevel.LOW: 0.05,
            RiskLevel.MODERATE: 0.15,
            RiskLevel.HIGH: 0.35,
            RiskLevel.CRITICAL: 0.65
        }
        
        has_lpp = random.random() < lpp_probabilities[risk_level]
        
        if not has_lpp:
            return {
                'has_lpp': False,
                'lpp_grade': None,
                'lpp_location': None,
                'lpp_duration_days': None
            }
        
        # Grade distribution based on risk level
        grade_distributions = {
            RiskLevel.LOW: [0.6, 0.3, 0.1, 0.0, 0.0, 0.0],  # Mostly Grade 1-2
            RiskLevel.MODERATE: [0.4, 0.4, 0.15, 0.05, 0.0, 0.0],
            RiskLevel.HIGH: [0.2, 0.3, 0.3, 0.15, 0.05, 0.0],
            RiskLevel.CRITICAL: [0.1, 0.2, 0.3, 0.25, 0.1, 0.05]
        }
        
        grades = [LPPGradeSynthetic.GRADE_1, LPPGradeSynthetic.GRADE_2, 
                 LPPGradeSynthetic.GRADE_3, LPPGradeSynthetic.GRADE_4,
                 LPPGradeSynthetic.UNSTAGEABLE, LPPGradeSynthetic.SUSPECTED_DTI]
        
        grade = random.choices(grades, weights=grade_distributions[risk_level])[0]
        
        # Location probabilities (sacrum most common)
        location_weights = [0.35, 0.15, 0.15, 0.1, 0.08, 0.05, 0.04, 0.04, 0.04]
        location = random.choices(list(AnatomicalLocation), weights=location_weights)[0]
        
        # Duration based on grade (higher grades typically older)
        duration_ranges = {
            LPPGradeSynthetic.GRADE_1: (1, 7),
            LPPGradeSynthetic.GRADE_2: (3, 14),
            LPPGradeSynthetic.GRADE_3: (7, 30),
            LPPGradeSynthetic.GRADE_4: (14, 60),
            LPPGradeSynthetic.UNSTAGEABLE: (7, 45),
            LPPGradeSynthetic.SUSPECTED_DTI: (1, 5)
        }
        
        duration = random.randint(*duration_ranges[grade])
        
        return {
            'has_lpp': True,
            'lpp_grade': grade,
            'lpp_location': location,
            'lpp_duration_days': duration
        }
    
    def generate_lab_values(self, malnutrition: bool, age: int) -> Dict[str, float]:
        """Generate realistic laboratory values"""
        if malnutrition:
            # Malnourished patients have lower values
            hemoglobin = random.uniform(8.5, 11.0)
            albumin = random.uniform(2.0, 3.0)
            total_protein = random.uniform(5.0, 6.5)
        elif age > 75:
            # Elderly patients tend to have lower values
            hemoglobin = random.uniform(10.0, 13.0)
            albumin = random.uniform(3.0, 4.0)
            total_protein = random.uniform(6.0, 7.5)
        else:
            # Normal values
            hemoglobin = random.uniform(12.0, 16.0)
            albumin = random.uniform(3.5, 5.0)
            total_protein = random.uniform(6.5, 8.5)
        
        return {
            'hemoglobin_g_dl': round(hemoglobin, 1),
            'albumin_g_dl': round(albumin, 1),
            'total_protein_g_dl': round(total_protein, 1)
        }
    
    def determine_expected_outcomes(self, patient_data: Dict[str, Any]) -> Dict[str, str]:
        """Determine expected system responses for testing"""
        risk_level = patient_data['risk_level']
        has_lpp = patient_data['has_lpp']
        lpp_grade = patient_data.get('lpp_grade')
        
        # Expected urgency
        if has_lpp and lpp_grade in [LPPGradeSynthetic.GRADE_4, LPPGradeSynthetic.SUSPECTED_DTI]:
            urgency = "EMERGENCY"
            priority = "high"
        elif has_lpp and lpp_grade == LPPGradeSynthetic.GRADE_3:
            urgency = "URGENT"
            priority = "high"
        elif has_lpp and lpp_grade in [LPPGradeSynthetic.GRADE_2, LPPGradeSynthetic.UNSTAGEABLE]:
            urgency = "IMPORTANTE"
            priority = "medium"
        elif has_lpp and lpp_grade == LPPGradeSynthetic.GRADE_1:
            urgency = "ATENCIÓN"
            priority = "medium"
        elif risk_level == RiskLevel.CRITICAL:
            urgency = "PREVENTIVO_CRÍTICO"
            priority = "medium"
        else:
            urgency = "RUTINA"
            priority = "low"
        
        # Expected intervention
        if has_lpp:
            interventions = {
                LPPGradeSynthetic.GRADE_1: "Alivio de presión + protección cutánea",
                LPPGradeSynthetic.GRADE_2: "Curación húmeda + apósitos hidrocoloides",
                LPPGradeSynthetic.GRADE_3: "Desbridamiento + apósitos avanzados",
                LPPGradeSynthetic.GRADE_4: "Evaluación quirúrgica + manejo de dolor",
                LPPGradeSynthetic.UNSTAGEABLE: "Evaluación especializada + desbridamiento",
                LPPGradeSynthetic.SUSPECTED_DTI: "Monitoreo estricto + protección"
            }
            intervention = interventions[lpp_grade]
        else:
            intervention = "Prevención según protocolo + valoración Braden"
        
        return {
            'expected_urgency': urgency,
            'expected_intervention': intervention,
            'expected_notification_priority': priority
        }
    
    def generate_single_patient(self, profile_type: str = "random") -> SyntheticPatient:
        """Generate a single synthetic patient"""
        
        hospital_id = random.choice(self.hospital_ids)
        patient_code = self.generate_patient_code(hospital_id)
        
        # Demographics
        age = self._generate_age_by_profile(profile_type)
        sex = random.choice(["M", "F"])
        ethnicity = random.choice(["Hispanic", "Non-Hispanic White", "Black", "Asian", "Other"])
        
        # Physical characteristics
        if sex == "M":
            weight_kg = random.uniform(60, 120)
            height_cm = random.uniform(160, 190)
        else:
            weight_kg = random.uniform(45, 100)
            height_cm = random.uniform(150, 175)
        
        bmi = weight_kg / ((height_cm / 100) ** 2)
        
        # Medical conditions (age-correlated)
        conditions = self._generate_conditions_by_age(age)
        
        # Mobility based on age and conditions
        mobility = self._generate_mobility(age, conditions)
        
        # Calculate Braden score and risk
        braden_score = self.calculate_braden_score(mobility, age, conditions)
        risk_level = self.determine_risk_level(braden_score)
        
        # LPP status
        lpp_data = self.generate_lpp_status(risk_level, age)
        
        # Lab values
        lab_values = self.generate_lab_values(conditions['malnutrition'], age)
        
        # Clinical context
        admission_date = datetime.now() - timedelta(days=random.randint(1, 30))
        length_of_stay = (datetime.now() - admission_date).days
        
        # Combine all data
        patient_data = {
            'patient_id': str(uuid.uuid4()),
            'patient_code': patient_code,
            'hospital_id': hospital_id,
            'age': age,
            'sex': sex,
            'ethnicity': ethnicity,
            'weight_kg': round(weight_kg, 1),
            'height_cm': round(height_cm, 1),
            'bmi': round(bmi, 1),
            'mobility_level': mobility,
            'braden_score': braden_score,
            'risk_level': risk_level,
            'hospital_unit': random.choice(self.hospital_units),
            'primary_diagnosis': random.choice(self.primary_diagnoses),
            'admission_date': admission_date,
            'length_of_stay_days': length_of_stay,
            'previous_lpp_history': random.random() < 0.3,
            **conditions,
            **lpp_data,
            **lab_values
        }
        
        # Expected outcomes for testing
        expected_outcomes = self.determine_expected_outcomes(patient_data)
        patient_data.update(expected_outcomes)
        
        return SyntheticPatient(**patient_data)
    
    def _generate_age_by_profile(self, profile_type: str) -> int:
        """Generate age based on profile type"""
        age_ranges = {
            "pediatric": (0, 17),
            "adult": (18, 64),
            "elderly": (65, 89),
            "very_elderly": (90, 105),
            "random": (18, 95)
        }
        return random.randint(*age_ranges.get(profile_type, age_ranges["random"]))
    
    def _generate_conditions_by_age(self, age: int) -> Dict[str, bool]:
        """Generate medical conditions based on age"""
        base_probabilities = {
            'diabetes': 0.1,
            'hypertension': 0.2,
            'malnutrition': 0.15,
            'incontinence': 0.1,
            'compromised_circulation': 0.08,
            'immunosuppression': 0.05,
            'anticoagulants': 0.2,
            'corticosteroids': 0.1,
            'chemotherapy': 0.03
        }
        
        # Age adjustments
        if age > 75:
            multiplier = 2.5
        elif age > 65:
            multiplier = 1.8
        elif age > 50:
            multiplier = 1.3
        else:
            multiplier = 0.7
        
        conditions = {}
        for condition, prob in base_probabilities.items():
            adjusted_prob = min(0.8, prob * multiplier)
            conditions[condition] = random.random() < adjusted_prob
        
        return conditions
    
    def _generate_mobility(self, age: int, conditions: Dict[str, bool]) -> MobilityLevel:
        """Generate mobility level based on age and conditions"""
        mobility_score = 100  # Start fully mobile
        
        # Age impact
        if age > 85: mobility_score -= 40
        elif age > 75: mobility_score -= 25
        elif age > 65: mobility_score -= 10
        
        # Condition impacts
        if conditions.get('diabetes'): mobility_score -= 15
        if conditions.get('compromised_circulation'): mobility_score -= 20
        if conditions.get('malnutrition'): mobility_score -= 10
        
        if mobility_score >= 80:
            return MobilityLevel.FULLY_MOBILE
        elif mobility_score >= 60:
            return MobilityLevel.SLIGHTLY_LIMITED
        elif mobility_score >= 30:
            return MobilityLevel.VERY_LIMITED
        else:
            return MobilityLevel.COMPLETELY_IMMOBILE
    
    def generate_patient_cohort(self, total_patients: int = 120) -> List[SyntheticPatient]:
        """Generate a comprehensive cohort of synthetic patients"""
        
        # Distribution strategy for comprehensive testing
        distributions = {
            "low_risk_no_lpp": 30,      # Baseline cases
            "moderate_risk_grade1": 25,  # Early intervention
            "high_risk_grade2": 20,      # Standard treatment
            "critical_grade3": 15,       # Advanced care
            "emergency_grade4": 10,      # Critical cases
            "edge_cases": 20             # Special scenarios
        }
        
        cohort = []
        
        # Generate patients by category
        for category, count in distributions.items():
            for _ in range(count):
                if category == "low_risk_no_lpp":
                    patient = self._generate_low_risk_patient()
                elif category == "moderate_risk_grade1":
                    patient = self._generate_moderate_risk_patient()
                elif category == "high_risk_grade2":
                    patient = self._generate_high_risk_patient()
                elif category == "critical_grade3":
                    patient = self._generate_critical_patient()
                elif category == "emergency_grade4":
                    patient = self._generate_emergency_patient()
                elif category == "edge_cases":
                    patient = self._generate_edge_case_patient()
                
                cohort.append(patient)
        
        return cohort
    
    def _generate_low_risk_patient(self) -> SyntheticPatient:
        """Generate low-risk patient without LPP"""
        # Force specific characteristics for this profile
        patient = self.generate_single_patient("adult")
        
        # Override to ensure low risk
        patient.age = random.randint(25, 55)
        patient.mobility_level = random.choice([MobilityLevel.FULLY_MOBILE, MobilityLevel.SLIGHTLY_LIMITED])
        patient.diabetes = random.random() < 0.1
        patient.malnutrition = False
        patient.has_lpp = False
        patient.lpp_grade = None
        patient.braden_score = random.randint(18, 23)
        patient.risk_level = RiskLevel.LOW
        
        return patient
    
    def _generate_moderate_risk_patient(self) -> SyntheticPatient:
        """Generate moderate-risk patient with Grade 1 LPP"""
        patient = self.generate_single_patient("elderly")
        
        # Override for moderate risk with Grade 1
        patient.age = random.randint(65, 80)
        patient.mobility_level = random.choice([MobilityLevel.SLIGHTLY_LIMITED, MobilityLevel.VERY_LIMITED])
        patient.has_lpp = True
        patient.lpp_grade = LPPGradeSynthetic.GRADE_1
        patient.lpp_location = random.choice([AnatomicalLocation.SACRUM, AnatomicalLocation.HEEL])
        patient.braden_score = random.randint(15, 18)
        patient.risk_level = RiskLevel.MODERATE
        
        return patient
    
    def _generate_high_risk_patient(self) -> SyntheticPatient:
        """Generate high-risk patient with Grade 2 LPP"""
        patient = self.generate_single_patient("elderly")
        
        # Override for high risk with Grade 2
        patient.age = random.randint(70, 85)
        patient.mobility_level = random.choice([MobilityLevel.VERY_LIMITED, MobilityLevel.COMPLETELY_IMMOBILE])
        patient.diabetes = True
        patient.has_lpp = True
        patient.lpp_grade = LPPGradeSynthetic.GRADE_2
        patient.lpp_location = AnatomicalLocation.SACRUM
        patient.braden_score = random.randint(13, 14)
        patient.risk_level = RiskLevel.HIGH
        
        return patient
    
    def _generate_critical_patient(self) -> SyntheticPatient:
        """Generate critical-risk patient with Grade 3 LPP"""
        patient = self.generate_single_patient("very_elderly")
        
        # Override for critical risk with Grade 3
        patient.age = random.randint(80, 95)
        patient.mobility_level = MobilityLevel.COMPLETELY_IMMOBILE
        patient.diabetes = True
        patient.malnutrition = True
        patient.has_lpp = True
        patient.lpp_grade = LPPGradeSynthetic.GRADE_3
        patient.lpp_location = AnatomicalLocation.SACRUM
        patient.braden_score = random.randint(8, 12)
        patient.risk_level = RiskLevel.CRITICAL
        
        return patient
    
    def _generate_emergency_patient(self) -> SyntheticPatient:
        """Generate emergency patient with Grade 4 LPP"""
        patient = self.generate_single_patient("very_elderly")
        
        # Override for emergency with Grade 4
        patient.age = random.randint(75, 100)
        patient.mobility_level = MobilityLevel.COMPLETELY_IMMOBILE
        patient.diabetes = True
        patient.malnutrition = True
        patient.compromised_circulation = True
        patient.has_lpp = True
        patient.lpp_grade = LPPGradeSynthetic.GRADE_4
        patient.lpp_location = AnatomicalLocation.SACRUM
        patient.braden_score = random.randint(6, 10)
        patient.risk_level = RiskLevel.CRITICAL
        
        return patient
    
    def _generate_edge_case_patient(self) -> SyntheticPatient:
        """Generate edge case patients for boundary testing"""
        edge_types = [
            "young_diabetic",
            "obese_immobile", 
            "multiple_lpp",
            "unstageable_lpp",
            "suspected_dti",
            "very_old_mobile"
        ]
        
        edge_type = random.choice(edge_types)
        patient = self.generate_single_patient()
        
        if edge_type == "young_diabetic":
            patient.age = random.randint(18, 35)
            patient.diabetes = True
            patient.has_lpp = True
            patient.lpp_grade = LPPGradeSynthetic.GRADE_2
        
        elif edge_type == "obese_immobile":
            patient.bmi = random.uniform(35, 50)
            patient.mobility_level = MobilityLevel.COMPLETELY_IMMOBILE
            patient.has_lpp = True
            patient.lpp_grade = LPPGradeSynthetic.GRADE_3
        
        elif edge_type == "unstageable_lpp":
            patient.has_lpp = True
            patient.lpp_grade = LPPGradeSynthetic.UNSTAGEABLE
            patient.lpp_location = AnatomicalLocation.SACRUM
        
        elif edge_type == "suspected_dti":
            patient.has_lpp = True
            patient.lpp_grade = LPPGradeSynthetic.SUSPECTED_DTI
            patient.lpp_location = AnatomicalLocation.HEEL
        
        elif edge_type == "very_old_mobile":
            patient.age = random.randint(95, 105)
            patient.mobility_level = MobilityLevel.SLIGHTLY_LIMITED
            patient.has_lpp = False
        
        return patient


# Singleton instance for consistent testing
_generator = SyntheticPatientGenerator()

def get_synthetic_patient_generator() -> SyntheticPatientGenerator:
    """Get singleton synthetic patient generator"""
    return _generator

def generate_test_cohort(size: int = 120) -> List[SyntheticPatient]:
    """Generate a test cohort of synthetic patients"""
    return _generator.generate_patient_cohort(size)

def get_patient_by_profile(profile: str) -> SyntheticPatient:
    """Get a specific patient profile for targeted testing"""
    if profile == "low_risk":
        return _generator._generate_low_risk_patient()
    elif profile == "moderate_risk":
        return _generator._generate_moderate_risk_patient()
    elif profile == "high_risk":
        return _generator._generate_high_risk_patient()
    elif profile == "critical":
        return _generator._generate_critical_patient()
    elif profile == "emergency":
        return _generator._generate_emergency_patient()
    elif profile == "edge_case":
        return _generator._generate_edge_case_patient()
    else:
        return _generator.generate_single_patient()