"""
Medical Explainability Service for RAG Recommendations
=====================================================

Advanced explainability system that provides detailed justification
for medical recommendations, enhancing trust and clinical decision-making.
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import logging
from pathlib import Path
from collections import defaultdict, Counter
from enum import Enum
import hashlib

import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.preprocessing import StandardScaler
import redis

# Optional imports for visualization
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

logger = logging.getLogger(__name__)


class ExplanationType(Enum):
    """Types of medical explanations."""
    SOURCE_ATTRIBUTION = "source_attribution"
    SIMILARITY_ANALYSIS = "similarity_analysis"
    EVIDENCE_HIERARCHY = "evidence_hierarchy"
    DECISION_PATHWAY = "decision_pathway"
    CONFIDENCE_BREAKDOWN = "confidence_breakdown"
    CONTRADICTION_ANALYSIS = "contradiction_analysis"


class EvidenceLevel(Enum):
    """Medical evidence levels."""
    LEVEL_A = "A"  # High-quality evidence
    LEVEL_B = "B"  # Moderate-quality evidence
    LEVEL_C = "C"  # Low-quality evidence
    EXPERT_OPINION = "E"  # Expert opinion


@dataclass
class EvidenceSource:
    """Medical evidence source."""
    source_id: str
    source_type: str  # 'clinical_guideline', 'research_paper', 'protocol', etc.
    title: str
    content: str
    evidence_level: EvidenceLevel
    confidence_score: float
    relevance_score: float
    publication_date: Optional[datetime]
    medical_specialty: str
    jurisdiction: str
    keywords: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['evidence_level'] = self.evidence_level.value
        if self.publication_date:
            data['publication_date'] = self.publication_date.isoformat()
        return data


@dataclass
class ExplanationComponent:
    """Individual explanation component."""
    component_id: str
    explanation_type: ExplanationType
    content: str
    supporting_evidence: List[EvidenceSource]
    confidence_score: float
    visual_data: Optional[Dict[str, Any]]
    medical_rationale: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['explanation_type'] = self.explanation_type.value
        data['supporting_evidence'] = [evidence.to_dict() for evidence in self.supporting_evidence]
        return data


@dataclass
class MedicalExplanation:
    """Complete medical explanation for a recommendation."""
    explanation_id: str
    recommendation_id: str
    patient_context: Dict[str, Any]
    query_text: str
    recommendation_text: str
    overall_confidence: float
    explanation_components: List[ExplanationComponent]
    decision_tree: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    alternative_options: List[Dict[str, Any]]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['explanation_components'] = [comp.to_dict() for comp in self.explanation_components]
        data['created_at'] = self.created_at.isoformat()
        return data


class MedicalExplainabilityService:
    """
    Advanced explainability service for medical RAG recommendations.
    Provides comprehensive justification and visualization of medical decisions.
    """
    
    def __init__(self):
        """Initialize explainability service."""
        self.redis_client = redis.Redis(host='localhost', port=6379, db=6)
        
        # Medical knowledge bases
        self.clinical_guidelines = self._load_clinical_guidelines()
        self.evidence_hierarchy = self._initialize_evidence_hierarchy()
        self.medical_ontology = self._load_medical_ontology()
        
        # Visualization settings
        self.visualization_config = self._initialize_visualization_config()
        
        # Statistics
        self.explanation_stats = {
            'total_explanations_generated': 0,
            'explanations_by_type': defaultdict(int),
            'average_confidence': 0.0,
            'most_cited_sources': Counter()
        }
        
        logger.info("Medical explainability service initialized")
    
    async def generate_comprehensive_explanation(self, 
                                               recommendation_id: str,
                                               query_text: str,
                                               recommendation_text: str,
                                               retrieved_sources: List[Dict[str, Any]],
                                               patient_context: Dict[str, Any],
                                               confidence_scores: Dict[str, float]) -> MedicalExplanation:
        """
        Generate comprehensive explanation for medical recommendation.
        
        Args:
            recommendation_id: Unique recommendation identifier
            query_text: Original medical query
            recommendation_text: Generated recommendation
            retrieved_sources: Sources used in RAG retrieval
            patient_context: Patient medical context
            confidence_scores: Various confidence scores
            
        Returns:
            Comprehensive medical explanation
        """
        try:
            explanation_id = self._generate_explanation_id(recommendation_id)
            
            # Generate different types of explanations
            explanation_components = []
            
            # 1. Source attribution explanation
            source_attribution = await self._generate_source_attribution(
                retrieved_sources, recommendation_text
            )
            explanation_components.append(source_attribution)
            
            # 2. Similarity analysis
            similarity_analysis = await self._generate_similarity_analysis(
                query_text, retrieved_sources, patient_context
            )
            explanation_components.append(similarity_analysis)
            
            # 3. Evidence hierarchy
            evidence_hierarchy = await self._generate_evidence_hierarchy(
                retrieved_sources, recommendation_text
            )
            explanation_components.append(evidence_hierarchy)
            
            # 4. Decision pathway
            decision_pathway = await self._generate_decision_pathway(
                query_text, recommendation_text, patient_context, retrieved_sources
            )
            explanation_components.append(decision_pathway)
            
            # 5. Confidence breakdown
            confidence_breakdown = await self._generate_confidence_breakdown(
                confidence_scores, retrieved_sources, patient_context
            )
            explanation_components.append(confidence_breakdown)
            
            # 6. Contradiction analysis
            contradiction_analysis = await self._generate_contradiction_analysis(
                retrieved_sources, recommendation_text
            )
            explanation_components.append(contradiction_analysis)
            
            # Generate decision tree
            decision_tree = await self._generate_decision_tree(
                query_text, patient_context, retrieved_sources, recommendation_text
            )
            
            # Generate risk assessment
            risk_assessment = await self._generate_risk_assessment(
                patient_context, recommendation_text, retrieved_sources
            )
            
            # Generate alternative options
            alternative_options = await self._generate_alternative_options(
                query_text, patient_context, retrieved_sources, recommendation_text
            )
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(
                confidence_scores, explanation_components
            )
            
            # Create comprehensive explanation
            explanation = MedicalExplanation(
                explanation_id=explanation_id,
                recommendation_id=recommendation_id,
                patient_context=patient_context,
                query_text=query_text,
                recommendation_text=recommendation_text,
                overall_confidence=overall_confidence,
                explanation_components=explanation_components,
                decision_tree=decision_tree,
                risk_assessment=risk_assessment,
                alternative_options=alternative_options,
                created_at=datetime.now()
            )
            
            # Store explanation
            await self._store_explanation(explanation)
            
            # Update statistics
            self._update_explanation_statistics(explanation)
            
            logger.info(f"Generated comprehensive explanation {explanation_id}")
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating comprehensive explanation: {e}")
            raise
    
    async def _generate_source_attribution(self, retrieved_sources: List[Dict[str, Any]], 
                                         recommendation_text: str) -> ExplanationComponent:
        """Generate source attribution explanation."""
        try:
            # Analyze which sources contributed to the recommendation
            source_contributions = []
            
            for source in retrieved_sources:
                content = source.get('content', '')
                similarity_score = source.get('similarity_score', 0.0)
                
                # Calculate contribution score
                contribution_score = self._calculate_source_contribution(
                    content, recommendation_text, similarity_score
                )
                
                # Create evidence source
                evidence_source = EvidenceSource(
                    source_id=source.get('id', 'unknown'),
                    source_type=source.get('source_type', 'unknown'),
                    title=source.get('title', 'Untitled'),
                    content=content,
                    evidence_level=EvidenceLevel(source.get('evidence_level', 'C')),
                    confidence_score=similarity_score,
                    relevance_score=contribution_score,
                    publication_date=None,
                    medical_specialty=source.get('medical_specialty', 'general'),
                    jurisdiction=source.get('jurisdiction', 'international'),
                    keywords=source.get('keywords', [])
                )
                
                source_contributions.append((evidence_source, contribution_score))
            
            # Sort by contribution score
            source_contributions.sort(key=lambda x: x[1], reverse=True)
            
            # Generate explanation content
            explanation_content = self._generate_source_attribution_text(source_contributions)
            
            # Generate visualization data
            visual_data = self._generate_source_attribution_visualization(source_contributions)
            
            # Medical rationale
            medical_rationale = (
                "La recomendación se basa en múltiples fuentes científicas validadas. "
                "Las fuentes con mayor nivel de evidencia (A/B) tienen mayor peso en la decisión final."
            )
            
            return ExplanationComponent(
                component_id=f"source_attr_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                explanation_type=ExplanationType.SOURCE_ATTRIBUTION,
                content=explanation_content,
                supporting_evidence=[contrib[0] for contrib in source_contributions],
                confidence_score=np.mean([contrib[1] for contrib in source_contributions]),
                visual_data=visual_data,
                medical_rationale=medical_rationale
            )
            
        except Exception as e:
            logger.error(f"Error generating source attribution: {e}")
            return self._create_error_explanation_component(ExplanationType.SOURCE_ATTRIBUTION, str(e))
    
    async def _generate_similarity_analysis(self, query_text: str, 
                                          retrieved_sources: List[Dict[str, Any]],
                                          patient_context: Dict[str, Any]) -> ExplanationComponent:
        """Generate similarity analysis explanation."""
        try:
            # Analyze semantic similarity between query and sources
            similarities = []
            
            for source in retrieved_sources:
                content = source.get('content', '')
                similarity = source.get('similarity_score', 0.0)
                
                # Analyze similarity factors
                similarity_factors = self._analyze_similarity_factors(
                    query_text, content, patient_context
                )
                
                similarities.append({
                    'source_title': source.get('title', 'Untitled'),
                    'similarity_score': similarity,
                    'similarity_factors': similarity_factors
                })
            
            # Generate explanation content
            explanation_content = self._generate_similarity_analysis_text(
                query_text, similarities, patient_context
            )
            
            # Generate visualization
            visual_data = self._generate_similarity_visualization(similarities)
            
            # Medical rationale
            medical_rationale = (
                "El análisis de similitud semántica identifica qué tan relevantes son las fuentes "
                "para la consulta específica, considerando el contexto clínico del paciente."
            )
            
            return ExplanationComponent(
                component_id=f"similarity_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                explanation_type=ExplanationType.SIMILARITY_ANALYSIS,
                content=explanation_content,
                supporting_evidence=[],
                confidence_score=np.mean([sim['similarity_score'] for sim in similarities]),
                visual_data=visual_data,
                medical_rationale=medical_rationale
            )
            
        except Exception as e:
            logger.error(f"Error generating similarity analysis: {e}")
            return self._create_error_explanation_component(ExplanationType.SIMILARITY_ANALYSIS, str(e))
    
    async def _generate_evidence_hierarchy(self, retrieved_sources: List[Dict[str, Any]], 
                                         recommendation_text: str) -> ExplanationComponent:
        """Generate evidence hierarchy explanation."""
        try:
            # Organize sources by evidence level
            evidence_by_level = defaultdict(list)
            
            for source in retrieved_sources:
                evidence_level = source.get('evidence_level', 'C')
                evidence_by_level[evidence_level].append(source)
            
            # Calculate evidence strength
            evidence_strength = self._calculate_evidence_strength(evidence_by_level)
            
            # Generate explanation content
            explanation_content = self._generate_evidence_hierarchy_text(
                evidence_by_level, evidence_strength
            )
            
            # Generate visualization
            visual_data = self._generate_evidence_hierarchy_visualization(evidence_by_level)
            
            # Medical rationale
            medical_rationale = (
                "La jerarquía de evidencia médica prioriza fuentes con mayor rigor científico. "
                "Evidencia nivel A (estudios controlados) > Nivel B (estudios observacionales) > "
                "Nivel C (opinión experta)."
            )
            
            return ExplanationComponent(
                component_id=f"evidence_hier_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                explanation_type=ExplanationType.EVIDENCE_HIERARCHY,
                content=explanation_content,
                supporting_evidence=[],
                confidence_score=evidence_strength,
                visual_data=visual_data,
                medical_rationale=medical_rationale
            )
            
        except Exception as e:
            logger.error(f"Error generating evidence hierarchy: {e}")
            return self._create_error_explanation_component(ExplanationType.EVIDENCE_HIERARCHY, str(e))
    
    async def _generate_decision_pathway(self, query_text: str, 
                                       recommendation_text: str,
                                       patient_context: Dict[str, Any],
                                       retrieved_sources: List[Dict[str, Any]]) -> ExplanationComponent:
        """Generate decision pathway explanation."""
        try:
            # Create decision pathway steps
            decision_steps = []
            
            # Step 1: Query analysis
            decision_steps.append({
                'step': 1,
                'description': 'Análisis de consulta médica',
                'details': f'Consulta: "{query_text}"',
                'factors': self._extract_query_factors(query_text, patient_context)
            })
            
            # Step 2: Evidence retrieval
            decision_steps.append({
                'step': 2,
                'description': 'Recuperación de evidencia científica',
                'details': f'Se recuperaron {len(retrieved_sources)} fuentes relevantes',
                'factors': [f'Fuente: {src.get("title", "Untitled")}' for src in retrieved_sources[:3]]
            })
            
            # Step 3: Patient context analysis
            decision_steps.append({
                'step': 3,
                'description': 'Análisis de contexto del paciente',
                'details': 'Consideración de factores específicos del paciente',
                'factors': self._extract_patient_factors(patient_context)
            })
            
            # Step 4: Clinical reasoning
            decision_steps.append({
                'step': 4,
                'description': 'Razonamiento clínico',
                'details': 'Integración de evidencia y contexto del paciente',
                'factors': self._extract_clinical_reasoning_factors(
                    retrieved_sources, patient_context, recommendation_text
                )
            })
            
            # Step 5: Recommendation generation
            decision_steps.append({
                'step': 5,
                'description': 'Generación de recomendación',
                'details': f'Recomendación: "{recommendation_text}"',
                'factors': ['Basada en evidencia científica', 'Adaptada al paciente', 'Protocolo estándar']
            })
            
            # Generate explanation content
            explanation_content = self._generate_decision_pathway_text(decision_steps)
            
            # Generate visualization
            visual_data = self._generate_decision_pathway_visualization(decision_steps)
            
            # Medical rationale
            medical_rationale = (
                "El proceso de decisión clínica sigue una metodología estructurada que integra "
                "evidencia científica con las características específicas del paciente."
            )
            
            return ExplanationComponent(
                component_id=f"decision_path_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                explanation_type=ExplanationType.DECISION_PATHWAY,
                content=explanation_content,
                supporting_evidence=[],
                confidence_score=0.85,  # Default confidence for structured process
                visual_data=visual_data,
                medical_rationale=medical_rationale
            )
            
        except Exception as e:
            logger.error(f"Error generating decision pathway: {e}")
            return self._create_error_explanation_component(ExplanationType.DECISION_PATHWAY, str(e))
    
    async def _generate_confidence_breakdown(self, confidence_scores: Dict[str, float],
                                           retrieved_sources: List[Dict[str, Any]],
                                           patient_context: Dict[str, Any]) -> ExplanationComponent:
        """Generate confidence breakdown explanation."""
        try:
            # Analyze confidence components
            confidence_components = {
                'retrieval_confidence': confidence_scores.get('retrieval_confidence', 0.0),
                'similarity_confidence': confidence_scores.get('similarity_confidence', 0.0),
                'evidence_quality_confidence': self._calculate_evidence_quality_confidence(retrieved_sources),
                'patient_match_confidence': self._calculate_patient_match_confidence(patient_context, retrieved_sources),
                'clinical_consensus_confidence': self._calculate_clinical_consensus_confidence(retrieved_sources)
            }
            
            # Calculate weighted overall confidence
            weights = {
                'retrieval_confidence': 0.2,
                'similarity_confidence': 0.25,
                'evidence_quality_confidence': 0.25,
                'patient_match_confidence': 0.15,
                'clinical_consensus_confidence': 0.15
            }
            
            weighted_confidence = sum(
                confidence_components[component] * weights[component]
                for component in confidence_components
            )
            
            # Generate explanation content
            explanation_content = self._generate_confidence_breakdown_text(
                confidence_components, weighted_confidence
            )
            
            # Generate visualization
            visual_data = self._generate_confidence_breakdown_visualization(confidence_components)
            
            # Medical rationale
            medical_rationale = (
                "La confianza en la recomendación se basa en múltiples factores: calidad de la evidencia, "
                "relevancia semántica, concordancia con el contexto del paciente y consenso clínico."
            )
            
            return ExplanationComponent(
                component_id=f"confidence_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                explanation_type=ExplanationType.CONFIDENCE_BREAKDOWN,
                content=explanation_content,
                supporting_evidence=[],
                confidence_score=weighted_confidence,
                visual_data=visual_data,
                medical_rationale=medical_rationale
            )
            
        except Exception as e:
            logger.error(f"Error generating confidence breakdown: {e}")
            return self._create_error_explanation_component(ExplanationType.CONFIDENCE_BREAKDOWN, str(e))
    
    async def _generate_contradiction_analysis(self, retrieved_sources: List[Dict[str, Any]],
                                             recommendation_text: str) -> ExplanationComponent:
        """Generate contradiction analysis explanation."""
        try:
            # Analyze potential contradictions between sources
            contradictions = []
            
            for i, source1 in enumerate(retrieved_sources):
                for j, source2 in enumerate(retrieved_sources[i+1:], i+1):
                    contradiction_score = self._detect_contradiction(
                        source1.get('content', ''), source2.get('content', '')
                    )
                    
                    if contradiction_score > 0.3:  # Threshold for potential contradiction
                        contradictions.append({
                            'source1': source1.get('title', 'Untitled'),
                            'source2': source2.get('title', 'Untitled'),
                            'contradiction_score': contradiction_score,
                            'explanation': self._explain_contradiction(source1, source2)
                        })
            
            # Analyze consistency with recommendation
            consistency_score = self._calculate_recommendation_consistency(
                retrieved_sources, recommendation_text
            )
            
            # Generate explanation content
            explanation_content = self._generate_contradiction_analysis_text(
                contradictions, consistency_score
            )
            
            # Generate visualization
            visual_data = self._generate_contradiction_visualization(contradictions)
            
            # Medical rationale
            medical_rationale = (
                "El análisis de contradicciones identifica discrepancias entre fuentes científicas "
                "y evalúa la consistencia de la recomendación con la evidencia disponible."
            )
            
            return ExplanationComponent(
                component_id=f"contradiction_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                explanation_type=ExplanationType.CONTRADICTION_ANALYSIS,
                content=explanation_content,
                supporting_evidence=[],
                confidence_score=1.0 - len(contradictions) * 0.1,  # Reduced confidence with contradictions
                visual_data=visual_data,
                medical_rationale=medical_rationale
            )
            
        except Exception as e:
            logger.error(f"Error generating contradiction analysis: {e}")
            return self._create_error_explanation_component(ExplanationType.CONTRADICTION_ANALYSIS, str(e))
    
    def _calculate_source_contribution(self, source_content: str, 
                                     recommendation_text: str, 
                                     similarity_score: float) -> float:
        """Calculate how much a source contributed to the recommendation."""
        # Simple keyword overlap analysis
        source_words = set(source_content.lower().split())
        recommendation_words = set(recommendation_text.lower().split())
        
        overlap = len(source_words.intersection(recommendation_words))
        total_words = len(recommendation_words)
        
        if total_words == 0:
            return similarity_score
        
        keyword_contribution = overlap / total_words
        
        # Combine with similarity score
        return 0.6 * similarity_score + 0.4 * keyword_contribution
    
    def _analyze_similarity_factors(self, query_text: str, source_content: str,
                                  patient_context: Dict[str, Any]) -> List[str]:
        """Analyze factors contributing to similarity."""
        factors = []
        
        query_lower = query_text.lower()
        content_lower = source_content.lower()
        
        # Medical condition matching
        if 'lpp' in query_lower and 'lpp' in content_lower:
            factors.append('Condición médica específica (LPP)')
        
        # Treatment matching
        if 'tratamiento' in query_lower and 'tratamiento' in content_lower:
            factors.append('Enfoque en tratamiento')
        
        # Prevention matching
        if 'prevención' in query_lower and 'prevención' in content_lower:
            factors.append('Enfoque en prevención')
        
        # Patient demographics
        if patient_context.get('age', 0) > 65:
            if 'geriátrico' in content_lower or 'elderly' in content_lower:
                factors.append('Población geriátrica')
        
        # Comorbidities
        if patient_context.get('diabetes', False):
            if 'diabetes' in content_lower:
                factors.append('Comorbilidad diabética')
        
        return factors
    
    def _calculate_evidence_strength(self, evidence_by_level: Dict[str, List]) -> float:
        """Calculate overall evidence strength."""
        level_weights = {'A': 1.0, 'B': 0.7, 'C': 0.4, 'E': 0.2}
        
        total_weight = 0
        total_sources = 0
        
        for level, sources in evidence_by_level.items():
            weight = level_weights.get(level, 0.2)
            total_weight += weight * len(sources)
            total_sources += len(sources)
        
        if total_sources == 0:
            return 0.0
        
        return total_weight / total_sources
    
    def _extract_query_factors(self, query_text: str, patient_context: Dict[str, Any]) -> List[str]:
        """Extract factors from medical query."""
        factors = []
        
        query_lower = query_text.lower()
        
        # Medical conditions
        if 'lpp' in query_lower:
            factors.append('Lesiones por presión')
        
        # Treatment intent
        if 'tratamiento' in query_lower:
            factors.append('Consulta sobre tratamiento')
        elif 'prevención' in query_lower:
            factors.append('Consulta sobre prevención')
        elif 'diagnóstico' in query_lower:
            factors.append('Consulta sobre diagnóstico')
        
        # Urgency
        if 'urgente' in query_lower or 'emergencia' in query_lower:
            factors.append('Consulta urgente')
        
        return factors
    
    def _extract_patient_factors(self, patient_context: Dict[str, Any]) -> List[str]:
        """Extract relevant patient factors."""
        factors = []
        
        # Age
        age = patient_context.get('age', 0)
        if age > 65:
            factors.append(f'Paciente geriátrico ({age} años)')
        elif age < 18:
            factors.append(f'Paciente pediátrico ({age} años)')
        
        # Comorbidities
        if patient_context.get('diabetes', False):
            factors.append('Diabetes mellitus')
        
        if patient_context.get('malnutrition', False):
            factors.append('Malnutrición')
        
        if patient_context.get('mobility_impaired', False):
            factors.append('Movilidad reducida')
        
        # Healthcare system
        if patient_context.get('public_healthcare', True):
            factors.append('Sistema público de salud')
        
        return factors
    
    def _extract_clinical_reasoning_factors(self, retrieved_sources: List[Dict[str, Any]],
                                          patient_context: Dict[str, Any],
                                          recommendation_text: str) -> List[str]:
        """Extract clinical reasoning factors."""
        factors = []
        
        # Evidence-based factors
        high_quality_sources = sum(1 for source in retrieved_sources 
                                 if source.get('evidence_level', 'C') in ['A', 'B'])
        
        if high_quality_sources > 0:
            factors.append(f'Basada en {high_quality_sources} fuentes de alta calidad')
        
        # Patient-specific adaptations
        if patient_context.get('age', 0) > 65:
            factors.append('Adaptada para población geriátrica')
        
        # Treatment approach
        if 'tratamiento' in recommendation_text.lower():
            factors.append('Enfoque terapéutico')
        elif 'prevención' in recommendation_text.lower():
            factors.append('Enfoque preventivo')
        
        return factors
    
    def _calculate_evidence_quality_confidence(self, retrieved_sources: List[Dict[str, Any]]) -> float:
        """Calculate confidence based on evidence quality."""
        if not retrieved_sources:
            return 0.0
        
        level_scores = {'A': 1.0, 'B': 0.8, 'C': 0.6, 'E': 0.4}
        
        scores = [level_scores.get(source.get('evidence_level', 'C'), 0.4) 
                 for source in retrieved_sources]
        
        return np.mean(scores)
    
    def _calculate_patient_match_confidence(self, patient_context: Dict[str, Any],
                                          retrieved_sources: List[Dict[str, Any]]) -> float:
        """Calculate confidence based on patient-source matching."""
        # Simplified patient matching
        match_factors = 0
        total_factors = 0
        
        # Age matching
        patient_age = patient_context.get('age', 0)
        for source in retrieved_sources:
            content = source.get('content', '').lower()
            total_factors += 1
            
            if patient_age > 65 and ('geriátrico' in content or 'elderly' in content):
                match_factors += 1
            elif patient_age < 65 and ('adult' in content or 'adulto' in content):
                match_factors += 1
        
        if total_factors == 0:
            return 0.5
        
        return match_factors / total_factors
    
    def _calculate_clinical_consensus_confidence(self, retrieved_sources: List[Dict[str, Any]]) -> float:
        """Calculate confidence based on clinical consensus."""
        if len(retrieved_sources) < 2:
            return 0.5
        
        # Simplified consensus analysis
        # In a real implementation, this would analyze content similarity and agreement
        return 0.8  # Default consensus score
    
    def _detect_contradiction(self, content1: str, content2: str) -> float:
        """Detect contradiction between two source contents."""
        # Simplified contradiction detection
        contradiction_keywords = [
            ('recommended', 'not recommended'),
            ('effective', 'ineffective'),
            ('safe', 'contraindicated'),
            ('indicated', 'contraindicated')
        ]
        
        content1_lower = content1.lower()
        content2_lower = content2.lower()
        
        contradictions = 0
        for pos_term, neg_term in contradiction_keywords:
            if ((pos_term in content1_lower and neg_term in content2_lower) or
                (neg_term in content1_lower and pos_term in content2_lower)):
                contradictions += 1
        
        return min(1.0, contradictions / len(contradiction_keywords))
    
    def _explain_contradiction(self, source1: Dict[str, Any], source2: Dict[str, Any]) -> str:
        """Explain the nature of contradiction between sources."""
        return (f"Posible discrepancia entre {source1.get('title', 'Fuente 1')} "
                f"y {source2.get('title', 'Fuente 2')} en recomendaciones específicas.")
    
    def _calculate_recommendation_consistency(self, retrieved_sources: List[Dict[str, Any]],
                                           recommendation_text: str) -> float:
        """Calculate consistency between sources and final recommendation."""
        # Simplified consistency calculation
        recommendation_words = set(recommendation_text.lower().split())
        
        consistency_scores = []
        for source in retrieved_sources:
            source_words = set(source.get('content', '').lower().split())
            overlap = len(recommendation_words.intersection(source_words))
            total = len(recommendation_words.union(source_words))
            
            if total > 0:
                consistency_scores.append(overlap / total)
        
        return np.mean(consistency_scores) if consistency_scores else 0.0
    
    # Text generation methods
    def _generate_source_attribution_text(self, source_contributions: List[Tuple]) -> str:
        """Generate source attribution explanation text."""
        text_parts = ["## Atribución de Fuentes\n\n"]
        
        for i, (evidence_source, contribution_score) in enumerate(source_contributions[:3]):
            text_parts.append(
                f"**{i+1}. {evidence_source.title}** "
                f"(Contribución: {contribution_score:.1%}, "
                f"Evidencia: Nivel {evidence_source.evidence_level.value})\n\n"
                f"*Relevancia:* {evidence_source.relevance_score:.1%}\n\n"
            )
        
        return "".join(text_parts)
    
    def _generate_similarity_analysis_text(self, query_text: str, 
                                         similarities: List[Dict], 
                                         patient_context: Dict[str, Any]) -> str:
        """Generate similarity analysis explanation text."""
        text_parts = ["## Análisis de Similitud Semántica\n\n"]
        
        text_parts.append(f"**Consulta original:** {query_text}\n\n")
        
        avg_similarity = np.mean([sim['similarity_score'] for sim in similarities])
        text_parts.append(f"**Similitud promedio:** {avg_similarity:.1%}\n\n")
        
        text_parts.append("**Factores de similitud identificados:**\n")
        for sim in similarities[:3]:
            text_parts.append(f"- {sim['source_title']}: {sim['similarity_score']:.1%}\n")
            for factor in sim['similarity_factors']:
                text_parts.append(f"  - {factor}\n")
        
        return "".join(text_parts)
    
    def _generate_evidence_hierarchy_text(self, evidence_by_level: Dict, 
                                        evidence_strength: float) -> str:
        """Generate evidence hierarchy explanation text."""
        text_parts = ["## Jerarquía de Evidencia Médica\n\n"]
        
        text_parts.append(f"**Fortaleza general de la evidencia:** {evidence_strength:.1%}\n\n")
        
        level_names = {'A': 'Alta calidad', 'B': 'Calidad moderada', 'C': 'Baja calidad', 'E': 'Opinión experta'}
        
        for level in ['A', 'B', 'C', 'E']:
            if level in evidence_by_level:
                sources = evidence_by_level[level]
                text_parts.append(
                    f"**Nivel {level} ({level_names[level]}):** {len(sources)} fuentes\n"
                )
        
        return "".join(text_parts)
    
    def _generate_decision_pathway_text(self, decision_steps: List[Dict]) -> str:
        """Generate decision pathway explanation text."""
        text_parts = ["## Proceso de Decisión Clínica\n\n"]
        
        for step in decision_steps:
            text_parts.append(f"**Paso {step['step']}: {step['description']}**\n")
            text_parts.append(f"{step['details']}\n\n")
            
            if step['factors']:
                text_parts.append("Factores considerados:\n")
                for factor in step['factors']:
                    text_parts.append(f"- {factor}\n")
                text_parts.append("\n")
        
        return "".join(text_parts)
    
    def _generate_confidence_breakdown_text(self, confidence_components: Dict[str, float],
                                          weighted_confidence: float) -> str:
        """Generate confidence breakdown explanation text."""
        text_parts = ["## Desglose de Confianza\n\n"]
        
        text_parts.append(f"**Confianza general:** {weighted_confidence:.1%}\n\n")
        
        component_names = {
            'retrieval_confidence': 'Confianza en recuperación',
            'similarity_confidence': 'Confianza en similitud',
            'evidence_quality_confidence': 'Calidad de la evidencia',
            'patient_match_confidence': 'Concordancia con paciente',
            'clinical_consensus_confidence': 'Consenso clínico'
        }
        
        text_parts.append("**Componentes de confianza:**\n")
        for component, score in confidence_components.items():
            name = component_names.get(component, component)
            text_parts.append(f"- {name}: {score:.1%}\n")
        
        return "".join(text_parts)
    
    def _generate_contradiction_analysis_text(self, contradictions: List[Dict],
                                            consistency_score: float) -> str:
        """Generate contradiction analysis explanation text."""
        text_parts = ["## Análisis de Contradicciones\n\n"]
        
        text_parts.append(f"**Consistencia de la recomendación:** {consistency_score:.1%}\n\n")
        
        if contradictions:
            text_parts.append(f"**Se identificaron {len(contradictions)} posibles contradicciones:**\n\n")
            for contradiction in contradictions:
                text_parts.append(
                    f"- Entre {contradiction['source1']} y {contradiction['source2']} "
                    f"(Score: {contradiction['contradiction_score']:.1%})\n"
                    f"  {contradiction['explanation']}\n\n"
                )
        else:
            text_parts.append("**No se identificaron contradicciones significativas entre las fuentes.**\n")
        
        return "".join(text_parts)
    
    # Visualization methods
    def _generate_source_attribution_visualization(self, source_contributions: List[Tuple]) -> Dict[str, Any]:
        """Generate source attribution visualization data."""
        sources = [contrib[0].title for contrib in source_contributions]
        contributions = [contrib[1] for contrib in source_contributions]
        evidence_levels = [contrib[0].evidence_level.value for contrib in source_contributions]
        
        return {
            'type': 'bar_chart',
            'data': {
                'sources': sources[:5],  # Top 5 sources
                'contributions': contributions[:5],
                'evidence_levels': evidence_levels[:5]
            },
            'title': 'Contribución de Fuentes a la Recomendación'
        }
    
    def _generate_similarity_visualization(self, similarities: List[Dict]) -> Dict[str, Any]:
        """Generate similarity visualization data."""
        return {
            'type': 'similarity_heatmap',
            'data': {
                'sources': [sim['source_title'] for sim in similarities],
                'similarity_scores': [sim['similarity_score'] for sim in similarities]
            },
            'title': 'Análisis de Similitud Semántica'
        }
    
    def _generate_evidence_hierarchy_visualization(self, evidence_by_level: Dict) -> Dict[str, Any]:
        """Generate evidence hierarchy visualization data."""
        levels = []
        counts = []
        
        for level in ['A', 'B', 'C', 'E']:
            if level in evidence_by_level:
                levels.append(f'Nivel {level}')
                counts.append(len(evidence_by_level[level]))
        
        return {
            'type': 'pie_chart',
            'data': {
                'labels': levels,
                'values': counts
            },
            'title': 'Distribución por Nivel de Evidencia'
        }
    
    def _generate_decision_pathway_visualization(self, decision_steps: List[Dict]) -> Dict[str, Any]:
        """Generate decision pathway visualization data."""
        return {
            'type': 'flowchart',
            'data': {
                'steps': [f"Paso {step['step']}: {step['description']}" for step in decision_steps],
                'details': [step['details'] for step in decision_steps]
            },
            'title': 'Proceso de Decisión Clínica'
        }
    
    def _generate_confidence_breakdown_visualization(self, confidence_components: Dict[str, float]) -> Dict[str, Any]:
        """Generate confidence breakdown visualization data."""
        return {
            'type': 'radar_chart',
            'data': {
                'components': list(confidence_components.keys()),
                'scores': list(confidence_components.values())
            },
            'title': 'Desglose de Componentes de Confianza'
        }
    
    def _generate_contradiction_visualization(self, contradictions: List[Dict]) -> Dict[str, Any]:
        """Generate contradiction visualization data."""
        if not contradictions:
            return {
                'type': 'text',
                'data': {'message': 'No se identificaron contradicciones'},
                'title': 'Análisis de Contradicciones'
            }
        
        return {
            'type': 'network_graph',
            'data': {
                'contradictions': [
                    {
                        'source1': c['source1'],
                        'source2': c['source2'],
                        'strength': c['contradiction_score']
                    }
                    for c in contradictions
                ]
            },
            'title': 'Red de Contradicciones entre Fuentes'
        }
    
    # Decision tree and risk assessment
    async def _generate_decision_tree(self, query_text: str, patient_context: Dict[str, Any],
                                    retrieved_sources: List[Dict[str, Any]], 
                                    recommendation_text: str) -> Dict[str, Any]:
        """Generate decision tree for the recommendation."""
        return {
            'root': 'Consulta médica recibida',
            'branches': [
                {
                    'condition': 'Análisis de consulta',
                    'outcome': 'Identificación de necesidad clínica',
                    'children': [
                        {
                            'condition': 'Búsqueda de evidencia',
                            'outcome': f'{len(retrieved_sources)} fuentes recuperadas',
                            'children': [
                                {
                                    'condition': 'Análisis de contexto del paciente',
                                    'outcome': 'Personalización de recomendación',
                                    'children': [
                                        {
                                            'condition': 'Síntesis final',
                                            'outcome': recommendation_text
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    
    async def _generate_risk_assessment(self, patient_context: Dict[str, Any],
                                       recommendation_text: str,
                                       retrieved_sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate risk assessment for the recommendation."""
        risks = []
        
        # Age-related risks
        age = patient_context.get('age', 0)
        if age > 75:
            risks.append({
                'type': 'Alto riesgo geriátrico',
                'level': 'medium',
                'description': 'Paciente mayor de 75 años requiere monitoreo adicional'
            })
        
        # Comorbidity risks
        if patient_context.get('diabetes', False):
            risks.append({
                'type': 'Complicaciones diabéticas',
                'level': 'medium',
                'description': 'Diabetes puede complicar cicatrización'
            })
        
        # Evidence quality risks
        high_quality_sources = sum(1 for source in retrieved_sources 
                                 if source.get('evidence_level', 'C') in ['A', 'B'])
        
        if high_quality_sources < len(retrieved_sources) * 0.5:
            risks.append({
                'type': 'Calidad de evidencia limitada',
                'level': 'low',
                'description': 'Evidencia disponible de calidad moderada'
            })
        
        return {
            'overall_risk_level': 'medium' if len(risks) > 1 else 'low',
            'identified_risks': risks,
            'mitigation_strategies': [
                'Monitoreo clínico frecuente',
                'Seguimiento con especialista si es necesario',
                'Reevaluación en 72 horas'
            ]
        }
    
    async def _generate_alternative_options(self, query_text: str, 
                                          patient_context: Dict[str, Any],
                                          retrieved_sources: List[Dict[str, Any]],
                                          recommendation_text: str) -> List[Dict[str, Any]]:
        """Generate alternative treatment options."""
        alternatives = []
        
        # Based on evidence from sources
        for source in retrieved_sources:
            content = source.get('content', '').lower()
            
            # Look for alternative treatments mentioned
            if 'alternativa' in content or 'alternative' in content:
                alternatives.append({
                    'option': f'Alternativa según {source.get("title", "fuente")}',
                    'description': 'Opción terapéutica alternativa identificada en la evidencia',
                    'evidence_level': source.get('evidence_level', 'C'),
                    'considerations': ['Requiere evaluación adicional', 'Considerar contexto específico']
                })
        
        # Standard alternatives based on condition
        if 'lpp' in query_text.lower():
            alternatives.extend([
                {
                    'option': 'Manejo conservador',
                    'description': 'Enfoque no invasivo con medidas de soporte',
                    'evidence_level': 'B',
                    'considerations': ['Apropiado para casos leves', 'Monitoreo cercano requerido']
                },
                {
                    'option': 'Consulta especializada',
                    'description': 'Derivación a especialista en heridas',
                    'evidence_level': 'A',
                    'considerations': ['Para casos complejos', 'Disponibilidad del especialista']
                }
            ])
        
        return alternatives[:3]  # Limit to top 3 alternatives
    
    # Utility methods
    def _calculate_overall_confidence(self, confidence_scores: Dict[str, float],
                                    explanation_components: List[ExplanationComponent]) -> float:
        """Calculate overall confidence in the explanation."""
        component_confidences = [comp.confidence_score for comp in explanation_components]
        avg_component_confidence = np.mean(component_confidences)
        
        # Weight with provided confidence scores
        provided_confidence = np.mean(list(confidence_scores.values()))
        
        return 0.6 * avg_component_confidence + 0.4 * provided_confidence
    
    def _create_error_explanation_component(self, explanation_type: ExplanationType, 
                                          error_message: str) -> ExplanationComponent:
        """Create error explanation component."""
        return ExplanationComponent(
            component_id=f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            explanation_type=explanation_type,
            content=f"Error generando explicación: {error_message}",
            supporting_evidence=[],
            confidence_score=0.0,
            visual_data=None,
            medical_rationale="Error en el procesamiento de la explicación"
        )
    
    async def _store_explanation(self, explanation: MedicalExplanation):
        """Store explanation in Redis."""
        try:
            self.redis_client.setex(
                f"medical_explanation:{explanation.explanation_id}",
                604800,  # 7 days
                json.dumps(explanation.to_dict())
            )
        except Exception as e:
            logger.error(f"Error storing explanation: {e}")
    
    def _update_explanation_statistics(self, explanation: MedicalExplanation):
        """Update explanation statistics."""
        self.explanation_stats['total_explanations_generated'] += 1
        
        for component in explanation.explanation_components:
            self.explanation_stats['explanations_by_type'][component.explanation_type.value] += 1
        
        # Update average confidence
        total_explanations = self.explanation_stats['total_explanations_generated']
        current_avg = self.explanation_stats['average_confidence']
        new_avg = ((current_avg * (total_explanations - 1)) + explanation.overall_confidence) / total_explanations
        self.explanation_stats['average_confidence'] = new_avg
    
    def _generate_explanation_id(self, recommendation_id: str) -> str:
        """Generate unique explanation ID."""
        content = f"explanation:{recommendation_id}:{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _load_clinical_guidelines(self) -> Dict[str, Any]:
        """Load clinical guidelines for reference."""
        return {
            'npuap_epuap': 'NPUAP/EPUAP Clinical Practice Guidelines 2019',
            'minsal': 'MINSAL Chilean Guidelines 2018',
            'who': 'WHO Medical Guidelines'
        }
    
    def _initialize_evidence_hierarchy(self) -> Dict[str, Dict[str, Any]]:
        """Initialize evidence hierarchy system."""
        return {
            'A': {'weight': 1.0, 'description': 'High-quality evidence'},
            'B': {'weight': 0.8, 'description': 'Moderate-quality evidence'},
            'C': {'weight': 0.6, 'description': 'Low-quality evidence'},
            'E': {'weight': 0.4, 'description': 'Expert opinion'}
        }
    
    def _load_medical_ontology(self) -> Dict[str, List[str]]:
        """Load medical ontology for concept matching."""
        return {
            'lpp': ['lesión por presión', 'úlcera por presión', 'escara'],
            'treatment': ['tratamiento', 'terapia', 'manejo'],
            'prevention': ['prevención', 'profilaxis', 'protección']
        }
    
    def _initialize_visualization_config(self) -> Dict[str, Any]:
        """Initialize visualization configuration."""
        return {
            'color_scheme': 'medical',
            'chart_sizes': {'small': (400, 300), 'medium': (600, 400), 'large': (800, 600)},
            'export_formats': ['png', 'svg', 'html']
        }
    
    async def get_explanation_statistics(self) -> Dict[str, Any]:
        """Get explainability service statistics."""
        return {
            **self.explanation_stats,
            'supported_explanation_types': [etype.value for etype in ExplanationType],
            'evidence_levels': [level.value for level in EvidenceLevel]
        }


# Factory function
async def create_explainability_service() -> MedicalExplainabilityService:
    """Create and initialize medical explainability service."""
    service = MedicalExplainabilityService()
    return service