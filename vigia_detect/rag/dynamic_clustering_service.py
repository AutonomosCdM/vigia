"""
Dynamic Medical Query Clustering Service
=======================================

Advanced clustering system for medical queries that identifies patterns,
emerging trends, and similar cases for improved medical decision making.
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import logging
from pathlib import Path
import hashlib
from collections import defaultdict, Counter
from enum import Enum

from sklearn.cluster import DBSCAN, KMeans, AgglomerativeClustering
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, calinski_harabasz_score
import scipy.spatial.distance as distance
import redis
import pandas as pd

# Optional imports
try:
    import umap
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False

logger = logging.getLogger(__name__)


class ClusterType(Enum):
    """Types of medical query clusters."""
    SIMILAR_SYMPTOMS = "similar_symptoms"
    TREATMENT_PATTERNS = "treatment_patterns"
    DIAGNOSTIC_QUERIES = "diagnostic_queries"
    PREVENTION_PROTOCOLS = "prevention_protocols"
    EMERGENCY_CASES = "emergency_cases"
    CHRONIC_CONDITIONS = "chronic_conditions"


@dataclass
class MedicalQuery:
    """Medical query data structure."""
    query_id: str
    query_text: str
    lpp_grade: Optional[int]
    anatomical_location: Optional[str]
    patient_context: Dict[str, Any]
    timestamp: datetime
    jurisdiction: str
    embedding: Optional[np.ndarray] = None
    cluster_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        if self.embedding is not None:
            data['embedding'] = self.embedding.tolist()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MedicalQuery':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if 'embedding' in data and data['embedding']:
            data['embedding'] = np.array(data['embedding'])
        return cls(**data)


@dataclass
class MedicalCluster:
    """Medical query cluster representation."""
    cluster_id: int
    cluster_type: ClusterType
    center_embedding: np.ndarray
    query_ids: List[str]
    dominant_patterns: Dict[str, Any]
    creation_time: datetime
    last_updated: datetime
    confidence_score: float
    medical_insights: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['cluster_type'] = self.cluster_type.value
        data['center_embedding'] = self.center_embedding.tolist()
        data['creation_time'] = self.creation_time.isoformat()
        data['last_updated'] = self.last_updated.isoformat()
        return data


class DynamicMedicalClusteringService:
    """
    Dynamic clustering service for medical queries.
    Identifies patterns and emerging trends in medical consultations.
    """
    
    def __init__(self, min_cluster_size: int = 3, similarity_threshold: float = 0.8):
        """
        Initialize dynamic clustering service.
        
        Args:
            min_cluster_size: Minimum queries per cluster
            similarity_threshold: Similarity threshold for clustering
        """
        self.min_cluster_size = min_cluster_size
        self.similarity_threshold = similarity_threshold
        
        # Storage
        self.redis_client = redis.Redis(host='localhost', port=6379, db=4)
        self.queries_buffer = []
        self.active_clusters = {}
        
        # Clustering algorithms
        self.clustering_algorithms = {
            'dbscan': DBSCAN,
            'kmeans': KMeans,
            'agglomerative': AgglomerativeClustering
        }
        
        # Medical pattern matchers
        self.medical_patterns = self._initialize_medical_patterns()
        
        # Statistics
        self.clustering_stats = {
            'total_queries_processed': 0,
            'clusters_created': 0,
            'patterns_identified': 0,
            'last_clustering_time': None
        }
        
        logger.info("Dynamic medical clustering service initialized")
    
    async def add_medical_query(self, query_text: str, 
                              embedding: np.ndarray,
                              lpp_grade: Optional[int] = None,
                              anatomical_location: Optional[str] = None,
                              patient_context: Optional[Dict[str, Any]] = None,
                              jurisdiction: str = "chile") -> str:
        """
        Add new medical query for clustering analysis.
        
        Args:
            query_text: Medical query text
            embedding: Query embedding vector
            lpp_grade: LPP grade if applicable
            anatomical_location: Anatomical location
            patient_context: Patient medical context
            jurisdiction: Medical jurisdiction
            
        Returns:
            Query ID
        """
        try:
            # Generate query ID
            query_id = self._generate_query_id(query_text)
            
            # Create medical query object
            medical_query = MedicalQuery(
                query_id=query_id,
                query_text=query_text,
                lpp_grade=lpp_grade,
                anatomical_location=anatomical_location,
                patient_context=patient_context or {},
                timestamp=datetime.now(),
                jurisdiction=jurisdiction,
                embedding=embedding
            )
            
            # Add to buffer
            self.queries_buffer.append(medical_query)
            
            # Store in Redis
            await self._store_query(medical_query)
            
            # Update statistics
            self.clustering_stats['total_queries_processed'] += 1
            
            # Check if clustering needed
            if len(self.queries_buffer) >= self.min_cluster_size * 2:
                await self._trigger_clustering_analysis()
            
            logger.info(f"Added medical query {query_id} for clustering")
            return query_id
            
        except Exception as e:
            logger.error(f"Error adding medical query: {e}")
            return ""
    
    async def _trigger_clustering_analysis(self):
        """Trigger clustering analysis on buffered queries."""
        try:
            if len(self.queries_buffer) < self.min_cluster_size:
                return
            
            logger.info(f"Starting clustering analysis on {len(self.queries_buffer)} queries")
            
            # Prepare embeddings matrix
            embeddings_matrix = np.array([q.embedding for q in self.queries_buffer])
            
            # Perform multi-algorithm clustering
            clustering_results = await self._perform_multi_algorithm_clustering(
                embeddings_matrix, self.queries_buffer
            )
            
            # Select best clustering
            best_clustering = self._select_best_clustering(clustering_results, embeddings_matrix)
            
            if best_clustering:
                # Create clusters
                await self._create_medical_clusters(best_clustering, self.queries_buffer)
                
                # Analyze patterns
                await self._analyze_cluster_patterns()
                
                # Clear buffer
                self.queries_buffer = []
                
                # Update statistics
                self.clustering_stats['last_clustering_time'] = datetime.now()
                
                logger.info(f"Clustering analysis completed. Created {len(best_clustering['clusters'])} clusters")
            
        except Exception as e:
            logger.error(f"Error in clustering analysis: {e}")
    
    async def _perform_multi_algorithm_clustering(self, embeddings_matrix: np.ndarray, 
                                                queries: List[MedicalQuery]) -> List[Dict[str, Any]]:
        """Perform clustering with multiple algorithms."""
        clustering_results = []
        
        # DBSCAN - good for finding dense regions
        try:
            dbscan = DBSCAN(eps=1-self.similarity_threshold, min_samples=self.min_cluster_size)
            dbscan_labels = dbscan.fit_predict(embeddings_matrix)
            
            clustering_results.append({
                'algorithm': 'dbscan',
                'labels': dbscan_labels,
                'n_clusters': len(set(dbscan_labels)) - (1 if -1 in dbscan_labels else 0),
                'n_noise': list(dbscan_labels).count(-1),
                'silhouette_score': self._safe_silhouette_score(embeddings_matrix, dbscan_labels)
            })
        except Exception as e:
            logger.warning(f"DBSCAN clustering failed: {e}")
        
        # K-Means with different k values
        for n_clusters in range(2, min(8, len(queries) // self.min_cluster_size + 1)):
            try:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                kmeans_labels = kmeans.fit_predict(embeddings_matrix)
                
                clustering_results.append({
                    'algorithm': f'kmeans_{n_clusters}',
                    'labels': kmeans_labels,
                    'n_clusters': n_clusters,
                    'n_noise': 0,
                    'silhouette_score': self._safe_silhouette_score(embeddings_matrix, kmeans_labels),
                    'inertia': kmeans.inertia_
                })
            except Exception as e:
                logger.warning(f"K-Means clustering (k={n_clusters}) failed: {e}")
        
        # Agglomerative clustering
        try:
            n_clusters = min(5, len(queries) // self.min_cluster_size)
            if n_clusters >= 2:
                agg = AgglomerativeClustering(n_clusters=n_clusters)
                agg_labels = agg.fit_predict(embeddings_matrix)
                
                clustering_results.append({
                    'algorithm': f'agglomerative_{n_clusters}',
                    'labels': agg_labels,
                    'n_clusters': n_clusters,
                    'n_noise': 0,
                    'silhouette_score': self._safe_silhouette_score(embeddings_matrix, agg_labels)
                })
        except Exception as e:
            logger.warning(f"Agglomerative clustering failed: {e}")
        
        return clustering_results
    
    def _select_best_clustering(self, clustering_results: List[Dict[str, Any]], 
                              embeddings_matrix: np.ndarray) -> Optional[Dict[str, Any]]:
        """Select best clustering result based on medical criteria."""
        if not clustering_results:
            return None
        
        best_result = None
        best_score = -1
        
        for result in clustering_results:
            # Skip if too few clusters or too many noise points
            if result['n_clusters'] < 2:
                continue
            
            if result['n_noise'] / len(embeddings_matrix) > 0.5:  # Too much noise
                continue
            
            # Calculate composite score
            silhouette = result.get('silhouette_score', 0)
            if silhouette <= 0:
                continue
            
            # Prefer moderate number of clusters for medical data
            cluster_penalty = abs(result['n_clusters'] - 4) * 0.1
            
            # Medical interpretability bonus
            medical_bonus = self._calculate_medical_interpretability_bonus(result)
            
            composite_score = silhouette - cluster_penalty + medical_bonus
            
            if composite_score > best_score:
                best_score = composite_score
                best_result = result
        
        if best_result:
            best_result['composite_score'] = best_score
            # Generate cluster assignments
            best_result['clusters'] = self._organize_clusters(best_result['labels'])
        
        return best_result
    
    def _calculate_medical_interpretability_bonus(self, clustering_result: Dict[str, Any]) -> float:
        """Calculate bonus for medical interpretability."""
        n_clusters = clustering_result['n_clusters']
        
        # Prefer 3-6 clusters for medical data (interpretable range)
        if 3 <= n_clusters <= 6:
            return 0.2
        elif 2 <= n_clusters <= 8:
            return 0.1
        else:
            return 0.0
    
    def _organize_clusters(self, labels: np.ndarray) -> Dict[int, List[int]]:
        """Organize labels into cluster dictionaries."""
        clusters = defaultdict(list)
        for idx, label in enumerate(labels):
            if label != -1:  # Skip noise points
                clusters[label].append(idx)
        return dict(clusters)
    
    async def _create_medical_clusters(self, clustering_result: Dict[str, Any], 
                                     queries: List[MedicalQuery]):
        """Create medical cluster objects from clustering results."""
        try:
            clusters = clustering_result['clusters']
            
            for cluster_id, query_indices in clusters.items():
                if len(query_indices) < self.min_cluster_size:
                    continue
                
                # Get queries in this cluster
                cluster_queries = [queries[i] for i in query_indices]
                query_ids = [q.query_id for q in cluster_queries]
                
                # Calculate cluster center
                cluster_embeddings = np.array([q.embedding for q in cluster_queries])
                center_embedding = np.mean(cluster_embeddings, axis=0)
                
                # Analyze dominant patterns
                dominant_patterns = self._analyze_dominant_patterns(cluster_queries)
                
                # Classify cluster type
                cluster_type = self._classify_cluster_type(cluster_queries, dominant_patterns)
                
                # Generate medical insights
                medical_insights = await self._generate_medical_insights(
                    cluster_queries, dominant_patterns, cluster_type
                )
                
                # Calculate confidence score
                confidence_score = self._calculate_cluster_confidence(
                    cluster_embeddings, center_embedding, dominant_patterns
                )
                
                # Create cluster object
                medical_cluster = MedicalCluster(
                    cluster_id=self._generate_cluster_id(cluster_type, query_ids),
                    cluster_type=cluster_type,
                    center_embedding=center_embedding,
                    query_ids=query_ids,
                    dominant_patterns=dominant_patterns,
                    creation_time=datetime.now(),
                    last_updated=datetime.now(),
                    confidence_score=confidence_score,
                    medical_insights=medical_insights
                )
                
                # Store cluster
                await self._store_cluster(medical_cluster)
                self.active_clusters[medical_cluster.cluster_id] = medical_cluster
                
                # Update statistics
                self.clustering_stats['clusters_created'] += 1
                
                logger.info(f"Created medical cluster {medical_cluster.cluster_id} "
                          f"with {len(query_ids)} queries")
                
        except Exception as e:
            logger.error(f"Error creating medical clusters: {e}")
    
    def _analyze_dominant_patterns(self, queries: List[MedicalQuery]) -> Dict[str, Any]:
        """Analyze dominant patterns in cluster queries."""
        patterns = {
            'lpp_grades': [],
            'anatomical_locations': [],
            'patient_ages': [],
            'comorbidities': [],
            'jurisdictions': [],
            'query_themes': [],
            'temporal_patterns': []
        }
        
        for query in queries:
            # LPP grades
            if query.lpp_grade is not None:
                patterns['lpp_grades'].append(query.lpp_grade)
            
            # Anatomical locations
            if query.anatomical_location:
                patterns['anatomical_locations'].append(query.anatomical_location)
            
            # Patient demographics
            if 'age' in query.patient_context:
                patterns['patient_ages'].append(query.patient_context['age'])
            
            # Comorbidities
            for condition in ['diabetes', 'malnutrition', 'mobility_impaired']:
                if query.patient_context.get(condition, False):
                    patterns['comorbidities'].append(condition)
            
            # Jurisdictions
            patterns['jurisdictions'].append(query.jurisdiction)
            
            # Query themes (simple keyword analysis)
            query_lower = query.query_text.lower()
            if 'treatment' in query_lower or 'tratamiento' in query_lower:
                patterns['query_themes'].append('treatment')
            elif 'prevention' in query_lower or 'prevención' in query_lower:
                patterns['query_themes'].append('prevention')
            elif 'diagnosis' in query_lower or 'diagnóstico' in query_lower:
                patterns['query_themes'].append('diagnosis')
            
            # Temporal patterns (hour of day)
            patterns['temporal_patterns'].append(query.timestamp.hour)
        
        # Calculate dominant values
        dominant_patterns = {}
        for key, values in patterns.items():
            if values:
                if key in ['patient_ages', 'temporal_patterns']:
                    # Numerical data
                    dominant_patterns[key] = {
                        'mean': np.mean(values),
                        'median': np.median(values),
                        'std': np.std(values),
                        'count': len(values)
                    }
                else:
                    # Categorical data
                    counter = Counter(values)
                    dominant_patterns[key] = {
                        'most_common': counter.most_common(3),
                        'distribution': dict(counter),
                        'count': len(values)
                    }
        
        return dominant_patterns
    
    def _classify_cluster_type(self, queries: List[MedicalQuery], 
                             patterns: Dict[str, Any]) -> ClusterType:
        """Classify cluster type based on patterns."""
        # Check query themes
        if 'query_themes' in patterns:
            theme_dist = patterns['query_themes'].get('distribution', {})
            most_common_theme = max(theme_dist.items(), key=lambda x: x[1])[0] if theme_dist else None
            
            if most_common_theme == 'treatment':
                return ClusterType.TREATMENT_PATTERNS
            elif most_common_theme == 'prevention':
                return ClusterType.PREVENTION_PROTOCOLS
            elif most_common_theme == 'diagnosis':
                return ClusterType.DIAGNOSTIC_QUERIES
        
        # Check for emergency patterns
        emergency_keywords = ['urgente', 'emergency', 'crítico', 'severe']
        emergency_count = sum(1 for q in queries 
                            if any(kw in q.query_text.lower() for kw in emergency_keywords))
        
        if emergency_count / len(queries) > 0.5:
            return ClusterType.EMERGENCY_CASES
        
        # Check for chronic conditions
        chronic_indicators = ['diabetes', 'malnutrition', 'mobility_impaired']
        chronic_count = sum(1 for q in queries 
                          if any(q.patient_context.get(ind, False) for ind in chronic_indicators))
        
        if chronic_count / len(queries) > 0.6:
            return ClusterType.CHRONIC_CONDITIONS
        
        # Default to similar symptoms
        return ClusterType.SIMILAR_SYMPTOMS
    
    async def _generate_medical_insights(self, queries: List[MedicalQuery],
                                       patterns: Dict[str, Any],
                                       cluster_type: ClusterType) -> Dict[str, Any]:
        """Generate medical insights for the cluster."""
        insights = {
            'cluster_summary': f'Cluster of {len(queries)} queries of type {cluster_type.value}',
            'clinical_recommendations': [],
            'risk_factors': [],
            'treatment_patterns': [],
            'prevention_opportunities': []
        }
        
        try:
            # Analyze LPP grade patterns
            if 'lpp_grades' in patterns and patterns['lpp_grades']['count'] > 0:
                grade_dist = patterns['lpp_grades']['distribution']
                most_common_grade = max(grade_dist.items(), key=lambda x: x[1])[0]
                
                insights['clinical_recommendations'].append(
                    f"Most common LPP grade in cluster: Grade {most_common_grade}"
                )
                
                if most_common_grade >= 3:
                    insights['clinical_recommendations'].append(
                        "High-grade LPP cluster requires immediate surgical evaluation"
                    )
            
            # Analyze anatomical patterns
            if 'anatomical_locations' in patterns and patterns['anatomical_locations']['count'] > 0:
                location_dist = patterns['anatomical_locations']['distribution']
                most_common_location = max(location_dist.items(), key=lambda x: x[1])[0]
                
                insights['risk_factors'].append(
                    f"Common anatomical location: {most_common_location}"
                )
                
                if most_common_location == 'sacrum':
                    insights['prevention_opportunities'].append(
                        "Sacral LPP cluster indicates positioning protocol review needed"
                    )
            
            # Analyze patient demographics
            if 'patient_ages' in patterns and patterns['patient_ages']['count'] > 0:
                mean_age = patterns['patient_ages']['mean']
                
                if mean_age > 70:
                    insights['risk_factors'].append(
                        f"Elderly population cluster (mean age: {mean_age:.1f})"
                    )
                    insights['clinical_recommendations'].append(
                        "Enhanced geriatric assessment protocols recommended"
                    )
            
            # Analyze comorbidity patterns
            if 'comorbidities' in patterns and patterns['comorbidities']['count'] > 0:
                comorbidity_dist = patterns['comorbidities']['distribution']
                
                for condition, count in comorbidity_dist.items():
                    if count / len(queries) > 0.5:
                        insights['risk_factors'].append(
                            f"High prevalence of {condition} ({count}/{len(queries)} cases)"
                        )
                        
                        if condition == 'diabetes':
                            insights['clinical_recommendations'].append(
                                "Diabetic patients require enhanced wound monitoring"
                            )
            
            # Cluster-type specific insights
            if cluster_type == ClusterType.EMERGENCY_CASES:
                insights['clinical_recommendations'].append(
                    "Emergency cluster requires immediate medical team notification"
                )
            elif cluster_type == ClusterType.TREATMENT_PATTERNS:
                insights['treatment_patterns'].append(
                    "Similar treatment queries suggest potential protocol standardization opportunity"
                )
            elif cluster_type == ClusterType.PREVENTION_PROTOCOLS:
                insights['prevention_opportunities'].append(
                    "Prevention-focused cluster indicates proactive care patterns"
                )
            
        except Exception as e:
            logger.error(f"Error generating medical insights: {e}")
            insights['error'] = str(e)
        
        return insights
    
    def _calculate_cluster_confidence(self, embeddings: np.ndarray, 
                                    center: np.ndarray, 
                                    patterns: Dict[str, Any]) -> float:
        """Calculate confidence score for cluster."""
        # Embedding cohesion (how close embeddings are to center)
        distances = [distance.cosine(emb, center) for emb in embeddings]
        embedding_cohesion = 1 - np.mean(distances)
        
        # Pattern consistency (how consistent the patterns are)
        pattern_scores = []
        
        for key, pattern_data in patterns.items():
            if isinstance(pattern_data, dict) and 'distribution' in pattern_data:
                dist = pattern_data['distribution']
                if dist:
                    # Calculate entropy-based consistency
                    total = sum(dist.values())
                    probs = [count/total for count in dist.values()]
                    entropy = -sum(p * np.log2(p) for p in probs if p > 0)
                    max_entropy = np.log2(len(dist)) if len(dist) > 1 else 1
                    consistency = 1 - (entropy / max_entropy) if max_entropy > 0 else 1
                    pattern_scores.append(consistency)
        
        pattern_consistency = np.mean(pattern_scores) if pattern_scores else 0.5
        
        # Combine scores
        confidence = 0.6 * embedding_cohesion + 0.4 * pattern_consistency
        return max(0, min(1, confidence))
    
    async def get_similar_clusters(self, query_embedding: np.ndarray, 
                                 top_k: int = 3) -> List[Dict[str, Any]]:
        """Find clusters similar to a query embedding."""
        try:
            if not self.active_clusters:
                return []
            
            similarities = []
            
            for cluster_id, cluster in self.active_clusters.items():
                similarity = 1 - distance.cosine(query_embedding, cluster.center_embedding)
                similarities.append({
                    'cluster_id': cluster_id,
                    'cluster_type': cluster.cluster_type.value,
                    'similarity': similarity,
                    'query_count': len(cluster.query_ids),
                    'confidence': cluster.confidence_score,
                    'medical_insights': cluster.medical_insights,
                    'dominant_patterns': cluster.dominant_patterns
                })
            
            # Sort by similarity and return top k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            return similarities[:top_k]
            
        except Exception as e:
            logger.error(f"Error finding similar clusters: {e}")
            return []
    
    async def _analyze_cluster_patterns(self):
        """Analyze patterns across all clusters."""
        try:
            if not self.active_clusters:
                return
            
            # Cross-cluster pattern analysis
            cluster_types = [c.cluster_type for c in self.active_clusters.values()]
            type_distribution = Counter(cluster_types)
            
            # Identify emerging patterns
            emerging_patterns = []
            
            # Check for unusual cluster type distributions
            if type_distribution[ClusterType.EMERGENCY_CASES] > len(self.active_clusters) * 0.3:
                emerging_patterns.append("High emergency case clustering detected")
            
            if type_distribution[ClusterType.PREVENTION_PROTOCOLS] > len(self.active_clusters) * 0.4:
                emerging_patterns.append("Increased focus on prevention protocols")
            
            # Update statistics
            self.clustering_stats['patterns_identified'] = len(emerging_patterns)
            
            # Log patterns
            for pattern in emerging_patterns:
                logger.info(f"Emerging pattern detected: {pattern}")
                
        except Exception as e:
            logger.error(f"Error analyzing cluster patterns: {e}")
    
    def _safe_silhouette_score(self, embeddings: np.ndarray, labels: np.ndarray) -> float:
        """Calculate silhouette score safely."""
        try:
            if len(set(labels)) < 2 or len(embeddings) < 2:
                return 0.0
            
            # Filter out noise points (label -1)
            mask = labels != -1
            if np.sum(mask) < 2:
                return 0.0
            
            filtered_embeddings = embeddings[mask]
            filtered_labels = labels[mask]
            
            if len(set(filtered_labels)) < 2:
                return 0.0
            
            return silhouette_score(filtered_embeddings, filtered_labels)
        except Exception:
            return 0.0
    
    def _initialize_medical_patterns(self) -> Dict[str, List[str]]:
        """Initialize medical pattern matchers."""
        return {
            'treatment_keywords': [
                'treatment', 'tratamiento', 'therapy', 'terapia',
                'medication', 'medicamento', 'antibiotic', 'antibiótico'
            ],
            'prevention_keywords': [
                'prevention', 'prevención', 'prophylaxis', 'profilaxis',
                'risk', 'riesgo', 'positioning', 'posicionamiento'
            ],
            'emergency_keywords': [
                'emergency', 'emergencia', 'urgent', 'urgente',
                'critical', 'crítico', 'severe', 'severo'
            ],
            'diagnostic_keywords': [
                'diagnosis', 'diagnóstico', 'assessment', 'evaluación',
                'classification', 'clasificación', 'staging', 'estadificación'
            ]
        }
    
    def _generate_query_id(self, query_text: str) -> str:
        """Generate unique query ID."""
        timestamp = datetime.now().isoformat()
        content = f"{query_text}:{timestamp}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def _generate_cluster_id(self, cluster_type: ClusterType, query_ids: List[str]) -> str:
        """Generate unique cluster ID."""
        content = f"{cluster_type.value}:{'|'.join(sorted(query_ids))}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def _store_query(self, query: MedicalQuery):
        """Store query in Redis."""
        try:
            self.redis_client.setex(
                f"medical_query:{query.query_id}",
                86400,  # 24 hours
                json.dumps(query.to_dict())
            )
        except Exception as e:
            logger.error(f"Error storing query: {e}")
    
    async def _store_cluster(self, cluster: MedicalCluster):
        """Store cluster in Redis."""
        try:
            self.redis_client.setex(
                f"medical_cluster:{cluster.cluster_id}",
                604800,  # 7 days
                json.dumps(cluster.to_dict())
            )
        except Exception as e:
            logger.error(f"Error storing cluster: {e}")
    
    async def get_clustering_statistics(self) -> Dict[str, Any]:
        """Get clustering service statistics."""
        active_cluster_stats = {
            'total_active_clusters': len(self.active_clusters),
            'clusters_by_type': {}
        }
        
        for cluster in self.active_clusters.values():
            cluster_type = cluster.cluster_type.value
            if cluster_type not in active_cluster_stats['clusters_by_type']:
                active_cluster_stats['clusters_by_type'][cluster_type] = 0
            active_cluster_stats['clusters_by_type'][cluster_type] += 1
        
        return {
            **self.clustering_stats,
            **active_cluster_stats,
            'queries_in_buffer': len(self.queries_buffer),
            'min_cluster_size': self.min_cluster_size,
            'similarity_threshold': self.similarity_threshold
        }


# Factory function
async def create_clustering_service(min_cluster_size: int = 3) -> DynamicMedicalClusteringService:
    """Create and initialize dynamic clustering service."""
    service = DynamicMedicalClusteringService(min_cluster_size=min_cluster_size)
    return service