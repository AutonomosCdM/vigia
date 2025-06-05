"""
Triage Engine - Capa 2: Motor de Reglas Médicas
Motor de decisión médica con reglas clínicas validadas.

Responsabilidades:
- Aplicar reglas médicas validadas
- Detectar casos de emergencia
- Clasificar severidad clínica
- Identificar necesidad de escalamiento humano
- Mantener explicabilidad de decisiones
"""

import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .input_packager import StandardizedInput
from ..utils.secure_logger import SecureLogger

logger = SecureLogger("triage_engine")


class ClinicalUrgency(Enum):
    """Niveles de urgencia clínica."""
    EMERGENCY = "emergency"      # Respuesta inmediata
    URGENT = "urgent"           # < 30 minutos
    PRIORITY = "priority"       # < 2 horas
    ROUTINE = "routine"         # < 24 horas
    SCHEDULED = "scheduled"     # Programado


class ClinicalContext(Enum):
    """Contexto clínico del input."""
    PRESSURE_INJURY = "pressure_injury"
    WOUND_ASSESSMENT = "wound_assessment"
    MEDICATION_QUERY = "medication_query"
    PROTOCOL_REQUEST = "protocol_request"
    GENERAL_MEDICAL = "general_medical"
    NON_MEDICAL = "non_medical"
    UNKNOWN = "unknown"


@dataclass
class TriageRule:
    """Regla de triage médico."""
    rule_id: str
    name: str
    description: str
    condition: str  # Expresión evaluable
    priority: int   # 1-10, mayor = más prioritario
    context: ClinicalContext
    urgency: ClinicalUrgency
    actions: List[str]
    flags: List[str]


@dataclass
class TriageResult:
    """Resultado del proceso de triage."""
    urgency: ClinicalUrgency
    context: ClinicalContext
    confidence: float
    matched_rules: List[str]
    recommended_route: str
    clinical_flags: List[str]
    explanation: str
    requires_human_review: bool
    timestamp: datetime


