"""
Multimodal Medical Embeddings Service with MedCLIP Integration
============================================================

Advanced multimodal RAG component that processes both medical images and text
using MedCLIP for unified vector representations in medical context.
"""

import torch
import torch.nn as nn
from typing import Dict, List, Any, Optional, Tuple, Union
import numpy as np
from PIL import Image
import cv2
from pathlib import Path
import json
import logging
from datetime import datetime
import hashlib
import pickle

from transformers import AutoModel, AutoProcessor, AutoTokenizer
from sentence_transformers import SentenceTransformer
import faiss
import redis

logger = logging.getLogger(__name__)


class MedCLIPMultimodalService:
    """
    Multimodal medical embedding service using MedCLIP for image-text representation.
    Enables unified search across medical images and clinical text.
    """
    
    def __init__(self, model_name: str = "microsoft/medclip-vit", cache_ttl: int = 3600):
        """
        Initialize MedCLIP multimodal service.
        
        Args:
            model_name: MedCLIP model identifier
            cache_ttl: Cache time-to-live in seconds
        """
        self.model_name = model_name
        self.cache_ttl = cache_ttl
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Initialize models
        self.medclip_model = None
        self.medclip_processor = None
        self.text_encoder = None
        self.image_encoder = None
        
        # Vector storage
        self.multimodal_index = None
        self.embedding_dimension = 768  # MedCLIP default
        
        # Cache setup
        self.redis_client = redis.Redis(host='localhost', port=6379, db=3)
        self.embedding_cache = {}
        
        # Medical preprocessing
        self.medical_concepts = self._load_medical_concepts()
        
        logger.info(f"Initialized MedCLIP service on {self.device}")
    
    async def initialize(self):
        """Initialize MedCLIP models and vector index."""
        try:
            # Load MedCLIP model and processor
            self.medclip_model = AutoModel.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32
            ).to(self.device)
            
            self.medclip_processor = AutoProcessor.from_pretrained(self.model_name)
            
            # Separate encoders for flexibility
            self.text_encoder = self.medclip_model.text_model
            self.image_encoder = self.medclip_model.vision_model
            
            # Initialize FAISS index for multimodal search
            self.multimodal_index = faiss.IndexFlatIP(self.embedding_dimension)
            
            logger.info("MedCLIP models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing MedCLIP: {e}")
            # Fallback to standard models
            await self._initialize_fallback_models()
    
    async def _initialize_fallback_models(self):
        """Initialize fallback models if MedCLIP unavailable."""
        logger.warning("Using fallback models - limited multimodal capabilities")
        
        # Use standard sentence transformer for text
        self.text_fallback = SentenceTransformer(
            'paraphrase-multilingual-MiniLM-L12-v2'
        )
        
        # Use ResNet for basic image features
        from torchvision import models, transforms
        self.image_fallback = models.resnet50(pretrained=True)
        self.image_fallback.eval()
        
        self.image_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
    
    def encode_medical_text(self, text: str, 
                           medical_context: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """
        Encode medical text with clinical context enhancement.
        
        Args:
            text: Medical text to encode
            medical_context: Additional medical context (LPP grade, location, etc.)
            
        Returns:
            Vector embedding for the medical text
        """
        try:
            # Enhance text with medical context
            enhanced_text = self._enhance_medical_text(text, medical_context)
            
            # Check cache
            cache_key = self._get_cache_key("text", enhanced_text)
            cached_embedding = self._get_cached_embedding(cache_key)
            if cached_embedding is not None:
                return cached_embedding
            
            # Generate embedding
            if self.medclip_model is not None:
                # Use MedCLIP text encoder
                inputs = self.medclip_processor(
                    text=[enhanced_text], 
                    return_tensors="pt"
                ).to(self.device)
                
                with torch.no_grad():
                    text_features = self.text_encoder(**inputs).last_hidden_state
                    # Pool features (mean pooling)
                    embedding = text_features.mean(dim=1).cpu().numpy().flatten()
            else:
                # Fallback to sentence transformer
                embedding = self.text_fallback.encode(enhanced_text)
            
            # Normalize embedding
            embedding = embedding / np.linalg.norm(embedding)
            
            # Cache result
            self._cache_embedding(cache_key, embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error encoding medical text: {e}")
            # Return zero vector as fallback
            return np.zeros(self.embedding_dimension)
    
    def encode_medical_image(self, image_path: str,
                           medical_context: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """
        Encode medical image with clinical context.
        
        Args:
            image_path: Path to medical image
            medical_context: Medical context (anatomical location, suspected condition)
            
        Returns:
            Vector embedding for the medical image
        """
        try:
            # Load and preprocess image
            image = self._load_and_preprocess_image(image_path)
            if image is None:
                return np.zeros(self.embedding_dimension)
            
            # Check cache
            cache_key = self._get_cache_key("image", image_path, medical_context)
            cached_embedding = self._get_cached_embedding(cache_key)
            if cached_embedding is not None:
                return cached_embedding
            
            # Generate embedding
            if self.medclip_model is not None:
                # Use MedCLIP image encoder
                inputs = self.medclip_processor(
                    images=image, 
                    return_tensors="pt"
                ).to(self.device)
                
                with torch.no_grad():
                    image_features = self.image_encoder(**inputs).last_hidden_state
                    # Pool features (mean pooling)
                    embedding = image_features.mean(dim=1).cpu().numpy().flatten()
            else:
                # Fallback to ResNet features
                image_tensor = self.image_transform(image).unsqueeze(0)
                with torch.no_grad():
                    features = self.image_fallback(image_tensor)
                    embedding = features.cpu().numpy().flatten()
                    # Pad or truncate to match expected dimension
                    if len(embedding) != self.embedding_dimension:
                        embedding = np.resize(embedding, self.embedding_dimension)
            
            # Normalize embedding
            embedding = embedding / np.linalg.norm(embedding)
            
            # Cache result
            self._cache_embedding(cache_key, embedding)
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error encoding medical image: {e}")
            return np.zeros(self.embedding_dimension)
    
    def encode_multimodal_query(self, text: str, image_path: Optional[str] = None,
                              medical_context: Optional[Dict[str, Any]] = None) -> np.ndarray:
        """
        Encode multimodal medical query combining text and image.
        
        Args:
            text: Medical text query
            image_path: Optional medical image
            medical_context: Medical context information
            
        Returns:
            Combined multimodal embedding
        """
        try:
            # Encode text component
            text_embedding = self.encode_medical_text(text, medical_context)
            
            if image_path is not None:
                # Encode image component
                image_embedding = self.encode_medical_image(image_path, medical_context)
                
                # Combine embeddings (weighted average)
                combined_embedding = 0.6 * text_embedding + 0.4 * image_embedding
            else:
                combined_embedding = text_embedding
            
            # Normalize combined embedding
            combined_embedding = combined_embedding / np.linalg.norm(combined_embedding)
            
            return combined_embedding
            
        except Exception as e:
            logger.error(f"Error encoding multimodal query: {e}")
            return np.zeros(self.embedding_dimension)
    
    async def search_multimodal_knowledge(self, query_text: str, 
                                        query_image: Optional[str] = None,
                                        medical_context: Optional[Dict[str, Any]] = None,
                                        top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search multimodal medical knowledge base.
        
        Args:
            query_text: Medical text query
            query_image: Optional medical image path
            medical_context: Medical context
            top_k: Number of results to return
            
        Returns:
            List of relevant medical documents with scores
        """
        try:
            # Generate multimodal query embedding
            query_embedding = self.encode_multimodal_query(
                query_text, query_image, medical_context
            )
            
            # Search in multimodal index
            if self.multimodal_index.ntotal > 0:
                query_vector = query_embedding.reshape(1, -1).astype(np.float32)
                scores, indices = self.multimodal_index.search(query_vector, top_k)
                
                # Retrieve documents
                results = []
                for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                    if idx != -1:  # Valid result
                        doc_info = self._get_document_by_index(idx)
                        if doc_info:
                            results.append({
                                'document': doc_info,
                                'similarity_score': float(score),
                                'rank': i + 1,
                                'query_type': 'multimodal'
                            })
                
                return results
            else:
                logger.warning("Multimodal index is empty")
                return []
                
        except Exception as e:
            logger.error(f"Error in multimodal search: {e}")
            return []
    
    def add_multimodal_document(self, doc_text: str, 
                              doc_image: Optional[str] = None,
                              metadata: Optional[Dict[str, Any]] = None) -> int:
        """
        Add multimodal document to the knowledge base.
        
        Args:
            doc_text: Document text content
            doc_image: Optional document image
            metadata: Document metadata
            
        Returns:
            Document index in the vector store
        """
        try:
            # Generate multimodal embedding
            doc_embedding = self.encode_multimodal_query(
                doc_text, doc_image, metadata
            )
            
            # Add to FAISS index
            doc_vector = doc_embedding.reshape(1, -1).astype(np.float32)
            self.multimodal_index.add(doc_vector)
            
            # Store document metadata
            doc_index = self.multimodal_index.ntotal - 1
            self._store_document_metadata(doc_index, {
                'text': doc_text,
                'image_path': doc_image,
                'metadata': metadata or {},
                'timestamp': datetime.now().isoformat(),
                'embedding_dimension': self.embedding_dimension
            })
            
            logger.info(f"Added multimodal document at index {doc_index}")
            return doc_index
            
        except Exception as e:
            logger.error(f"Error adding multimodal document: {e}")
            return -1
    
    def _enhance_medical_text(self, text: str, 
                            medical_context: Optional[Dict[str, Any]] = None) -> str:
        """Enhance text with medical context."""
        enhanced = text
        
        if medical_context:
            # Add LPP grade context
            if 'lpp_grade' in medical_context:
                grade = medical_context['lpp_grade']
                enhanced = f"LPP Grado {grade}: {enhanced}"
            
            # Add anatomical location
            if 'anatomical_location' in medical_context:
                location = medical_context['anatomical_location']
                enhanced = f"Localización {location}: {enhanced}"
            
            # Add patient context
            if 'patient_age' in medical_context:
                age = medical_context['patient_age']
                if age > 65:
                    enhanced = f"Paciente geriátrico: {enhanced}"
        
        # Add medical concept expansion
        for concept, synonyms in self.medical_concepts.items():
            if concept.lower() in enhanced.lower():
                enhanced += f" ({', '.join(synonyms)})"
        
        return enhanced
    
    def _load_and_preprocess_image(self, image_path: str) -> Optional[Image.Image]:
        """Load and preprocess medical image."""
        try:
            if not Path(image_path).exists():
                logger.warning(f"Image not found: {image_path}")
                return None
            
            # Load image
            image = Image.open(image_path).convert('RGB')
            
            # Basic medical image preprocessing
            # Resize to standard size
            image = image.resize((224, 224), Image.Resampling.LANCZOS)
            
            # Enhance contrast for medical images
            import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.2)
            
            return image
            
        except Exception as e:
            logger.error(f"Error loading image {image_path}: {e}")
            return None
    
    def _load_medical_concepts(self) -> Dict[str, List[str]]:
        """Load medical concept synonyms."""
        return {
            'lpp': ['lesión por presión', 'úlcera por presión', 'escara'],
            'wound': ['herida', 'lesión', 'úlcera'],
            'healing': ['cicatrización', 'curación', 'reparación'],
            'infection': ['infección', 'contaminación', 'sepsis'],
            'pain': ['dolor', 'molestia', 'discomfort'],
            'nutrition': ['nutrición', 'alimentación', 'malnutrición']
        }
    
    def _get_cache_key(self, content_type: str, content: str, 
                      context: Optional[Dict[str, Any]] = None) -> str:
        """Generate cache key for embeddings."""
        key_data = f"{content_type}:{content}"
        if context:
            key_data += f":{json.dumps(context, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def _get_cached_embedding(self, cache_key: str) -> Optional[np.ndarray]:
        """Retrieve cached embedding."""
        try:
            cached_data = self.redis_client.get(f"medclip_embed:{cache_key}")
            if cached_data:
                return pickle.loads(cached_data)
        except Exception as e:
            logger.debug(f"Cache miss for key {cache_key}: {e}")
        return None
    
    def _cache_embedding(self, cache_key: str, embedding: np.ndarray):
        """Cache embedding with TTL."""
        try:
            serialized = pickle.dumps(embedding)
            self.redis_client.setex(
                f"medclip_embed:{cache_key}", 
                self.cache_ttl, 
                serialized
            )
        except Exception as e:
            logger.debug(f"Failed to cache embedding: {e}")
    
    def _store_document_metadata(self, doc_index: int, metadata: Dict[str, Any]):
        """Store document metadata in Redis."""
        try:
            self.redis_client.setex(
                f"medclip_doc:{doc_index}",
                86400,  # 24 hours
                json.dumps(metadata)
            )
        except Exception as e:
            logger.error(f"Error storing document metadata: {e}")
    
    def _get_document_by_index(self, doc_index: int) -> Optional[Dict[str, Any]]:
        """Retrieve document by index."""
        try:
            doc_data = self.redis_client.get(f"medclip_doc:{doc_index}")
            if doc_data:
                return json.loads(doc_data)
        except Exception as e:
            logger.error(f"Error retrieving document {doc_index}: {e}")
        return None
    
    async def get_multimodal_stats(self) -> Dict[str, Any]:
        """Get multimodal service statistics."""
        return {
            'total_documents': self.multimodal_index.ntotal if self.multimodal_index else 0,
            'embedding_dimension': self.embedding_dimension,
            'cache_size': len(self.embedding_cache),
            'model_name': self.model_name,
            'device': str(self.device),
            'medclip_available': self.medclip_model is not None
        }


# Factory function for easy instantiation
async def create_medclip_service(model_name: str = "microsoft/medclip-vit") -> MedCLIPMultimodalService:
    """
    Create and initialize MedCLIP multimodal service.
    
    Args:
        model_name: MedCLIP model to use
        
    Returns:
        Initialized multimodal service
    """
    service = MedCLIPMultimodalService(model_name=model_name)
    await service.initialize()
    return service


# Integration with existing RAG system
class MultimodalRAGEnhancer:
    """
    Enhanced RAG system with multimodal capabilities.
    Integrates MedCLIP with existing medical knowledge retrieval.
    """
    
    def __init__(self, medclip_service: MedCLIPMultimodalService):
        self.medclip_service = medclip_service
        
    async def enhance_clinical_decision_multimodal(self, 
                                                 lpp_grade: int,
                                                 query_text: str,
                                                 image_path: Optional[str] = None,
                                                 patient_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Enhance clinical decision with multimodal knowledge retrieval.
        
        Args:
            lpp_grade: LPP grade detected
            query_text: Clinical query text
            image_path: Optional medical image
            patient_context: Patient medical context
            
        Returns:
            Enhanced clinical decision with multimodal evidence
        """
        try:
            # Search multimodal knowledge base
            multimodal_results = await self.medclip_service.search_multimodal_knowledge(
                query_text=query_text,
                query_image=image_path,
                medical_context={'lpp_grade': lpp_grade, **patient_context},
                top_k=5
            )
            
            # Extract evidence from multimodal results
            evidence_sources = []
            clinical_recommendations = []
            
            for result in multimodal_results:
                doc = result['document']
                score = result['similarity_score']
                
                if score > 0.7:  # High confidence threshold
                    evidence_sources.append({
                        'source': 'multimodal_knowledge_base',
                        'content': doc.get('text', ''),
                        'confidence': score,
                        'has_image': doc.get('image_path') is not None,
                        'metadata': doc.get('metadata', {})
                    })
                    
                    # Extract recommendations
                    if 'treatment' in doc.get('text', '').lower():
                        clinical_recommendations.append(doc['text'])
            
            return {
                'multimodal_evidence': evidence_sources,
                'enhanced_recommendations': clinical_recommendations,
                'retrieval_confidence': len(evidence_sources) / 5.0,  # Normalized
                'search_type': 'image_text' if image_path else 'text_only',
                'total_results': len(multimodal_results)
            }
            
        except Exception as e:
            logger.error(f"Error in multimodal clinical enhancement: {e}")
            return {'error': str(e)}