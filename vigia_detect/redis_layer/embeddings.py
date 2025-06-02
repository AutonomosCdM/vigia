"""Embedding generation service for semantic caching and vector search."""
import logging
from typing import List, Optional, Union
from sentence_transformers import SentenceTransformer
import torch
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings for medical text."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service.
        
        Args:
            model_name: Name of the sentence transformer model to use.
                       For medical domain, consider 'pritamdeka/S-PubMedBert-MS-MARCO'
        """
        self.model_name = model_name
        self.model = None
        self._load_model()
        
    def _load_model(self):
        """Lazy load the embedding model."""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
            
    def generate_embedding(self, text: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for text.
        
        Args:
            text: Single text string or list of texts
            
        Returns:
            Numpy array of embeddings
        """
        if self.model is None:
            self._load_model()
            
        if isinstance(text, str):
            text = [text]
            
        embeddings = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True  # For cosine similarity
        )
        
        return embeddings[0] if len(text) == 1 else embeddings
        
    def generate_medical_embedding(self, text: str, context: Optional[dict] = None) -> np.ndarray:
        """
        Generate embedding with medical context enhancement.
        
        Args:
            text: Medical text to embed
            context: Optional medical context (patient_id, lpp_grade, location)
            
        Returns:
            Enhanced embedding vector
        """
        # Enhance text with medical context if provided
        if context:
            enhanced_text = self._enhance_with_context(text, context)
        else:
            enhanced_text = text
            
        return self.generate_embedding(enhanced_text)
        
    def _enhance_with_context(self, text: str, context: dict) -> str:
        """Enhance text with medical context for better semantic matching."""
        context_parts = []
        
        if "lpp_grade" in context:
            context_parts.append(f"LPP Grade {context['lpp_grade']}")
        if "location" in context:
            context_parts.append(f"Location: {context['location']}")
        if "patient_type" in context:
            context_parts.append(f"Patient: {context['patient_type']}")
            
        if context_parts:
            return f"{' '.join(context_parts)}. {text}"
        return text
        
    def batch_generate(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            batch_size: Size of batches for processing
            
        Returns:
            Array of embeddings
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self.generate_embedding(batch)
            all_embeddings.extend(embeddings)
            
        return np.array(all_embeddings)
        
    @property
    def embedding_dim(self) -> int:
        """Get the dimension of embeddings produced by the model."""
        if self.model is None:
            self._load_model()
        return self.model.get_sentence_embedding_dimension()


class MedicalEmbeddingService(EmbeddingService):
    """Specialized embedding service for medical domain."""
    
    def __init__(self):
        # Use medical-specific model if available
        super().__init__(model_name="all-MiniLM-L6-v2")  # Can be replaced with medical model
        
    def preprocess_medical_text(self, text: str) -> str:
        """Preprocess medical text for better embedding quality."""
        # Standardize medical abbreviations
        replacements = {
            "LPP": "lesión por presión",
            "UPP": "úlcera por presión",
            "EPUAP": "European Pressure Ulcer Advisory Panel",
            "NPUAP": "National Pressure Ulcer Advisory Panel",
        }
        
        processed = text
        for abbr, full in replacements.items():
            processed = processed.replace(abbr, full)
            
        return processed
        
    def generate_medical_embedding(self, text: str, context: Optional[dict] = None) -> np.ndarray:
        """Generate embedding with medical preprocessing."""
        processed_text = self.preprocess_medical_text(text)
        return super().generate_medical_embedding(processed_text, context)