"""
Incremental Training Pipeline for Medical Embeddings
===================================================

Advanced pipeline for continuous improvement of medical embeddings
through incremental learning with validated clinical data.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import logging
from pathlib import Path
import numpy as np
import pickle
from collections import defaultdict
import hashlib
from enum import Enum

from sentence_transformers import SentenceTransformer, losses, evaluation
from sentence_transformers.util import cos_sim
from transformers import AutoModel, AutoTokenizer
import redis
import sqlite3
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Status of medical data validation."""
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"
    EXPERT_REVIEW = "expert_review"


class TrainingDataType(Enum):
    """Types of training data."""
    QUERY_RESPONSE_PAIR = "query_response_pair"
    SIMILAR_QUERIES = "similar_queries"
    MEDICAL_CLASSIFICATION = "medical_classification"
    CLINICAL_OUTCOME = "clinical_outcome"


@dataclass
class MedicalTrainingData:
    """Medical training data point."""
    data_id: str
    data_type: TrainingDataType
    query_text: str
    target_text: Optional[str]
    similarity_score: Optional[float]
    medical_classification: Optional[str]
    patient_outcome: Optional[Dict[str, Any]]
    validation_status: ValidationStatus
    medical_context: Dict[str, Any]
    created_at: datetime
    validated_at: Optional[datetime]
    validator_id: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['data_type'] = self.data_type.value
        data['validation_status'] = self.validation_status.value
        data['created_at'] = self.created_at.isoformat()
        if self.validated_at:
            data['validated_at'] = self.validated_at.isoformat()
        return data


@dataclass
class TrainingBatch:
    """Training batch for incremental learning."""
    batch_id: str
    training_data: List[MedicalTrainingData]
    batch_size: int
    creation_time: datetime
    training_metrics: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'batch_id': self.batch_id,
            'batch_size': self.batch_size,
            'creation_time': self.creation_time.isoformat(),
            'training_metrics': self.training_metrics,
            'data_ids': [data.data_id for data in self.training_data]
        }


