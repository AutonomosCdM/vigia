"""
MINSAL RAG Enhancement for Medical Decision Engine
=================================================

Enhances the existing RAG system with MINSAL-specific knowledge retrieval
and Chilean medical context integration.
"""

from typing import Dict, List, Any, Optional, Tuple
import json
from pathlib import Path
import logging
from vigia_detect.redis_layer.vector_service import VectorSearchService
from vigia_detect.systems.config.clinical_guidelines import load_clinical_guidelines

logger = logging.getLogger(__name__)


class MINSALRAGEnhancer:
    """
    RAG enhancer for MINSAL medical knowledge integration.
    Extends existing vector search with Chilean medical context.
    """
    
    def __init__(self):
        self.vector_service = VectorSearchService()
        self.minsal_guidelines = self._load_minsal_guidelines()
        self.extracted_info = self._load_extracted_minsal_info()
        
    def enhance_clinical_decision(self, lpp_grade: int, patient_context: Dict[str, Any],
                                clinical_query: str) -> Dict[str, Any]:
        """
        Enhance clinical decision with MINSAL RAG retrieval.
        
        Args:
            lpp_grade: LPP grade (0-6)
            patient_context: Patient medical context
            clinical_query: Natural language query for knowledge retrieval
            
        Returns:
            Enhanced decision with MINSAL knowledge
        """
        try:
            # 1. Search MINSAL-specific protocols
            minsal_protocols = self._search_minsal_protocols(lpp_grade, clinical_query)
            
            # 2. Retrieve patient-contextual recommendations
            contextual_recs = self._get_contextual_recommendations(
                lpp_grade, patient_context
            )
            
            # 3. Find Chilean healthcare system adaptations
            system_adaptations = self._get_healthcare_system_adaptations(patient_context)
            
            # 4. Combine knowledge sources
            enhanced_knowledge = {
                'minsal_protocols': minsal_protocols,
                'contextual_recommendations': contextual_recs,
                'healthcare_adaptations': system_adaptations,
                'evidence_sources': self._get_evidence_sources(lpp_grade),
                'retrieval_confidence': self._calculate_retrieval_confidence(
                    minsal_protocols, contextual_recs
                )
            }
            
            return enhanced_knowledge
            
        except Exception as e:
            logger.error(f"Error in MINSAL RAG enhancement: {e}")
            return {'error': str(e)}
    
    def _search_minsal_protocols(self, lpp_grade: int, query: str) -> List[Dict[str, Any]]:
        """Search for MINSAL-specific protocols"""
        protocols = []
        
        # Search in extracted MINSAL documents
        for doc_name, doc_info in self.extracted_info.items():
            if 'prevention_measures' in doc_info:
                for measure in doc_info['prevention_measures']:
                    if self._is_relevant_to_grade(measure, lpp_grade):
                        protocols.append({
                            'source': f"MINSAL_{doc_name}",
                            'content': measure,
                            'relevance_score': self._calculate_relevance(measure, query),
                            'evidence_level': 'B',  # MINSAL guidelines = Level B
                            'type': 'prevention'
                        })
            
            if 'treatment_recommendations' in doc_info:
                for treatment in doc_info['treatment_recommendations']:
                    if self._is_relevant_to_grade(treatment, lpp_grade):
                        protocols.append({
                            'source': f"MINSAL_{doc_name}",
                            'content': treatment,
                            'relevance_score': self._calculate_relevance(treatment, query),
                            'evidence_level': 'B',
                            'type': 'treatment'
                        })
        
        # Sort by relevance and return top results
        protocols.sort(key=lambda x: x['relevance_score'], reverse=True)
        return protocols[:5]
    
    def _get_contextual_recommendations(self, lpp_grade: int, 
                                      patient_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get patient-contextual recommendations"""
        recommendations = []
        
        # Chilean population-specific factors
        if patient_context.get('age', 0) > 65:
            recommendations.append({
                'context': 'elderly_chilean_population',
                'recommendation': 'Evaluación geriátrica integral según protocolos MINSAL',
                'source': 'MINSAL Geriatric Guidelines',
                'priority': 'high'
            })
        
        if patient_context.get('diabetes', False):
            recommendations.append({
                'context': 'diabetes_chilean_prevalence',
                'recommendation': 'Control glucémico estricto según Guía MINSAL Diabetes',
                'source': 'MINSAL Diabetes Guidelines 2017',
                'priority': 'high'
            })
        
        if patient_context.get('public_healthcare', True):
            recommendations.append({
                'context': 'public_healthcare_resources',
                'recommendation': 'Optimización recursos según disponibilidad sistema público',
                'source': 'MINSAL Resource Management',
                'priority': 'medium'
            })
        
        return recommendations
    
    def _get_healthcare_system_adaptations(self, patient_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get Chilean healthcare system specific adaptations"""
        adaptations = {
            'system_type': 'mixed_public_private',
            'available_resources': [],
            'referral_pathways': [],
            'cost_considerations': []
        }
        
        if patient_context.get('public_healthcare', True):
            adaptations['available_resources'].extend([
                'Colchones antiescaras básicos disponibles',
                'Apósitos hidrocoloides sistema público',
                'Evaluación nutricional según protocolo MINSAL'
            ])
            
            adaptations['referral_pathways'].extend([
                'Derivación a especialista heridas vía interconsulta',
                'Evaluación quirúrgica según criterios GES',
                'Seguimiento en atención primaria'
            ])
            
        return adaptations
    
    def _get_evidence_sources(self, lpp_grade: int) -> List[Dict[str, str]]:
        """Get evidence sources for specific LPP grade"""
        base_sources = [
            {
                'source': 'NPUAP/EPUAP/PPPIA',
                'reference': 'Clinical Practice Guideline 2019',
                'evidence_level': 'A'
            }
        ]
        
        # Add MINSAL sources
        minsal_sources = [
            {
                'source': 'MINSAL',
                'reference': 'Orientación Técnica Prevención LPP 2018',
                'evidence_level': 'B'
            },
            {
                'source': 'MINSAL',
                'reference': 'ULCERAS POR PRESION MINISTERIO 2015',
                'evidence_level': 'B'
            }
        ]
        
        if lpp_grade >= 3:
            minsal_sources.append({
                'source': 'Hospital Coquimbo',
                'reference': 'Protocolo Prevención UPP 2021',
                'evidence_level': 'C'
            })
        
        return base_sources + minsal_sources
    
    def _is_relevant_to_grade(self, content: str, lpp_grade: int) -> bool:
        """Check if content is relevant to LPP grade"""
        grade_keywords = {
            0: ['prevención', 'preventiva', 'riesgo'],
            1: ['eritema', 'categoría i', 'grado i'],
            2: ['categoría ii', 'grado ii', 'espesor parcial'],
            3: ['categoría iii', 'grado iii', 'espesor total'],
            4: ['categoría iv', 'grado iv', 'hueso', 'músculo']
        }
        
        keywords = grade_keywords.get(lpp_grade, [])
        content_lower = content.lower()
        
        return any(keyword in content_lower for keyword in keywords)
    
    def _calculate_relevance(self, content: str, query: str) -> float:
        """Calculate relevance score (simple implementation)"""
        query_terms = query.lower().split()
        content_lower = content.lower()
        
        matches = sum(1 for term in query_terms if term in content_lower)
        return matches / len(query_terms) if query_terms else 0.0
    
    def _calculate_retrieval_confidence(self, protocols: List[Dict], 
                                      recommendations: List[Dict]) -> float:
        """Calculate confidence in retrieved knowledge"""
        if not protocols and not recommendations:
            return 0.0
        
        total_items = len(protocols) + len(recommendations)
        high_relevance = sum(1 for p in protocols if p.get('relevance_score', 0) > 0.7)
        high_relevance += sum(1 for r in recommendations if r.get('priority') == 'high')
        
        return min(1.0, high_relevance / total_items if total_items > 0 else 0.5)
    
    def _load_minsal_guidelines(self) -> Dict[str, Any]:
        """Load MINSAL guidelines configuration"""
        try:
            config_path = Path("vigia_detect/systems/config/clinical_guidelines.json")
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading MINSAL guidelines: {e}")
        return {}
    
    def _load_extracted_minsal_info(self) -> Dict[str, Any]:
        """Load extracted MINSAL information"""
        try:
            info_path = Path("vigia_detect/systems/config/minsal_extracted_info.json")
            if info_path.exists():
                with open(info_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading extracted MINSAL info: {e}")
        return {}


# Integration function for MINSAL decision engine
async def enhance_minsal_decision_with_rag(lpp_grade: int, confidence: float,
                                         anatomical_location: str,
                                         patient_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance MINSAL clinical decision with RAG knowledge retrieval.
    
    This function should be called from the MINSAL decision engine to add
    retrieved knowledge context to clinical decisions.
    """
    enhancer = MINSALRAGEnhancer()
    
    # Construct clinical query
    clinical_query = f"LPP grado {lpp_grade} {anatomical_location} tratamiento prevención"
    
    # Get enhanced knowledge
    enhanced_knowledge = enhancer.enhance_clinical_decision(
        lpp_grade, patient_context, clinical_query
    )
    
    return enhanced_knowledge