class MedicalTriageEngine:
    """
    Motor de triage médico con reglas clínicas.
    """
    
    def __init__(self):
        """Inicializar motor de triage."""
        self.rules = self._initialize_medical_rules()
        self.emergency_patterns = self._compile_emergency_patterns()
        self.clinical_patterns = self._compile_clinical_patterns()
        
        logger.audit("triage_engine_initialized", {
            "component": "layer2_triage_engine",
            "total_rules": len(self.rules),
            "emergency_patterns": len(self.emergency_patterns),
            "clinical_compliance": True
        })
    
    def _initialize_medical_rules(self) -> List[TriageRule]:
        """Inicializar reglas médicas validadas."""
        return [
            # Reglas de emergencia
            TriageRule(
                rule_id="EMR001",
                name="Emergency Keywords Detection",
                description="Detect emergency medical situations",
                condition="emergency_keywords",
                priority=10,
                context=ClinicalContext.UNKNOWN,
                urgency=ClinicalUrgency.EMERGENCY,
                actions=["immediate_escalation", "notify_medical_team"],
                flags=["emergency", "critical", "human_required"]
            ),
            
            TriageRule(
                rule_id="EMR002",
                name="Severe Pain Indicator",
                description="Detect severe pain mentions",
                condition="severe_pain",
                priority=9,
                context=ClinicalContext.GENERAL_MEDICAL,
                urgency=ClinicalUrgency.URGENT,
                actions=["urgent_triage", "pain_assessment"],
                flags=["pain_management", "urgent"]
            ),
            
            # Reglas de lesiones por presión
            TriageRule(
                rule_id="LPP001",
                name="Pressure Injury with Patient Code",
                description="Clinical image with valid patient identifier",
                condition="has_image_and_patient_code",
                priority=8,
                context=ClinicalContext.PRESSURE_INJURY,
                urgency=ClinicalUrgency.PRIORITY,
                actions=["clinical_image_processing", "lpp_detection"],
                flags=["lpp_assessment", "has_patient_id"]
            ),
            
            TriageRule(
                rule_id="LPP002",
                name="Pressure Injury Keywords",
                description="Text mentions pressure injury terms",
                condition="pressure_injury_keywords",
                priority=7,
                context=ClinicalContext.PRESSURE_INJURY,
                urgency=ClinicalUrgency.ROUTINE,
                actions=["medical_knowledge_query", "protocol_search"],
                flags=["lpp_related", "knowledge_request"]
            ),
            
            # Reglas de protocolo médico
            TriageRule(
                rule_id="PRO001",
                name="Protocol Request",
                description="Request for medical protocols",
                condition="protocol_request",
                priority=6,
                context=ClinicalContext.PROTOCOL_REQUEST,
                urgency=ClinicalUrgency.ROUTINE,
                actions=["protocol_retrieval", "knowledge_base_search"],
                flags=["protocol", "information_request"]
            ),
            
            # Reglas de medicación
            TriageRule(
                rule_id="MED001",
                name="Medication Query",
                description="Questions about medications",
                condition="medication_query",
                priority=7,
                context=ClinicalContext.MEDICATION_QUERY,
                urgency=ClinicalUrgency.PRIORITY,
                actions=["medication_info", "interaction_check"],
                flags=["medication", "pharma_query"]
            ),
            
            # Reglas de validación
            TriageRule(
                rule_id="VAL001",
                name="Missing Patient Identifier",
                description="Clinical image without patient code",
                condition="image_without_patient_code",
                priority=5,
                context=ClinicalContext.UNKNOWN,
                urgency=ClinicalUrgency.ROUTINE,
                actions=["human_review", "patient_id_request"],
                flags=["missing_id", "requires_validation"]
            ),
            
            # Regla por defecto
            TriageRule(
                rule_id="DEF001",
                name="Default Medical Query",
                description="General medical inquiry",
                condition="default",
                priority=1,
                context=ClinicalContext.GENERAL_MEDICAL,
                urgency=ClinicalUrgency.ROUTINE,
                actions=["general_medical_response"],
                flags=["general", "low_priority"]
            )
        ]
    
    def _compile_emergency_patterns(self) -> List[re.Pattern]:
        """Compilar patrones de emergencia."""
        emergency_terms = [
            # Español
            r'\b(emergencia|urgente|crítico|grave|severo|ayuda)\b',
            r'\b(dolor\s+(severo|intenso|insoportable))\b',
            r'\b(sangr(ando|ado|e)|hemorragia)\b',
            r'\b(no\s+puedo\s+respirar|ahog(ando|o))\b',
            r'\b(paro|infarto|convuls)',
            
            # English
            r'\b(emergency|urgent|critical|severe|help)\b',
            r'\b(severe\s+pain|intense\s+pain|unbearable)\b',
            r'\b(bleed(ing)?|hemorrhag(e|ing))\b',
            r'\b(can\'?t\s+breathe|chok(ing|e))\b',
            r'\b(cardiac|heart\s+attack|seizure)\b'
        ]
        
        return [re.compile(pattern, re.IGNORECASE) for pattern in emergency_terms]
    
    def _compile_clinical_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Compilar patrones clínicos por categoría."""
        patterns = {
            "pressure_injury": [
                re.compile(r'\b(lpp|lesión\s+por\s+presión|úlcera\s+por\s+presión)\b', re.IGNORECASE),
                re.compile(r'\b(pressure\s+(injury|ulcer|sore)|bedsore)\b', re.IGNORECASE),
                re.compile(r'\b(escara|decúbito)\b', re.IGNORECASE),
                re.compile(r'\bgrado\s+[1-4]\b', re.IGNORECASE),
                re.compile(r'\bstage\s+[1-4]\b', re.IGNORECASE)
            ],
            
            "medication": [
                re.compile(r'\b(medicamento|medicina|fármaco|dosis)\b', re.IGNORECASE),
                re.compile(r'\b(medication|medicine|drug|dose|dosage)\b', re.IGNORECASE),
                re.compile(r'\b(antibiótico|analgésico|antiinflamatorio)\b', re.IGNORECASE),
                re.compile(r'\b(antibiotic|analgesic|anti-inflammatory)\b', re.IGNORECASE)
            ],
            
            "protocol": [
                re.compile(r'\b(protocolo|procedimiento|guía\s+clínica)\b', re.IGNORECASE),
                re.compile(r'\b(protocol|procedure|clinical\s+guide(line)?)\b', re.IGNORECASE),
                re.compile(r'\b(tratamiento|manejo|cuidado)\b', re.IGNORECASE),
                re.compile(r'\b(treatment|management|care)\b', re.IGNORECASE)
            ],
            
            "wound": [
                re.compile(r'\b(herida|lesión|úlcera|llaga)\b', re.IGNORECASE),
                re.compile(r'\b(wound|injury|ulcer|sore)\b', re.IGNORECASE),
                re.compile(r'\b(tejido|necrosis|infección)\b', re.IGNORECASE),
                re.compile(r'\b(tissue|necrosis|infection)\b', re.IGNORECASE)
            ],
            
            "patient_code": [
                re.compile(r'\b[A-Z]{2}-\d{4}-\d{3}\b'),  # CD-2025-001
                re.compile(r'\bpaciente[\s:]+(\w+)', re.IGNORECASE),
                re.compile(r'\bpatient[\s:]+(\w+)', re.IGNORECASE),
                re.compile(r'\bcódigo[\s:]+(\w+)', re.IGNORECASE),
                re.compile(r'\bcode[\s:]+(\w+)', re.IGNORECASE)
            ]
        }
        
        return patterns
    
    async def perform_triage(self, standardized_input: StandardizedInput) -> TriageResult:
        """
        Realizar triage médico completo.
        
        Args:
            standardized_input: Input estandarizado
            
        Returns:
            TriageResult con decisión y justificación
        """
        try:
            # Extraer información relevante
            text_content = standardized_input.raw_content.get("text", "")
            has_image = standardized_input.metadata.get("has_media", False)
            input_type = standardized_input.input_type
            
            # Detectar contexto clínico
            clinical_context = self._detect_clinical_context(text_content, has_image)
            
            # Detectar urgencia
            urgency = self._assess_urgency(text_content)
            
            # Evaluar reglas
            matched_rules, clinical_flags = self._evaluate_rules(
                text_content, has_image, clinical_context, urgency
            )
            
            # Determinar ruta recomendada
            recommended_route = self._determine_route(
                matched_rules, clinical_context, urgency, has_image
            )
            
            # Calcular confianza
            confidence = self._calculate_confidence(
                matched_rules, clinical_context, text_content
            )
            
            # Determinar si requiere revisión humana
            requires_human = self._requires_human_review(
                confidence, urgency, clinical_flags
            )
            
            # Generar explicación
            explanation = self._generate_explanation(
                clinical_context, urgency, matched_rules, clinical_flags
            )
            
            result = TriageResult(
                urgency=urgency,
                context=clinical_context,
                confidence=confidence,
                matched_rules=[r.rule_id for r in matched_rules],
                recommended_route=recommended_route,
                clinical_flags=clinical_flags,
                explanation=explanation,
                requires_human_review=requires_human,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Log de triage (sin PII)
            logger.audit("medical_triage_completed", {
                "session_id": standardized_input.session_id,
                "urgency": urgency.value,
                "context": clinical_context.value,
                "confidence": confidence,
                "matched_rules": result.matched_rules,
                "requires_human": requires_human
            })
            
            return result
            
        except Exception as e:
            logger.error("triage_engine_error", {
                "session_id": standardized_input.session_id,
                "error": str(e)
            })
            
            # Resultado por defecto en caso de error
            return TriageResult(
                urgency=ClinicalUrgency.PRIORITY,
                context=ClinicalContext.UNKNOWN,
                confidence=0.0,
                matched_rules=["ERROR"],
                recommended_route="human_review",
                clinical_flags=["triage_error", "requires_validation"],
                explanation=f"Triage error: {str(e)}",
                requires_human_review=True,
                timestamp=datetime.now(timezone.utc)
            )
    
    def _detect_clinical_context(self, text: str, has_image: bool) -> ClinicalContext:
        """Detectar contexto clínico del input."""
        if not text and not has_image:
            return ClinicalContext.NON_MEDICAL
        
        text_lower = text.lower()
        
        # Verificar cada categoría de patrones
        for category, patterns in self.clinical_patterns.items():
            for pattern in patterns:
                if pattern.search(text):
                    if category == "pressure_injury":
                        return ClinicalContext.PRESSURE_INJURY
                    elif category == "medication":
                        return ClinicalContext.MEDICATION_QUERY
                    elif category == "protocol":
                        return ClinicalContext.PROTOCOL_REQUEST
                    elif category == "wound":
                        return ClinicalContext.WOUND_ASSESSMENT
        
        # Si hay imagen, asumir contexto de wound assessment
        if has_image:
            return ClinicalContext.WOUND_ASSESSMENT
        
        # Si hay algún contenido médico general
        medical_terms = ["médico", "doctor", "enfermera", "salud", "medical", "health", "nurse"]
        if any(term in text_lower for term in medical_terms):
            return ClinicalContext.GENERAL_MEDICAL
        
        return ClinicalContext.UNKNOWN
    
    def _assess_urgency(self, text: str) -> ClinicalUrgency:
        """Evaluar urgencia clínica."""
        # Verificar patrones de emergencia
        for pattern in self.emergency_patterns:
            if pattern.search(text):
                return ClinicalUrgency.EMERGENCY
        
        # Verificar indicadores de urgencia
        urgent_terms = ["urgente", "urgent", "pronto", "soon", "rápido", "quick", "ahora", "now"]
        if any(term in text.lower() for term in urgent_terms):
            return ClinicalUrgency.URGENT
        
        # Verificar indicadores de prioridad
        priority_terms = ["importante", "important", "necesito", "need", "dolor", "pain"]
        if any(term in text.lower() for term in priority_terms):
            return ClinicalUrgency.PRIORITY
        
        return ClinicalUrgency.ROUTINE
    
    def _evaluate_rules(self, text: str, has_image: bool, 
                       context: ClinicalContext, urgency: ClinicalUrgency) -> Tuple[List[TriageRule], List[str]]:
        """Evaluar reglas de triage."""
        matched_rules = []
        clinical_flags = []
        
        # Evaluar cada regla
        for rule in sorted(self.rules, key=lambda r: r.priority, reverse=True):
            if self._evaluate_rule_condition(rule, text, has_image, context, urgency):
                matched_rules.append(rule)
                clinical_flags.extend(rule.flags)
        
        # Si no hay reglas específicas, usar default
        if not matched_rules:
            default_rule = next((r for r in self.rules if r.rule_id == "DEF001"), None)
            if default_rule:
                matched_rules.append(default_rule)
                clinical_flags.extend(default_rule.flags)
        
        return matched_rules, list(set(clinical_flags))
    
    def _evaluate_rule_condition(self, rule: TriageRule, text: str, 
                                has_image: bool, context: ClinicalContext, 
                                urgency: ClinicalUrgency) -> bool:
        """Evaluar condición de una regla específica."""
        condition = rule.condition
        
        if condition == "emergency_keywords":
            return urgency == ClinicalUrgency.EMERGENCY
        
        elif condition == "severe_pain":
            pain_patterns = [
                r'dolor\s+(severo|intenso|insoportable)',
                r'severe\s+pain',
                r'intense\s+pain'
            ]
            return any(re.search(p, text, re.IGNORECASE) for p in pain_patterns)
        
        elif condition == "has_image_and_patient_code":
            if not has_image:
                return False
            patient_code_found = any(
                pattern.search(text) 
                for pattern in self.clinical_patterns["patient_code"]
            )
            return patient_code_found
        
        elif condition == "pressure_injury_keywords":
            return any(
                pattern.search(text)
                for pattern in self.clinical_patterns["pressure_injury"]
            )
        
        elif condition == "protocol_request":
            return any(
                pattern.search(text)
                for pattern in self.clinical_patterns["protocol"]
            )
        
        elif condition == "medication_query":
            return any(
                pattern.search(text)
                for pattern in self.clinical_patterns["medication"]
            )
        
        elif condition == "image_without_patient_code":
            if not has_image:
                return False
            patient_code_found = any(
                pattern.search(text)
                for pattern in self.clinical_patterns["patient_code"]
            )
            return not patient_code_found
        
        elif condition == "default":
            return True
        
        return False
    
    def _determine_route(self, matched_rules: List[TriageRule], 
                        context: ClinicalContext, urgency: ClinicalUrgency,
                        has_image: bool) -> str:
        """Determinar ruta de procesamiento recomendada."""
        if not matched_rules:
            return "human_review"
        
        # Usar la regla de mayor prioridad
        top_rule = matched_rules[0]
        
        # Mapear acciones a rutas
        if "immediate_escalation" in top_rule.actions:
            return "emergency_escalation"
        elif "clinical_image_processing" in top_rule.actions and has_image:
            return "clinical_image_processing"
        elif "medical_knowledge_query" in top_rule.actions:
            return "medical_knowledge_system"
        elif "human_review" in top_rule.actions:
            return "human_review_queue"
        else:
            return "medical_knowledge_system"
    
    def _calculate_confidence(self, matched_rules: List[TriageRule],
                            context: ClinicalContext, text: str) -> float:
        """Calcular confianza en la decisión de triage."""
        if not matched_rules:
            return 0.0
        
        base_confidence = 0.5
        
        # Bonus por reglas de alta prioridad
        if matched_rules[0].priority >= 8:
            base_confidence += 0.3
        elif matched_rules[0].priority >= 5:
            base_confidence += 0.2
        else:
            base_confidence += 0.1
        
        # Bonus por contexto claro
        if context in [ClinicalContext.PRESSURE_INJURY, ClinicalContext.MEDICATION_QUERY]:
            base_confidence += 0.1
        
        # Penalización por texto ambiguo
        if len(text) < 20 or context == ClinicalContext.UNKNOWN:
            base_confidence -= 0.2
        
        return max(0.0, min(1.0, base_confidence))
    
    def _requires_human_review(self, confidence: float, urgency: ClinicalUrgency,
                              clinical_flags: List[str]) -> bool:
        """Determinar si requiere revisión humana."""
        # Siempre para emergencias
        if urgency == ClinicalUrgency.EMERGENCY:
            return True
        
        # Si hay flags específicos
        human_required_flags = ["human_required", "requires_validation", "triage_error"]
        if any(flag in clinical_flags for flag in human_required_flags):
            return True
        
        # Si la confianza es baja
        if confidence < 0.6:
            return True
        
        return False
    
    def _generate_explanation(self, context: ClinicalContext, urgency: ClinicalUrgency,
                            matched_rules: List[TriageRule], flags: List[str]) -> str:
        """Generar explicación de la decisión de triage."""
        parts = []
        
        # Contexto clínico
        parts.append(f"Clinical context identified: {context.value}")
        
        # Urgencia
        parts.append(f"Urgency level: {urgency.value}")
        
        # Reglas aplicadas
        if matched_rules:
            rule_names = [r.name for r in matched_rules[:3]]  # Top 3 reglas
            parts.append(f"Applied rules: {', '.join(rule_names)}")
        
        # Flags importantes
        important_flags = [f for f in flags if f in ["emergency", "critical", "missing_id"]]
        if important_flags:
            parts.append(f"Clinical flags: {', '.join(important_flags)}")
        
        return " | ".join(parts)


class TriageEngineFactory:
    """Factory para crear instancias de TriageEngine."""
    
    @staticmethod
    def create_engine() -> MedicalTriageEngine:
        """Crear nueva instancia del motor de triage."""
        return MedicalTriageEngine()
    
    @staticmethod
    def create_engine_with_custom_rules(rules: List[TriageRule]) -> MedicalTriageEngine:
        """Crear motor con reglas personalizadas."""
        engine = MedicalTriageEngine()
        engine.rules = rules
        return engine