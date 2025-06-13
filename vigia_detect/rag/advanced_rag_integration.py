"""
Advanced RAG Integration Hub
===========================

Central integration point for all advanced RAG capabilities:
- Multimodal MedCLIP embeddings
- Dynamic clustering
- Incremental training
- Medical explainability

This module orchestrates all advanced RAG features for enhanced medical decision making.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime
import json
import logging
from pathlib import Path

from .multimodal_medclip_service import MedCLIPMultimodalService, create_medclip_service, MultimodalRAGEnhancer
from .dynamic_clustering_service import DynamicMedicalClusteringService, create_clustering_service
from .incremental_training_pipeline import IncrementalTrainingPipeline, create_training_pipeline, TrainingDataType
from .medical_explainability_service import MedicalExplainabilityService, create_explainability_service
from ..systems.medical_decision_engine import make_evidence_based_decision
from ..systems.minsal_medical_decision_engine import make_minsal_clinical_decision

logger = logging.getLogger(__name__)


class AdvancedRAGOrchestrator:
    """
    Advanced RAG orchestrator that integrates all enhanced capabilities
    for comprehensive medical knowledge retrieval and decision support.
    """
    
    def __init__(self):
        """Initialize the advanced RAG orchestrator."""
        # Core services
        self.medclip_service: Optional[MedCLIPMultimodalService] = None
        self.clustering_service: Optional[DynamicMedicalClusteringService] = None
        self.training_pipeline: Optional[IncrementalTrainingPipeline] = None
        self.explainability_service: Optional[MedicalExplainabilityService] = None
        
        # Integration components
        self.multimodal_enhancer: Optional[MultimodalRAGEnhancer] = None
        
        # System state
        self.is_initialized = False
        self.capabilities = {
            'multimodal_search': False,
            'dynamic_clustering': False,
            'incremental_learning': False,
            'explainable_recommendations': False
        }
        
        # Performance metrics
        self.metrics = {
            'total_queries_processed': 0,
            'multimodal_queries': 0,
            'explanations_generated': 0,
            'training_sessions': 0,
            'clusters_identified': 0
        }
        
        logger.info("Advanced RAG orchestrator initialized")
    
    async def initialize(self, enable_all_features: bool = True):
        """
        Initialize all advanced RAG components.
        
        Args:
            enable_all_features: Whether to enable all features or selective initialization
        """
        try:
            logger.info("Initializing advanced RAG components...")
            
            # Initialize MedCLIP multimodal service
            if enable_all_features:
                try:
                    self.medclip_service = await create_medclip_service()
                    self.multimodal_enhancer = MultimodalRAGEnhancer(self.medclip_service)
                    self.capabilities['multimodal_search'] = True
                    logger.info("✅ MedCLIP multimodal service initialized")
                except Exception as e:
                    logger.warning(f"⚠️ MedCLIP initialization failed: {e}")
            
            # Initialize dynamic clustering service
            try:
                self.clustering_service = await create_clustering_service()
                self.capabilities['dynamic_clustering'] = True
                logger.info("✅ Dynamic clustering service initialized")
            except Exception as e:
                logger.warning(f"⚠️ Clustering service initialization failed: {e}")
            
            # Initialize incremental training pipeline
            if enable_all_features:
                try:
                    self.training_pipeline = await create_training_pipeline()
                    self.capabilities['incremental_learning'] = True
                    logger.info("✅ Incremental training pipeline initialized")
                except Exception as e:
                    logger.warning(f"⚠️ Training pipeline initialization failed: {e}")
            
            # Initialize explainability service
            try:
                self.explainability_service = await create_explainability_service()
                self.capabilities['explainable_recommendations'] = True
                logger.info("✅ Medical explainability service initialized")
            except Exception as e:
                logger.warning(f"⚠️ Explainability service initialization failed: {e}")
            
            self.is_initialized = True
            
            enabled_features = sum(self.capabilities.values())
            logger.info(f"🚀 Advanced RAG orchestrator ready with {enabled_features}/4 features enabled")
            
        except Exception as e:
            logger.error(f"Error initializing advanced RAG orchestrator: {e}")
            raise
    
    async def enhanced_medical_query(self, 
                                   query_text: str,
                                   image_path: Optional[str] = None,
                                   patient_context: Optional[Dict[str, Any]] = None,
                                   lpp_grade: Optional[int] = None,
                                   anatomical_location: Optional[str] = None,
                                   jurisdiction: str = "chile",
                                   generate_explanation: bool = True) -> Dict[str, Any]:
        """
        Process enhanced medical query with all advanced RAG capabilities.
        
        Args:
            query_text: Medical query text
            image_path: Optional medical image path
            patient_context: Patient medical context
            lpp_grade: LPP grade if known
            anatomical_location: Anatomical location
            jurisdiction: Medical jurisdiction
            generate_explanation: Whether to generate detailed explanation
            
        Returns:
            Comprehensive medical response with enhanced insights
        """
        try:
            if not self.is_initialized:
                await self.initialize()
            
            logger.info(f"Processing enhanced medical query: {query_text[:50]}...")
            
            # 1. Multimodal knowledge retrieval
            multimodal_results = await self._perform_multimodal_retrieval(
                query_text, image_path, patient_context, lpp_grade, anatomical_location
            )
            
            # 2. Dynamic clustering analysis
            clustering_insights = await self._perform_clustering_analysis(
                query_text, multimodal_results.get('query_embedding'), patient_context
            )
            
            # 3. Enhanced medical decision making
            clinical_decision = await self._make_enhanced_clinical_decision(
                query_text, lpp_grade, anatomical_location, patient_context, 
                multimodal_results, jurisdiction
            )
            
            # 4. Generate comprehensive explanation
            explanation = None
            if generate_explanation and self.explainability_service:
                explanation = await self._generate_comprehensive_explanation(
                    query_text, clinical_decision, multimodal_results, 
                    patient_context, clustering_insights
                )
            
            # 5. Incremental learning opportunity
            await self._capture_learning_opportunity(
                query_text, clinical_decision, patient_context, 
                multimodal_results, explanation
            )
            
            # 6. Compile comprehensive response
            response = self._compile_comprehensive_response(
                query_text, image_path, patient_context, multimodal_results,
                clustering_insights, clinical_decision, explanation
            )
            
            # Update metrics
            self._update_metrics(response)
            
            logger.info(f"Enhanced medical query processed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error processing enhanced medical query: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_recommendation': 'Consulte con un profesional médico para evaluación detallada'
            }
    
    async def _perform_multimodal_retrieval(self, query_text: str, 
                                          image_path: Optional[str],
                                          patient_context: Optional[Dict[str, Any]],
                                          lpp_grade: Optional[int],
                                          anatomical_location: Optional[str]) -> Dict[str, Any]:
        """Perform multimodal knowledge retrieval."""
        if not self.medclip_service:
            logger.warning("MedCLIP service not available, using text-only retrieval")
            return {
                'retrieved_sources': [],
                'query_embedding': None,
                'multimodal_confidence': 0.0,
                'search_type': 'text_only_fallback'
            }
        
        try:
            # Enhanced multimodal search
            if self.multimodal_enhancer:
                enhanced_results = await self.multimodal_enhancer.enhance_clinical_decision_multimodal(
                    lpp_grade=lpp_grade or 0,
                    query_text=query_text,
                    image_path=image_path,
                    patient_context=patient_context or {}
                )
                
                # Get query embedding for clustering
                query_embedding = self.medclip_service.encode_multimodal_query(
                    query_text, image_path, patient_context
                )
                
                return {
                    'retrieved_sources': enhanced_results.get('multimodal_evidence', []),
                    'query_embedding': query_embedding,
                    'multimodal_confidence': enhanced_results.get('retrieval_confidence', 0.0),
                    'search_type': enhanced_results.get('search_type', 'multimodal'),
                    'enhanced_recommendations': enhanced_results.get('enhanced_recommendations', []),
                    'total_results': enhanced_results.get('total_results', 0)
                }
            else:
                # Basic multimodal search
                search_results = await self.medclip_service.search_multimodal_knowledge(
                    query_text=query_text,
                    query_image=image_path,
                    medical_context={'lpp_grade': lpp_grade, **(patient_context or {})},
                    top_k=5
                )
                
                query_embedding = self.medclip_service.encode_multimodal_query(
                    query_text, image_path, patient_context
                )
                
                return {
                    'retrieved_sources': search_results,
                    'query_embedding': query_embedding,
                    'multimodal_confidence': 0.8,  # Default confidence
                    'search_type': 'image_text' if image_path else 'text_only',
                    'total_results': len(search_results)
                }
                
        except Exception as e:
            logger.error(f"Error in multimodal retrieval: {e}")
            return {
                'retrieved_sources': [],
                'query_embedding': None,
                'multimodal_confidence': 0.0,
                'search_type': 'error',
                'error': str(e)
            }
    
    async def _perform_clustering_analysis(self, query_text: str, 
                                         query_embedding: Optional[Any],
                                         patient_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform dynamic clustering analysis."""
        if not self.clustering_service or query_embedding is None:
            return {
                'similar_clusters': [],
                'clustering_insights': [],
                'pattern_analysis': {},
                'status': 'clustering_unavailable'
            }
        
        try:
            # Add query to clustering analysis
            query_id = await self.clustering_service.add_medical_query(
                query_text=query_text,
                embedding=query_embedding,
                lpp_grade=patient_context.get('lpp_grade') if patient_context else None,
                anatomical_location=patient_context.get('anatomical_location') if patient_context else None,
                patient_context=patient_context or {},
                jurisdiction=patient_context.get('jurisdiction', 'chile') if patient_context else 'chile'
            )
            
            # Find similar clusters
            similar_clusters = await self.clustering_service.get_similar_clusters(
                query_embedding=query_embedding,
                top_k=3
            )
            
            # Extract clustering insights
            clustering_insights = []
            for cluster in similar_clusters:
                if cluster['similarity'] > 0.7:  # High similarity threshold
                    insights = cluster.get('medical_insights', {})
                    clustering_insights.extend(insights.get('clinical_recommendations', []))
            
            # Pattern analysis
            pattern_analysis = {
                'total_similar_clusters': len(similar_clusters),
                'high_similarity_clusters': len([c for c in similar_clusters if c['similarity'] > 0.7]),
                'emerging_patterns': [c['cluster_type'] for c in similar_clusters if c['similarity'] > 0.8]
            }
            
            return {
                'query_id': query_id,
                'similar_clusters': similar_clusters,
                'clustering_insights': clustering_insights,
                'pattern_analysis': pattern_analysis,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error in clustering analysis: {e}")
            return {
                'similar_clusters': [],
                'clustering_insights': [],
                'pattern_analysis': {},
                'status': 'error',
                'error': str(e)
            }
    
    async def _make_enhanced_clinical_decision(self, query_text: str,
                                             lpp_grade: Optional[int],
                                             anatomical_location: Optional[str],
                                             patient_context: Optional[Dict[str, Any]],
                                             multimodal_results: Dict[str, Any],
                                             jurisdiction: str) -> Dict[str, Any]:
        """Make enhanced clinical decision using available evidence."""
        try:
            # Determine which decision engine to use
            if jurisdiction.lower() == "chile":
                clinical_decision = make_minsal_clinical_decision(
                    lpp_grade=lpp_grade or 0,
                    confidence=multimodal_results.get('multimodal_confidence', 0.8),
                    anatomical_location=anatomical_location or 'general',
                    patient_context=patient_context
                )
                decision_engine = 'MINSAL_Enhanced'
            else:
                clinical_decision = make_evidence_based_decision(
                    lpp_grade=lpp_grade or 0,
                    confidence=multimodal_results.get('multimodal_confidence', 0.8),
                    anatomical_location=anatomical_location or 'general',
                    patient_context=patient_context
                )
                decision_engine = 'International_NPUAP_EPUAP'
            
            # Enhance decision with multimodal evidence
            if multimodal_results.get('enhanced_recommendations'):
                enhanced_recs = multimodal_results['enhanced_recommendations']
                existing_recs = clinical_decision.get('clinical_recommendations', [])
                clinical_decision['clinical_recommendations'] = existing_recs + enhanced_recs
            
            # Add retrieval metadata
            clinical_decision.update({
                'decision_engine_used': decision_engine,
                'multimodal_evidence_count': len(multimodal_results.get('retrieved_sources', [])),
                'retrieval_confidence': multimodal_results.get('multimodal_confidence', 0.0),
                'search_type': multimodal_results.get('search_type', 'unknown'),
                'query_analysis': {
                    'original_query': query_text,
                    'extracted_lpp_grade': lpp_grade,
                    'extracted_location': anatomical_location,
                    'patient_factors': list(patient_context.keys()) if patient_context else []
                }
            })
            
            return clinical_decision
            
        except Exception as e:
            logger.error(f"Error making enhanced clinical decision: {e}")
            return {
                'error': str(e),
                'fallback_recommendation': 'Error en el procesamiento. Consulte con profesional médico.',
                'decision_engine_used': 'error_fallback'
            }
    
    async def _generate_comprehensive_explanation(self, query_text: str,
                                                clinical_decision: Dict[str, Any],
                                                multimodal_results: Dict[str, Any],
                                                patient_context: Optional[Dict[str, Any]],
                                                clustering_insights: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate comprehensive explanation for the recommendation."""
        if not self.explainability_service:
            return None
        
        try:
            # Prepare recommendation text
            recommendation_text = self._extract_recommendation_text(clinical_decision)
            
            # Prepare confidence scores
            confidence_scores = {
                'retrieval_confidence': multimodal_results.get('multimodal_confidence', 0.0),
                'similarity_confidence': multimodal_results.get('multimodal_confidence', 0.0),
                'clinical_decision_confidence': clinical_decision.get('confidence_score', 0.8),
                'clustering_confidence': len(clustering_insights.get('clustering_insights', [])) * 0.1
            }
            
            # Generate explanation
            explanation = await self.explainability_service.generate_comprehensive_explanation(
                recommendation_id=f"rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                query_text=query_text,
                recommendation_text=recommendation_text,
                retrieved_sources=multimodal_results.get('retrieved_sources', []),
                patient_context=patient_context or {},
                confidence_scores=confidence_scores
            )
            
            return explanation.to_dict()
            
        except Exception as e:
            logger.error(f"Error generating comprehensive explanation: {e}")
            return None
    
    async def _capture_learning_opportunity(self, query_text: str,
                                          clinical_decision: Dict[str, Any],
                                          patient_context: Optional[Dict[str, Any]],
                                          multimodal_results: Dict[str, Any],
                                          explanation: Optional[Dict[str, Any]]):
        """Capture learning opportunity for incremental training."""
        if not self.training_pipeline:
            return
        
        try:
            # Extract recommendation for training
            recommendation_text = self._extract_recommendation_text(clinical_decision)
            
            # Check if this is a high-quality training example
            confidence = multimodal_results.get('multimodal_confidence', 0.0)
            if confidence > 0.8 and recommendation_text:
                # Add to training pipeline
                await self.training_pipeline.add_training_data(
                    query_text=query_text,
                    target_text=recommendation_text,
                    data_type=TrainingDataType.QUERY_RESPONSE_PAIR,
                    medical_context={
                        'lpp_grade': patient_context.get('lpp_grade') if patient_context else None,
                        'anatomical_location': patient_context.get('anatomical_location') if patient_context else None,
                        'decision_engine': clinical_decision.get('decision_engine_used', 'unknown'),
                        'confidence': confidence
                    }
                )
                
                logger.debug(f"Captured learning opportunity for query: {query_text[:30]}...")
                
        except Exception as e:
            logger.error(f"Error capturing learning opportunity: {e}")
    
    def _extract_recommendation_text(self, clinical_decision: Dict[str, Any]) -> str:
        """Extract recommendation text from clinical decision."""
        recommendations = clinical_decision.get('clinical_recommendations', [])
        if isinstance(recommendations, list) and recommendations:
            return '; '.join(recommendations)
        elif isinstance(recommendations, str):
            return recommendations
        else:
            return clinical_decision.get('summary', 'Recomendación médica generada')
    
    def _compile_comprehensive_response(self, query_text: str,
                                      image_path: Optional[str],
                                      patient_context: Optional[Dict[str, Any]],
                                      multimodal_results: Dict[str, Any],
                                      clustering_insights: Dict[str, Any],
                                      clinical_decision: Dict[str, Any],
                                      explanation: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Compile comprehensive response with all advanced insights."""
        
        response = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'query_analysis': {
                'original_query': query_text,
                'has_image': image_path is not None,
                'patient_context_provided': patient_context is not None
            },
            'clinical_decision': clinical_decision,
            'advanced_insights': {
                'multimodal_analysis': {
                    'search_type': multimodal_results.get('search_type', 'unknown'),
                    'confidence': multimodal_results.get('multimodal_confidence', 0.0),
                    'sources_found': len(multimodal_results.get('retrieved_sources', [])),
                    'enhanced_recommendations': multimodal_results.get('enhanced_recommendations', [])
                },
                'clustering_analysis': {
                    'similar_patterns_found': len(clustering_insights.get('similar_clusters', [])),
                    'pattern_insights': clustering_insights.get('clustering_insights', []),
                    'pattern_analysis': clustering_insights.get('pattern_analysis', {})
                },
                'explanation_available': explanation is not None
            },
            'capabilities_used': {
                'multimodal_search': self.capabilities.get('multimodal_search', False),
                'dynamic_clustering': self.capabilities.get('dynamic_clustering', False),
                'incremental_learning': self.capabilities.get('incremental_learning', False),
                'explainable_recommendations': explanation is not None
            }
        }
        
        # Add explanation if available
        if explanation:
            response['detailed_explanation'] = explanation
        
        # Add evidence sources
        if multimodal_results.get('retrieved_sources'):
            response['evidence_sources'] = multimodal_results['retrieved_sources']
        
        return response
    
    def _update_metrics(self, response: Dict[str, Any]):
        """Update orchestrator metrics."""
        self.metrics['total_queries_processed'] += 1
        
        if response.get('query_analysis', {}).get('has_image', False):
            self.metrics['multimodal_queries'] += 1
        
        if response.get('detailed_explanation'):
            self.metrics['explanations_generated'] += 1
        
        if response.get('advanced_insights', {}).get('clustering_analysis', {}).get('similar_patterns_found', 0) > 0:
            self.metrics['clusters_identified'] += 1
    
    async def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator status."""
        status = {
            'is_initialized': self.is_initialized,
            'capabilities': self.capabilities,
            'metrics': self.metrics,
            'service_status': {}
        }
        
        # Check individual service status
        if self.medclip_service:
            status['service_status']['medclip'] = await self.medclip_service.get_multimodal_stats()
        
        if self.clustering_service:
            status['service_status']['clustering'] = await self.clustering_service.get_clustering_statistics()
        
        if self.training_pipeline:
            status['service_status']['training'] = await self.training_pipeline.get_training_statistics()
        
        if self.explainability_service:
            status['service_status']['explainability'] = await self.explainability_service.get_explanation_statistics()
        
        return status
    
    async def optimize_performance(self):
        """Optimize performance across all services."""
        try:
            logger.info("Optimizing advanced RAG performance...")
            
            # Cleanup operations for each service
            if self.clustering_service:
                # Could implement cluster cleanup/optimization
                pass
            
            if self.training_pipeline:
                # Could implement model checkpoint optimization
                pass
            
            # Memory cleanup
            import gc
            gc.collect()
            
            logger.info("Performance optimization completed")
            
        except Exception as e:
            logger.error(f"Error optimizing performance: {e}")


# Factory function for easy instantiation
async def create_advanced_rag_orchestrator(enable_all_features: bool = True) -> AdvancedRAGOrchestrator:
    """
    Create and initialize advanced RAG orchestrator.
    
    Args:
        enable_all_features: Whether to enable all features or selective initialization
        
    Returns:
        Initialized advanced RAG orchestrator
    """
    orchestrator = AdvancedRAGOrchestrator()
    await orchestrator.initialize(enable_all_features=enable_all_features)
    return orchestrator


# Convenience function for enhanced medical queries
async def enhanced_medical_query(query_text: str,
                               image_path: Optional[str] = None,
                               patient_context: Optional[Dict[str, Any]] = None,
                               lpp_grade: Optional[int] = None,
                               anatomical_location: Optional[str] = None,
                               jurisdiction: str = "chile",
                               generate_explanation: bool = True) -> Dict[str, Any]:
    """
    Convenience function for enhanced medical queries.
    
    Args:
        query_text: Medical query text
        image_path: Optional medical image path
        patient_context: Patient medical context
        lpp_grade: LPP grade if known
        anatomical_location: Anatomical location
        jurisdiction: Medical jurisdiction
        generate_explanation: Whether to generate detailed explanation
        
    Returns:
        Comprehensive medical response
    """
    orchestrator = await create_advanced_rag_orchestrator()
    
    return await orchestrator.enhanced_medical_query(
        query_text=query_text,
        image_path=image_path,
        patient_context=patient_context,
        lpp_grade=lpp_grade,
        anatomical_location=anatomical_location,
        jurisdiction=jurisdiction,
        generate_explanation=generate_explanation
    )