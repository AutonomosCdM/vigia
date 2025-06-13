"""
MedHELM Test Data Generator
==========================

Generates test data for MedHELM evaluation based on Vigía's synthetic patients.
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timedelta

class MedHELMTestDataGenerator:
    """Generate test data for MedHELM evaluation."""
    
    def __init__(self):
        # Anatomical locations
        self.locations = ["sacrum", "heel", "hip", "elbow", "shoulder", "ankle"]
        
        # Medical conditions
        self.conditions = [
            "pressure ulcer", "diabetic ulcer", "venous ulcer", 
            "arterial ulcer", "traumatic wound"
        ]
        
        # Patient contexts
        self.patient_contexts = [
            {"diabetes": True, "mobility": "limited"},
            {"diabetes": False, "mobility": "bedridden"},
            {"diabetes": True, "mobility": "wheelchair"},
            {"diabetes": False, "mobility": "ambulatory"}
        ]
        
        # Clinical notes templates
        self.note_templates = [
            "Patient presents with {condition} on {location}. Grade {grade} with {size}cm diameter.",
            "{age} year old patient with {condition} affecting {location}. Evidence of {tissue_type}.",
            "Chronic {condition} observed on {location}. Progression from grade {prev_grade} to {grade}."
        ]
        
    def generate_clinical_decision_data(self, n_samples: int = 50) -> List[Dict[str, Any]]:
        """Generate test data for clinical decision support tasks."""
        data = []
        
        for i in range(n_samples):
            grade = random.randint(0, 4)
            location = random.choice(self.locations)
            
            sample = {
                "id": f"cds_{i:04d}",
                "image_path": f"/synthetic/images/patient_{i:04d}_lpp.jpg",
                "true_grade": grade,
                "lpp_grade": grade,
                "confidence": random.uniform(0.7, 0.95),
                "location": location,
                "anatomical_region": self._get_region(location),
                "patient_context": random.choice(self.patient_contexts),
                "timestamp": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "expected_urgency": self._get_urgency(grade),
                "expected_treatment": self._get_treatment(grade, location)
            }
            
            data.append(sample)
            
        return data
    
    def generate_note_generation_data(self, n_samples: int = 30) -> List[Dict[str, Any]]:
        """Generate test data for clinical note generation tasks."""
        data = []
        
        for i in range(n_samples):
            grade = random.randint(0, 4)
            location = random.choice(self.locations)
            age = random.randint(45, 85)
            
            condition = f"Grade {grade} pressure ulcer"
            template = random.choice(self.note_templates)
            
            reference_note = template.format(
                condition=condition,
                location=location,
                grade=grade,
                age=age,
                size=random.uniform(1, 10),
                tissue_type=self._get_tissue_type(grade),
                prev_grade=max(0, grade-1)
            )
            
            sample = {
                "id": f"note_{i:04d}",
                "patient_id": f"P{i:04d}",
                "condition": condition,
                "location": location,
                "grade": grade,
                "clinical_context": {
                    "age": age,
                    "comorbidities": self._get_comorbidities(age),
                    "medications": self._get_medications()
                },
                "reference_note": reference_note,
                "note_type": random.choice(["progress", "admission", "discharge"]),
                "expected_sections": ["chief_complaint", "assessment", "plan"]
            }
            
            data.append(sample)
            
        return data
    
    def generate_communication_data(self, n_samples: int = 40) -> List[Dict[str, Any]]:
        """Generate test data for patient communication tasks."""
        data = []
        
        medical_terms = [
            ("pressure ulcer", "bed sore"),
            ("sacrum", "lower back"),
            ("necrotic tissue", "dead skin"),
            ("debridement", "cleaning the wound"),
            ("granulation", "healing tissue"),
            ("exudate", "wound drainage")
        ]
        
        for i in range(n_samples):
            term, simple = random.choice(medical_terms)
            grade = random.randint(1, 3)
            
            medical_text = f"You have a grade {grade} {term} that requires {self._get_treatment(grade, 'sacrum')}"
            simplified_text = f"You have a stage {grade} {simple} that needs {self._get_simple_treatment(grade)}"
            
            sample = {
                "id": f"comm_{i:04d}",
                "medical_text": medical_text,
                "simplified_text": simplified_text,
                "target_reading_level": random.randint(6, 8),  # Grade level
                "patient_language": random.choice(["es", "en"]),
                "health_literacy": random.choice(["low", "medium", "high"]),
                "communication_type": random.choice(["diagnosis", "treatment", "followup"])
            }
            
            data.append(sample)
            
        return data
    
    def generate_admin_workflow_data(self, n_samples: int = 60) -> List[Dict[str, Any]]:
        """Generate test data for administration and workflow tasks."""
        data = []
        
        for i in range(n_samples):
            grade = random.randint(0, 4)
            
            # Triage data
            urgency_map = {0: "low", 1: "medium", 2: "high", 3: "high", 4: "critical"}
            true_urgency = urgency_map[grade]
            
            sample = {
                "id": f"admin_{i:04d}",
                "patient_id": f"P{i:04d}",
                "presentation": {
                    "chief_complaint": f"wound on {random.choice(self.locations)}",
                    "pain_scale": random.randint(1, 10),
                    "duration_days": random.randint(1, 30),
                    "fever": random.choice([True, False]),
                    "signs_infection": grade >= 3
                },
                "vitals": {
                    "temperature": random.uniform(36.0, 39.0),
                    "blood_pressure": f"{random.randint(110, 150)}/{random.randint(70, 90)}",
                    "heart_rate": random.randint(60, 100)
                },
                "true_urgency": true_urgency,
                "expected_disposition": self._get_disposition(true_urgency),
                "workflow_type": "triage"
            }
            
            data.append(sample)
            
        return data
    
    def generate_research_data(self, n_samples: int = 20) -> List[Dict[str, Any]]:
        """Generate test data for medical research tasks."""
        data = []
        
        research_queries = [
            "latest treatments for stage 3 pressure ulcers",
            "prevention protocols for heel pressure injuries",
            "evidence for negative pressure wound therapy",
            "nutritional interventions for wound healing",
            "risk assessment tools for pressure injury"
        ]
        
        for i in range(n_samples):
            query = random.choice(research_queries)
            
            sample = {
                "id": f"research_{i:04d}",
                "query": query,
                "research_type": random.choice(["literature_review", "protocol_development"]),
                "evidence_level_required": random.choice(["A", "B", "C"]),
                "guidelines": ["NPUAP", "EPUAP", "PPPIA"],
                "expected_sources": random.randint(5, 20),
                "output_format": random.choice(["summary", "systematic_review", "protocol"])
            }
            
            data.append(sample)
            
        return data
    
    def generate_complete_dataset(self, output_path: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """Generate complete MedHELM test dataset."""
        dataset = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator_version": "1.0.0",
                "vigia_version": "1.3.1",
                "total_samples": 0
            },
            "clinical_decision_support": {
                "cds_diagnosis_1": self.generate_clinical_decision_data(50),
                "cds_treatment_1": self.generate_clinical_decision_data(40),
                "cds_risk_1": self.generate_clinical_decision_data(30)
            },
            "clinical_note_generation": {
                "note_summary_1": self.generate_note_generation_data(30),
                "note_report_1": self.generate_note_generation_data(20)
            },
            "patient_communication": {
                "comm_explain_1": self.generate_communication_data(40),
                "comm_instruct_1": self.generate_communication_data(30)
            },
            "admin_workflow": {
                "admin_triage_1": self.generate_admin_workflow_data(60),
                "admin_schedule_1": []  # Not applicable
            },
            "medical_research": {
                "research_literature_1": self.generate_research_data(20),
                "research_protocol_1": self.generate_research_data(15)
            }
        }
        
        # Count total samples
        total = 0
        for category in dataset.values():
            if isinstance(category, dict):
                for task_data in category.values():
                    if isinstance(task_data, list):
                        total += len(task_data)
        
        dataset["metadata"]["total_samples"] = total
        
        # Save if path provided
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(dataset, f, indent=2)
                
            print(f"Test dataset saved to: {output_path}")
            print(f"Total samples generated: {total}")
        
        return dataset
    
    # Helper methods
    def _get_region(self, location: str) -> str:
        """Get anatomical region from location."""
        region_map = {
            "sacrum": "trunk", "heel": "lower_extremity",
            "hip": "trunk", "elbow": "upper_extremity",
            "shoulder": "upper_extremity", "ankle": "lower_extremity"
        }
        return region_map.get(location, "other")
    
    def _get_urgency(self, grade: int) -> str:
        """Get urgency level from grade."""
        if grade == 0:
            return "low"
        elif grade == 1:
            return "medium"
        elif grade in [2, 3]:
            return "high"
        else:
            return "critical"
    
    def _get_treatment(self, grade: int, location: str) -> str:
        """Get treatment recommendation."""
        treatments = {
            0: "preventive measures and monitoring",
            1: "pressure relief and skin protection",
            2: "wound dressing and pressure redistribution",
            3: "advanced wound care and possible debridement",
            4: "urgent surgical consultation and intensive wound management"
        }
        return treatments.get(grade, "standard wound care")
    
    def _get_simple_treatment(self, grade: int) -> str:
        """Get simplified treatment description."""
        simple_treatments = {
            1: "special cushions and skin care",
            2: "bandages and pressure relief",
            3: "special wound care from a nurse",
            4: "immediate medical attention"
        }
        return simple_treatments.get(grade, "wound care")
    
    def _get_tissue_type(self, grade: int) -> str:
        """Get tissue type description."""
        tissue_types = {
            0: "intact skin with erythema",
            1: "partial thickness skin loss",
            2: "full thickness skin loss",
            3: "tissue loss with exposed bone/muscle",
            4: "extensive tissue necrosis"
        }
        return tissue_types.get(grade, "damaged tissue")
    
    def _get_comorbidities(self, age: int) -> List[str]:
        """Get age-appropriate comorbidities."""
        base_conditions = ["hypertension", "diabetes", "arthritis"]
        
        if age > 65:
            base_conditions.extend(["dementia", "osteoporosis"])
        if age > 75:
            base_conditions.extend(["heart_failure", "COPD"])
            
        # Return random subset
        n_conditions = random.randint(1, min(3, len(base_conditions)))
        return random.sample(base_conditions, n_conditions)
    
    def _get_medications(self) -> List[str]:
        """Get common medications."""
        meds = [
            "metformin", "lisinopril", "aspirin", "atorvastatin",
            "warfarin", "insulin", "furosemide", "metoprolol"
        ]
        n_meds = random.randint(2, 5)
        return random.sample(meds, n_meds)
    
    def _get_disposition(self, urgency: str) -> str:
        """Get expected disposition based on urgency."""
        disposition_map = {
            "low": "outpatient_followup",
            "medium": "urgent_care_referral",
            "high": "emergency_evaluation",
            "critical": "immediate_admission"
        }
        return disposition_map.get(urgency, "clinical_evaluation")