class MedicalEmbeddingModel(nn.Module):
    """
    Custom medical embedding model for incremental training.
    """
    
    def __init__(self, base_model_name: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'):
        super().__init__()
        self.base_model = SentenceTransformer(base_model_name)
        self.embedding_dim = self.base_model.get_sentence_embedding_dimension()
        
        # Add medical adaptation layers
        self.medical_adapter = nn.Sequential(
            nn.Linear(self.embedding_dim, self.embedding_dim * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(self.embedding_dim * 2, self.embedding_dim),
            nn.LayerNorm(self.embedding_dim)
        )
        
        # Medical classification head (optional)
        self.classification_head = nn.Sequential(
            nn.Linear(self.embedding_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 7)  # LPP grades 0-6
        )
    
    def forward(self, input_texts: List[str]) -> torch.Tensor:
        """Forward pass through the model."""
        # Get base embeddings
        with torch.no_grad():
            base_embeddings = self.base_model.encode(input_texts, convert_to_tensor=True)
        
        # Apply medical adaptation
        adapted_embeddings = self.medical_adapter(base_embeddings)
        
        return adapted_embeddings
    
    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode texts to embeddings."""
        self.eval()
        with torch.no_grad():
            embeddings = self.forward(texts)
            return embeddings.cpu().numpy()
    
    def classify_lpp(self, embeddings: torch.Tensor) -> torch.Tensor:
        """Classify LPP grade from embeddings."""
        return self.classification_head(embeddings)


class MedicalTrainingDataset(Dataset):
    """Dataset for medical training data."""
    
    def __init__(self, training_data: List[MedicalTrainingData], data_type: TrainingDataType):
        self.training_data = [data for data in training_data if data.data_type == data_type]
        self.data_type = data_type
    
    def __len__(self) -> int:
        return len(self.training_data)
    
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        data = self.training_data[idx]
        
        item = {
            'query_text': data.query_text,
            'medical_context': data.medical_context
        }
        
        if self.data_type == TrainingDataType.QUERY_RESPONSE_PAIR:
            item['target_text'] = data.target_text
        elif self.data_type == TrainingDataType.SIMILAR_QUERIES:
            item['similarity_score'] = data.similarity_score
            item['target_text'] = data.target_text
        elif self.data_type == TrainingDataType.MEDICAL_CLASSIFICATION:
            item['classification'] = data.medical_classification
        elif self.data_type == TrainingDataType.CLINICAL_OUTCOME:
            item['outcome'] = data.patient_outcome
        
        return item


class IncrementalTrainingPipeline:
    """
    Incremental training pipeline for medical embeddings.
    Continuously improves embeddings with validated clinical data.
    """
    
    def __init__(self, base_model_name: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
                 min_batch_size: int = 32, validation_threshold: float = 0.8):
        """
        Initialize incremental training pipeline.
        
        Args:
            base_model_name: Base sentence transformer model
            min_batch_size: Minimum batch size for training
            validation_threshold: Minimum validation score to accept data
        """
        self.base_model_name = base_model_name
        self.min_batch_size = min_batch_size
        self.validation_threshold = validation_threshold
        
        # Model components
        self.model = None
        self.tokenizer = None
        self.optimizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Training data storage
        self.redis_client = redis.Redis(host='localhost', port=6379, db=5)
        self.training_data_buffer = []
        self.validated_data = []
        
        # Training statistics
        self.training_stats = {
            'total_training_sessions': 0,
            'total_data_points_processed': 0,
            'total_validated_data': 0,
            'last_training_time': None,
            'current_model_version': '1.0.0',
            'improvement_metrics': []
        }
        
        # Data validation
        self.medical_validators = self._initialize_medical_validators()
        
        # Model versioning
        self.model_versions = {}
        
        logger.info(f"Initialized incremental training pipeline on {self.device}")
    
    async def initialize(self):
        """Initialize the training pipeline."""
        try:
            # Load or create medical embedding model
            self.model = MedicalEmbeddingModel(self.base_model_name).to(self.device)
            
            # Initialize optimizer
            self.optimizer = optim.AdamW(
                self.model.parameters(),
                lr=1e-5,
                weight_decay=0.01
            )
            
            # Load existing validated data
            await self._load_existing_training_data()
            
            logger.info("Incremental training pipeline initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing training pipeline: {e}")
            raise
    
    async def add_training_data(self, query_text: str, 
                              target_text: Optional[str] = None,
                              data_type: TrainingDataType = TrainingDataType.QUERY_RESPONSE_PAIR,
                              medical_context: Optional[Dict[str, Any]] = None,
                              similarity_score: Optional[float] = None,
                              medical_classification: Optional[str] = None,
                              patient_outcome: Optional[Dict[str, Any]] = None) -> str:
        """
        Add new training data point for validation and potential training.
        
        Args:
            query_text: Medical query text
            target_text: Target response/similar query
            data_type: Type of training data
            medical_context: Medical context
            similarity_score: Similarity score for similar queries
            medical_classification: Medical classification label
            patient_outcome: Patient outcome data
            
        Returns:
            Data ID
        """
        try:
            # Generate data ID
            data_id = self._generate_data_id(query_text, target_text)
            
            # Create training data object
            training_data = MedicalTrainingData(
                data_id=data_id,
                data_type=data_type,
                query_text=query_text,
                target_text=target_text,
                similarity_score=similarity_score,
                medical_classification=medical_classification,
                patient_outcome=patient_outcome,
                validation_status=ValidationStatus.PENDING,
                medical_context=medical_context or {},
                created_at=datetime.now(),
                validated_at=None,
                validator_id=None
            )
            
            # Add to buffer
            self.training_data_buffer.append(training_data)
            
            # Store in Redis
            await self._store_training_data(training_data)
            
            # Trigger validation
            validation_result = await self._validate_training_data(training_data)
            
            if validation_result['status'] == ValidationStatus.VALIDATED:
                self.validated_data.append(training_data)
                training_data.validation_status = ValidationStatus.VALIDATED
                training_data.validated_at = datetime.now()
                
                # Update statistics
                self.training_stats['total_validated_data'] += 1
                
                # Check if ready for incremental training
                if len(self.validated_data) >= self.min_batch_size:
                    await self._trigger_incremental_training()
            
            logger.info(f"Added training data {data_id} with validation status: {validation_result['status']}")
            return data_id
            
        except Exception as e:
            logger.error(f"Error adding training data: {e}")
            return ""
    
    async def _validate_training_data(self, training_data: MedicalTrainingData) -> Dict[str, Any]:
        """Validate training data using medical validators."""
        try:
            validation_scores = []
            validation_details = []
            
            # Medical relevance validation
            relevance_score = await self._validate_medical_relevance(training_data)
            validation_scores.append(relevance_score)
            validation_details.append(f"Medical relevance: {relevance_score:.2f}")
            
            # Quality validation
            quality_score = await self._validate_data_quality(training_data)
            validation_scores.append(quality_score)
            validation_details.append(f"Data quality: {quality_score:.2f}")
            
            # Consistency validation
            consistency_score = await self._validate_consistency(training_data)
            validation_scores.append(consistency_score)
            validation_details.append(f"Consistency: {consistency_score:.2f}")
            
            # Calculate overall validation score
            overall_score = np.mean(validation_scores)
            
            # Determine validation status
            if overall_score >= self.validation_threshold:
                status = ValidationStatus.VALIDATED
            elif overall_score >= 0.6:
                status = ValidationStatus.EXPERT_REVIEW
            else:
                status = ValidationStatus.REJECTED
            
            return {
                'status': status,
                'overall_score': overall_score,
                'individual_scores': validation_scores,
                'details': validation_details
            }
            
        except Exception as e:
            logger.error(f"Error validating training data: {e}")
            return {
                'status': ValidationStatus.REJECTED,
                'overall_score': 0.0,
                'error': str(e)
            }
    
    async def _validate_medical_relevance(self, training_data: MedicalTrainingData) -> float:
        """Validate medical relevance of training data."""
        medical_keywords = [
            'lpp', 'lesión', 'úlcera', 'wound', 'pressure', 'injury',
            'treatment', 'tratamiento', 'diagnosis', 'diagnóstico',
            'prevention', 'prevención', 'protocol', 'protocolo'
        ]
        
        text_to_check = training_data.query_text.lower()
        if training_data.target_text:
            text_to_check += " " + training_data.target_text.lower()
        
        # Count medical keywords
        keyword_count = sum(1 for keyword in medical_keywords if keyword in text_to_check)
        relevance_score = min(1.0, keyword_count / 3.0)  # Normalize to 0-1
        
        # Bonus for medical context
        if training_data.medical_context:
            if any(key in training_data.medical_context for key in ['lpp_grade', 'anatomical_location']):
                relevance_score += 0.2
        
        return min(1.0, relevance_score)
    
    async def _validate_data_quality(self, training_data: MedicalTrainingData) -> float:
        """Validate data quality."""
        quality_score = 0.0
        
        # Text length validation
        query_length = len(training_data.query_text.split())
        if 5 <= query_length <= 100:  # Reasonable length
            quality_score += 0.3
        
        # Target validation (if applicable)
        if training_data.target_text:
            target_length = len(training_data.target_text.split())
            if 5 <= target_length <= 200:
                quality_score += 0.3
        else:
            quality_score += 0.3  # No target required for some data types
        
        # Medical context validation
        if training_data.medical_context:
            if len(training_data.medical_context) > 0:
                quality_score += 0.2
        
        # Language consistency
        if self._check_language_consistency(training_data):
            quality_score += 0.2
        
        return quality_score
    
    async def _validate_consistency(self, training_data: MedicalTrainingData) -> float:
        """Validate consistency with existing validated data."""
        if not self.validated_data:
            return 0.8  # Default score for first data points
        
        try:
            # Encode current data
            current_embedding = self.model.encode([training_data.query_text])[0]
            
            # Compare with existing validated data (sample)
            sample_size = min(20, len(self.validated_data))
            sample_data = np.random.choice(self.validated_data, sample_size, replace=False)
            
            similarities = []
            for data in sample_data:
                existing_embedding = self.model.encode([data.query_text])[0]
                similarity = float(cos_sim(
                    torch.tensor(current_embedding), 
                    torch.tensor(existing_embedding)
                ).item())
                similarities.append(similarity)
            
            # Check for reasonable similarity range (not too similar, not too different)
            mean_similarity = np.mean(similarities)
            
            if 0.3 <= mean_similarity <= 0.8:  # Good diversity range
                return 0.9
            elif 0.1 <= mean_similarity <= 0.9:  # Acceptable range
                return 0.7
            else:
                return 0.5  # Too similar or too different
                
        except Exception as e:
            logger.warning(f"Error in consistency validation: {e}")
            return 0.6  # Default score on error
    
    def _check_language_consistency(self, training_data: MedicalTrainingData) -> bool:
        """Check language consistency within training data."""
        spanish_indicators = ['lesión', 'úlcera', 'tratamiento', 'prevención', 'diagnóstico']
        english_indicators = ['pressure', 'injury', 'treatment', 'prevention', 'diagnosis']
        
        query_text = training_data.query_text.lower()
        
        spanish_count = sum(1 for ind in spanish_indicators if ind in query_text)
        english_count = sum(1 for ind in english_indicators if ind in query_text)
        
        # Check target text if available
        if training_data.target_text:
            target_text = training_data.target_text.lower()
            target_spanish = sum(1 for ind in spanish_indicators if ind in target_text)
            target_english = sum(1 for ind in english_indicators if ind in target_text)
            
            # Language should be consistent between query and target
            return (spanish_count > english_count) == (target_spanish > target_english)
        
        return True  # Single text is always consistent
    
    async def _trigger_incremental_training(self):
        """Trigger incremental training with validated data."""
        try:
            if len(self.validated_data) < self.min_batch_size:
                logger.info("Not enough validated data for training")
                return
            
            logger.info(f"Starting incremental training with {len(self.validated_data)} validated data points")
            
            # Create training batch
            training_batch = self._create_training_batch(self.validated_data[-self.min_batch_size:])
            
            # Perform incremental training
            training_metrics = await self._perform_incremental_training(training_batch)
            
            # Evaluate model improvement
            improvement_metrics = await self._evaluate_model_improvement(training_metrics)
            
            # Update model version if improved
            if improvement_metrics['improved']:
                await self._update_model_version(training_metrics, improvement_metrics)
            
            # Update statistics
            self.training_stats['total_training_sessions'] += 1
            self.training_stats['total_data_points_processed'] += len(training_batch.training_data)
            self.training_stats['last_training_time'] = datetime.now()
            self.training_stats['improvement_metrics'].append(improvement_metrics)
            
            # Clear used validated data
            self.validated_data = self.validated_data[self.min_batch_size:]
            
            logger.info(f"Incremental training completed. Model improved: {improvement_metrics['improved']}")
            
        except Exception as e:
            logger.error(f"Error in incremental training: {e}")
    
    def _create_training_batch(self, training_data: List[MedicalTrainingData]) -> TrainingBatch:
        """Create training batch from validated data."""
        batch_id = self._generate_batch_id(training_data)
        
        return TrainingBatch(
            batch_id=batch_id,
            training_data=training_data,
            batch_size=len(training_data),
            creation_time=datetime.now()
        )
    
    async def _perform_incremental_training(self, training_batch: TrainingBatch) -> Dict[str, float]:
        """Perform incremental training on the batch."""
        try:
            self.model.train()
            
            # Group data by type
            data_by_type = defaultdict(list)
            for data in training_batch.training_data:
                data_by_type[data.data_type].append(data)
            
            total_loss = 0.0
            num_batches = 0
            
            # Train on each data type
            for data_type, data_list in data_by_type.items():
                if len(data_list) < 2:
                    continue
                
                dataset = MedicalTrainingDataset(data_list, data_type)
                dataloader = DataLoader(dataset, batch_size=min(8, len(data_list)), shuffle=True)
                
                for batch in dataloader:
                    loss = await self._compute_training_loss(batch, data_type)
                    
                    self.optimizer.zero_grad()
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                    self.optimizer.step()
                    
                    total_loss += loss.item()
                    num_batches += 1
            
            avg_loss = total_loss / num_batches if num_batches > 0 else 0.0
            
            # Training metrics
            training_metrics = {
                'average_loss': avg_loss,
                'batches_processed': num_batches,
                'data_points': len(training_batch.training_data),
                'training_time': datetime.now().isoformat()
            }
            
            # Update batch with metrics
            training_batch.training_metrics = training_metrics
            
            return training_metrics
            
        except Exception as e:
            logger.error(f"Error in incremental training: {e}")
            return {'error': str(e)}
    
    async def _compute_training_loss(self, batch: Dict[str, Any], data_type: TrainingDataType) -> torch.Tensor:
        """Compute training loss for batch based on data type."""
        if data_type == TrainingDataType.QUERY_RESPONSE_PAIR:
            return await self._compute_similarity_loss(batch)
        elif data_type == TrainingDataType.SIMILAR_QUERIES:
            return await self._compute_similarity_loss(batch)
        elif data_type == TrainingDataType.MEDICAL_CLASSIFICATION:
            return await self._compute_classification_loss(batch)
        else:
            # Default similarity loss
            return await self._compute_similarity_loss(batch)
    
    async def _compute_similarity_loss(self, batch: Dict[str, Any]) -> torch.Tensor:
        """Compute similarity loss for query-response pairs."""
        query_texts = batch['query_text']
        target_texts = batch['target_text']
        
        # Get embeddings
        query_embeddings = self.model(query_texts)
        target_embeddings = self.model(target_texts)
        
        # Cosine similarity loss
        similarity_scores = torch.cosine_similarity(query_embeddings, target_embeddings)
        
        # We want high similarity, so loss is (1 - similarity)
        loss = torch.mean(1 - similarity_scores)
        
        return loss
    
    async def _compute_classification_loss(self, batch: Dict[str, Any]) -> torch.Tensor:
        """Compute classification loss for medical classification data."""
        query_texts = batch['query_text']
        classifications = batch['classification']
        
        # Get embeddings
        embeddings = self.model(query_texts)
        
        # Get classification predictions
        predictions = self.model.classify_lpp(embeddings)
        
        # Convert string classifications to integers
        class_mapping = {'grade_0': 0, 'grade_1': 1, 'grade_2': 2, 'grade_3': 3, 
                        'grade_4': 4, 'unstageable': 5, 'dti': 6}
        
        targets = torch.tensor([class_mapping.get(cls, 0) for cls in classifications], 
                             dtype=torch.long, device=self.device)
        
        # Cross-entropy loss
        criterion = nn.CrossEntropyLoss()
        loss = criterion(predictions, targets)
        
        return loss
    
    async def _evaluate_model_improvement(self, training_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Evaluate if the model has improved after training."""
        try:
            # Create evaluation dataset
            eval_data = await self._create_evaluation_dataset()
            
            if not eval_data:
                return {'improved': False, 'reason': 'No evaluation data available'}
            
            # Evaluate current model
            current_metrics = await self._evaluate_model_performance(eval_data)
            
            # Compare with previous metrics
            previous_metrics = self.training_stats['improvement_metrics'][-1] if self.training_stats['improvement_metrics'] else None
            
            if previous_metrics is None:
                # First training session
                return {
                    'improved': True,
                    'reason': 'First training session',
                    'current_metrics': current_metrics,
                    'improvement_score': 1.0
                }
            
            # Calculate improvement
            improvement_score = self._calculate_improvement_score(
                current_metrics, previous_metrics.get('current_metrics', {})
            )
            
            improved = improvement_score > 0.05  # 5% improvement threshold
            
            return {
                'improved': improved,
                'improvement_score': improvement_score,
                'current_metrics': current_metrics,
                'previous_metrics': previous_metrics.get('current_metrics', {}),
                'reason': f"Improvement score: {improvement_score:.3f}"
            }
            
        except Exception as e:
            logger.error(f"Error evaluating model improvement: {e}")
            return {'improved': False, 'error': str(e)}
    
    async def _create_evaluation_dataset(self) -> List[Dict[str, Any]]:
        """Create evaluation dataset from validated data."""
        if len(self.validated_data) < 10:
            return []
        
        # Use a sample of validated data for evaluation
        eval_size = min(20, len(self.validated_data) // 2)
        eval_data = np.random.choice(self.validated_data, eval_size, replace=False)
        
        return [
            {
                'query': data.query_text,
                'target': data.target_text,
                'medical_context': data.medical_context
            }
            for data in eval_data if data.target_text
        ]
    
    async def _evaluate_model_performance(self, eval_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Evaluate model performance on evaluation data."""
        try:
            self.model.eval()
            
            similarities = []
            
            with torch.no_grad():
                for item in eval_data:
                    query_emb = self.model.encode([item['query']])[0]
                    target_emb = self.model.encode([item['target']])[0]
                    
                    similarity = float(cos_sim(
                        torch.tensor(query_emb), 
                        torch.tensor(target_emb)
                    ).item())
                    
                    similarities.append(similarity)
            
            return {
                'mean_similarity': np.mean(similarities),
                'std_similarity': np.std(similarities),
                'min_similarity': np.min(similarities),
                'max_similarity': np.max(similarities),
                'num_evaluations': len(similarities)
            }
            
        except Exception as e:
            logger.error(f"Error evaluating model performance: {e}")
            return {}
    
    def _calculate_improvement_score(self, current_metrics: Dict[str, float], 
                                   previous_metrics: Dict[str, float]) -> float:
        """Calculate improvement score between current and previous metrics."""
        if not current_metrics or not previous_metrics:
            return 0.0
        
        # Compare mean similarity (primary metric)
        current_sim = current_metrics.get('mean_similarity', 0.0)
        previous_sim = previous_metrics.get('mean_similarity', 0.0)
        
        if previous_sim == 0:
            return 1.0 if current_sim > 0 else 0.0
        
        improvement = (current_sim - previous_sim) / previous_sim
        return improvement
    
    async def _update_model_version(self, training_metrics: Dict[str, float], 
                                  improvement_metrics: Dict[str, Any]):
        """Update model version after successful improvement."""
        try:
            # Generate new version
            current_version = self.training_stats['current_model_version']
            major, minor, patch = map(int, current_version.split('.'))
            
            if improvement_metrics['improvement_score'] > 0.2:  # Major improvement
                major += 1
                minor = 0
                patch = 0
            elif improvement_metrics['improvement_score'] > 0.1:  # Minor improvement
                minor += 1
                patch = 0
            else:  # Patch improvement
                patch += 1
            
            new_version = f"{major}.{minor}.{patch}"
            
            # Save current model
            model_path = Path(f"models/medical_embedding_v{new_version}.pt")
            model_path.parent.mkdir(exist_ok=True)
            
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'version': new_version,
                'training_metrics': training_metrics,
                'improvement_metrics': improvement_metrics,
                'timestamp': datetime.now().isoformat()
            }, model_path)
            
            # Update version tracking
            self.model_versions[new_version] = {
                'path': str(model_path),
                'training_metrics': training_metrics,
                'improvement_metrics': improvement_metrics,
                'created_at': datetime.now().isoformat()
            }
            
            self.training_stats['current_model_version'] = new_version
            
            logger.info(f"Updated model to version {new_version}")
            
        except Exception as e:
            logger.error(f"Error updating model version: {e}")
    
    def _initialize_medical_validators(self) -> Dict[str, Any]:
        """Initialize medical data validators."""
        return {
            'medical_keywords': [
                'lpp', 'lesión', 'úlcera', 'wound', 'pressure', 'injury',
                'treatment', 'tratamiento', 'therapy', 'terapia',
                'diagnosis', 'diagnóstico', 'prevention', 'prevención'
            ],
            'quality_thresholds': {
                'min_query_length': 5,
                'max_query_length': 100,
                'min_target_length': 5,
                'max_target_length': 200
            },
            'consistency_thresholds': {
                'min_similarity': 0.1,
                'max_similarity': 0.9
            }
        }
    
    async def _load_existing_training_data(self):
        """Load existing validated training data from storage."""
        try:
            # Load from Redis (recent data)
            keys = self.redis_client.keys("training_data:*")
            
            for key in keys:
                data_json = self.redis_client.get(key)
                if data_json:
                    data_dict = json.loads(data_json)
                    training_data = MedicalTrainingData(**data_dict)
                    
                    if training_data.validation_status == ValidationStatus.VALIDATED:
                        self.validated_data.append(training_data)
            
            logger.info(f"Loaded {len(self.validated_data)} validated training data points")
            
        except Exception as e:
            logger.error(f"Error loading existing training data: {e}")
    
    async def _store_training_data(self, training_data: MedicalTrainingData):
        """Store training data in Redis."""
        try:
            self.redis_client.setex(
                f"training_data:{training_data.data_id}",
                604800,  # 7 days
                json.dumps(training_data.to_dict())
            )
        except Exception as e:
            logger.error(f"Error storing training data: {e}")
    
    def _generate_data_id(self, query_text: str, target_text: Optional[str]) -> str:
        """Generate unique data ID."""
        content = f"{query_text}:{target_text or ''}:{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _generate_batch_id(self, training_data: List[MedicalTrainingData]) -> str:
        """Generate unique batch ID."""
        data_ids = sorted([data.data_id for data in training_data])
        content = f"batch:{'|'.join(data_ids)}:{datetime.now().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    async def get_training_statistics(self) -> Dict[str, Any]:
        """Get training pipeline statistics."""
        return {
            **self.training_stats,
            'buffer_size': len(self.training_data_buffer),
            'validated_data_size': len(self.validated_data),
            'model_versions': list(self.model_versions.keys()),
            'device': str(self.device),
            'min_batch_size': self.min_batch_size,
            'validation_threshold': self.validation_threshold
        }


# Factory function
async def create_training_pipeline(base_model_name: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2') -> IncrementalTrainingPipeline:
    """Create and initialize incremental training pipeline."""
    pipeline = IncrementalTrainingPipeline(base_model_name=base_model_name)
    await pipeline.initialize()
    return pipeline