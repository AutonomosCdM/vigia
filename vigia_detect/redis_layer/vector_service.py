"""
Enhanced Vector Service - Servicio vectorial con embeddings médicos reales
Implementación completa de búsqueda vectorial para el sistema de conocimiento médico.

Características:
- Embeddings médicos especializados
- Búsqueda semántica con HNSW
- Indexación automática de protocolos
- Cache inteligente de resultados
- Soporte para múltiples idiomas
"""

import asyncio
import json
import hashlib
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# Redis imports
import redis.asyncio as redis
from redis.exceptions import RedisError

# Vector processing
from sentence_transformers import SentenceTransformer
import faiss

from ..utils.secure_logger import SecureLogger
from ..utils.error_handling import handle_exceptions

logger = SecureLogger("vector_service_enhanced")


class EmbeddingModel(Enum):
    """Modelos de embeddings disponibles."""
    BIOBERT = "dmis-lab/biobert-v1.1"
    CLINICAL_BERT = "emilyalsentzer/Bio_ClinicalBERT" 
    MULTILINGUAL_MEDICAL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    SPANISH_MEDICAL = "PlanTL-GOB-ES/roberta-base-biomedical-clinical-es"


@dataclass
class VectorSearchConfig:
    """Configuración para búsqueda vectorial."""
    model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    dimension: int = 384
    index_type: str = "HNSW"
    distance_metric: str = "cosine"
    cache_ttl: int = 3600  # 1 hora
    max_results: int = 20
    similarity_threshold: float = 0.7


@dataclass
class VectorDocument:
    """Documento vectorizado."""
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    vector: Optional[np.ndarray]
    language: str = "es"
    document_type: str = "medical_protocol"
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


@dataclass
class VectorSearchResult:
    """Resultado de búsqueda vectorial."""
    doc_id: str
    content: str
    metadata: Dict[str, Any]
    similarity_score: float
    document_type: str
    language: str


class EnhancedVectorService:
    """Servicio vectorial enhanced con embeddings médicos reales."""
    
    def __init__(self, config: Optional[VectorSearchConfig] = None):
        """
        Inicializar servicio vectorial enhanced.
        
        Args:
            config: Configuración del servicio vectorial
        """
        self.config = config or VectorSearchConfig()
        self.redis_client: Optional[redis.Redis] = None
        self.embedding_model: Optional[SentenceTransformer] = None
        self.vector_index: Optional[faiss.IndexHNSWFlat] = None
        self.document_store: Dict[str, VectorDocument] = {}
        self.index_to_doc_id: Dict[int, str] = {}
        self.next_index_id = 0
        
        # Cache para embeddings
        self.embedding_cache: Dict[str, np.ndarray] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "total_queries": 0
        }
        
        logger.audit("enhanced_vector_service_initialized", {
            "model": self.config.model_name,
            "dimension": self.config.dimension,
            "index_type": self.config.index_type
        })
    
    async def initialize(self):
        """Inicializar servicios y modelos."""
        try:
            # Inicializar Redis
            await self._initialize_redis()
            
            # Cargar modelo de embeddings
            await self._load_embedding_model()
            
            # Inicializar índice vectorial
            await self._initialize_vector_index()
            
            # Cargar documentos existentes
            await self._load_existing_documents()
            
            logger.info("Enhanced vector service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize enhanced vector service: {e}")
            raise
    
    async def _initialize_redis(self):
        """Inicializar conexión a Redis."""
        try:
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                decode_responses=False,  # Para manejar datos binarios
                socket_timeout=5.0,
                socket_connect_timeout=5.0,
                retry_on_timeout=True
            )
            
            # Probar conexión
            await self.redis_client.ping()
            logger.info("Redis connection established")
            
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None
    
    async def _load_embedding_model(self):
        """Cargar modelo de embeddings médicos."""
        try:
            logger.info(f"Loading embedding model: {self.config.model_name}")
            
            # Cargar modelo en un hilo separado para no bloquear
            loop = asyncio.get_event_loop()
            self.embedding_model = await loop.run_in_executor(
                None, 
                SentenceTransformer, 
                self.config.model_name
            )
            
            # Verificar dimensión
            test_embedding = self.embedding_model.encode("test")
            actual_dim = len(test_embedding)
            
            if actual_dim != self.config.dimension:
                logger.warning(f"Model dimension {actual_dim} differs from config {self.config.dimension}")
                self.config.dimension = actual_dim
            
            logger.info(f"Embedding model loaded successfully (dim: {self.config.dimension})")
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    async def _initialize_vector_index(self):
        """Inicializar índice vectorial FAISS."""
        try:
            if self.config.index_type == "HNSW":
                # HNSW index para búsqueda rápida y precisa
                self.vector_index = faiss.IndexHNSWFlat(
                    self.config.dimension,
                    32  # M parameter for HNSW
                )
                self.vector_index.hnsw.efConstruction = 200
                self.vector_index.hnsw.efSearch = 100
                
            else:
                # Flat index como fallback
                self.vector_index = faiss.IndexFlatL2(self.config.dimension)
            
            logger.info(f"Vector index initialized: {self.config.index_type}")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector index: {e}")
            raise
    
    async def _load_existing_documents(self):
        """Cargar documentos existentes desde Redis."""
        if not self.redis_client:
            logger.warning("Redis not available, skipping document loading")
            return
        
        try:
            # Buscar claves de documentos
            doc_keys = await self.redis_client.keys("vec_doc:*")
            
            loaded_count = 0
            for key in doc_keys:
                try:
                    doc_data = await self.redis_client.hgetall(key)
                    if doc_data:
                        # Deserializar documento
                        doc = self._deserialize_document(doc_data)
                        if doc and doc.vector is not None:
                            # Agregar al índice
                            self._add_to_index(doc)
                            loaded_count += 1
                
                except Exception as e:
                    logger.warning(f"Failed to load document {key}: {e}")
                    continue
            
            logger.info(f"Loaded {loaded_count} existing documents")
            
        except Exception as e:
            logger.error(f"Failed to load existing documents: {e}")
    
    @handle_exceptions(logger)
    async def index_document(self, 
                           content: str,
                           metadata: Dict[str, Any],
                           doc_id: Optional[str] = None,
                           document_type: str = "medical_protocol",
                           language: str = "es") -> str:
        """
        Indexar documento para búsqueda vectorial.
        
        Args:
            content: Contenido del documento
            metadata: Metadatos del documento
            doc_id: ID del documento (opcional)
            document_type: Tipo de documento
            language: Idioma del documento
            
        Returns:
            ID del documento indexado
        """
        try:
            # Generar ID si no se proporciona
            if not doc_id:
                doc_id = hashlib.sha256(
                    f"{content[:100]}_{datetime.now().isoformat()}".encode()
                ).hexdigest()[:16]
            
            # Generar embedding
            embedding = await self._generate_embedding(content)
            
            # Crear documento
            doc = VectorDocument(
                doc_id=doc_id,
                content=content,
                metadata=metadata,
                vector=embedding,
                language=language,
                document_type=document_type
            )
            
            # Agregar al índice
            self._add_to_index(doc)
            
            # Persistir en Redis
            await self._persist_document(doc)
            
            logger.audit("document_indexed", {
                "doc_id": doc_id,
                "document_type": document_type,
                "language": language,
                "content_length": len(content)
            })
            
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to index document: {e}")
            raise
    
    @handle_exceptions(logger)
    async def search_similar(self,
                           query: str,
                           k: int = 5,
                           filter_by_type: Optional[str] = None,
                           filter_by_language: Optional[str] = None,
                           similarity_threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Buscar documentos similares.
        
        Args:
            query: Consulta de búsqueda
            k: Número de resultados
            filter_by_type: Filtrar por tipo de documento
            filter_by_language: Filtrar por idioma
            similarity_threshold: Umbral mínimo de similitud
            
        Returns:
            Lista de documentos similares
        """
        try:
            self.cache_stats["total_queries"] += 1
            
            # Verificar cache
            cache_key = self._get_cache_key(query, k, filter_by_type, filter_by_language)
            cached_result = await self._get_cached_result(cache_key)
            
            if cached_result:
                self.cache_stats["hits"] += 1
                return cached_result
            
            self.cache_stats["misses"] += 1
            
            # Generar embedding de la consulta
            query_embedding = await self._generate_embedding(query)
            
            # Realizar búsqueda vectorial
            raw_results = await self._vector_search(query_embedding, k * 2)  # Buscar más para filtrar
            
            # Aplicar filtros
            filtered_results = self._apply_filters(
                raw_results,
                filter_by_type,
                filter_by_language,
                similarity_threshold or self.config.similarity_threshold
            )
            
            # Limitar resultados
            final_results = filtered_results[:k]
            
            # Serializar para cache
            serialized_results = [self._serialize_search_result(r) for r in final_results]
            
            # Guardar en cache
            await self._cache_result(cache_key, serialized_results)
            
            logger.audit("vector_search_completed", {
                "query_length": len(query),
                "results_found": len(final_results),
                "cache_hit": False,
                "filters_applied": {
                    "type": filter_by_type,
                    "language": filter_by_language
                }
            })
            
            return serialized_results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    async def _generate_embedding(self, text: str) -> np.ndarray:
        """Generar embedding para texto."""
        # Verificar cache de embeddings
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        if text_hash in self.embedding_cache:
            return self.embedding_cache[text_hash]
        
        if not self.embedding_model:
            raise RuntimeError("Embedding model not initialized")
        
        try:
            # Preprocesar texto para contexto médico
            processed_text = self._preprocess_medical_text(text)
            
            # Generar embedding en hilo separado
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                self.embedding_model.encode,
                processed_text
            )
            
            # Convertir a numpy array si no lo es
            embedding = np.array(embedding, dtype=np.float32)
            
            # Guardar en cache (mantener solo los últimos 1000)
            if len(self.embedding_cache) >= 1000:
                # Remover el más antiguo (implementación simple)
                oldest_key = next(iter(self.embedding_cache))
                del self.embedding_cache[oldest_key]
            
            self.embedding_cache[text_hash] = embedding
            
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    def _preprocess_medical_text(self, text: str) -> str:
        """Preprocesar texto para contexto médico."""
        # Agregar contexto médico implícito
        medical_context = "Contexto médico: "
        
        # Identificar términos médicos comunes
        medical_terms = [
            "lpp", "lesión por presión", "pressure injury",
            "herida", "wound", "cicatrización", "healing",
            "infección", "infection", "antibiótico", "antibiotic",
            "dolor", "pain", "analgesia", "tratamiento", "treatment"
        ]
        
        text_lower = text.lower()
        found_terms = [term for term in medical_terms if term in text_lower]
        
        if found_terms:
            medical_context += f"Términos relevantes: {', '.join(found_terms[:3])}. "
        
        return medical_context + text
    
    def _add_to_index(self, doc: VectorDocument):
        """Agregar documento al índice vectorial."""
        if not self.vector_index or doc.vector is None:
            return
        
        try:
            # Agregar vector al índice FAISS
            vector = doc.vector.reshape(1, -1)
            self.vector_index.add(vector)
            
            # Mantener mapeo de índice a doc_id
            self.index_to_doc_id[self.next_index_id] = doc.doc_id
            self.next_index_id += 1
            
            # Guardar documento
            self.document_store[doc.doc_id] = doc
            
        except Exception as e:
            logger.error(f"Failed to add document to index: {e}")
            raise
    
    async def _vector_search(self, query_vector: np.ndarray, k: int) -> List[VectorSearchResult]:
        """Realizar búsqueda vectorial en el índice."""
        if not self.vector_index or self.vector_index.ntotal == 0:
            return []
        
        try:
            # Buscar vectores similares
            query_vector = query_vector.reshape(1, -1)
            distances, indices = self.vector_index.search(query_vector, min(k, self.vector_index.ntotal))
            
            results = []
            for distance, index in zip(distances[0], indices[0]):
                if index == -1:  # No encontrado
                    continue
                
                # Obtener documento
                doc_id = self.index_to_doc_id.get(index)
                if not doc_id or doc_id not in self.document_store:
                    continue
                
                doc = self.document_store[doc_id]
                
                # Convertir distancia a similitud (cosine similarity)
                similarity = 1.0 / (1.0 + distance) if distance > 0 else 1.0
                
                result = VectorSearchResult(
                    doc_id=doc.doc_id,
                    content=doc.content,
                    metadata=doc.metadata,
                    similarity_score=similarity,
                    document_type=doc.document_type,
                    language=doc.language
                )
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Vector search execution failed: {e}")
            return []
    
    def _apply_filters(self,
                      results: List[VectorSearchResult],
                      filter_type: Optional[str],
                      filter_language: Optional[str],
                      similarity_threshold: float) -> List[VectorSearchResult]:
        """Aplicar filtros a los resultados."""
        filtered = []
        
        for result in results:
            # Filtro de similitud
            if result.similarity_score < similarity_threshold:
                continue
            
            # Filtro de tipo
            if filter_type and result.document_type != filter_type:
                continue
            
            # Filtro de idioma
            if filter_language and result.language != filter_language:
                continue
            
            filtered.append(result)
        
        return filtered
    
    async def _persist_document(self, doc: VectorDocument):
        """Persistir documento en Redis."""
        if not self.redis_client:
            return
        
        try:
            # Serializar documento
            doc_data = self._serialize_document(doc)
            
            # Guardar en Redis
            key = f"vec_doc:{doc.doc_id}"
            await self.redis_client.hset(key, mapping=doc_data)
            
            # Establecer TTL si se configura
            if hasattr(self.config, 'document_ttl') and self.config.document_ttl:
                await self.redis_client.expire(key, self.config.document_ttl)
            
        except Exception as e:
            logger.warning(f"Failed to persist document {doc.doc_id}: {e}")
    
    def _serialize_document(self, doc: VectorDocument) -> Dict[str, bytes]:
        """Serializar documento para almacenamiento."""
        return {
            "doc_id": doc.doc_id.encode(),
            "content": doc.content.encode(),
            "metadata": json.dumps(doc.metadata).encode(),
            "vector": doc.vector.tobytes() if doc.vector is not None else b"",
            "language": doc.language.encode(),
            "document_type": doc.document_type.encode(),
            "created_at": doc.created_at.isoformat().encode()
        }
    
    def _deserialize_document(self, doc_data: Dict[bytes, bytes]) -> Optional[VectorDocument]:
        """Deserializar documento desde almacenamiento."""
        try:
            # Decodificar campos
            doc_id = doc_data[b"doc_id"].decode()
            content = doc_data[b"content"].decode()
            metadata = json.loads(doc_data[b"metadata"].decode())
            language = doc_data[b"language"].decode()
            document_type = doc_data[b"document_type"].decode()
            created_at = datetime.fromisoformat(doc_data[b"created_at"].decode())
            
            # Deserializar vector
            vector = None
            if doc_data[b"vector"]:
                vector = np.frombuffer(doc_data[b"vector"], dtype=np.float32)
                if len(vector) == self.config.dimension:
                    vector = vector.reshape(1, -1)
                else:
                    logger.warning(f"Vector dimension mismatch for doc {doc_id}")
                    vector = None
            
            return VectorDocument(
                doc_id=doc_id,
                content=content,
                metadata=metadata,
                vector=vector,
                language=language,
                document_type=document_type,
                created_at=created_at
            )
            
        except Exception as e:
            logger.error(f"Failed to deserialize document: {e}")
            return None
    
    def _get_cache_key(self, query: str, k: int, filter_type: Optional[str], filter_language: Optional[str]) -> str:
        """Generar clave de cache para consulta."""
        cache_data = f"{query}|{k}|{filter_type or ''}|{filter_language or ''}"
        return f"vec_cache:{hashlib.sha256(cache_data.encode()).hexdigest()[:16]}"
    
    async def _get_cached_result(self, cache_key: str) -> Optional[List[Dict[str, Any]]]:
        """Obtener resultado desde cache."""
        if not self.redis_client:
            return None
        
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
        
        return None
    
    async def _cache_result(self, cache_key: str, results: List[Dict[str, Any]]):
        """Guardar resultado en cache."""
        if not self.redis_client:
            return
        
        try:
            cached_data = json.dumps(results)
            await self.redis_client.setex(cache_key, self.config.cache_ttl, cached_data)
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
    
    def _serialize_search_result(self, result: VectorSearchResult) -> Dict[str, Any]:
        """Serializar resultado de búsqueda."""
        return {
            "doc_id": result.doc_id,
            "content": result.content,
            "metadata": result.metadata,
            "similarity_score": result.similarity_score,
            "document_type": result.document_type,
            "language": result.language,
            "confidence": result.similarity_score,  # Alias para compatibilidad
            "sources": ["vector_search"],
            "references": result.metadata.get("references", [])
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del servicio."""
        return {
            "indexed_documents": len(self.document_store),
            "vector_index_size": self.vector_index.ntotal if self.vector_index else 0,
            "embedding_cache_size": len(self.embedding_cache),
            "cache_stats": self.cache_stats.copy(),
            "model_info": {
                "name": self.config.model_name,
                "dimension": self.config.dimension
            },
            "redis_available": self.redis_client is not None
        }
    
    async def index_medical_protocols(self):
        """Indexar protocolos médicos básicos."""
        """Index basic medical protocols for testing and demonstration."""
        protocols = [
            {
                "content": "Protocolo de prevención de lesiones por presión: Evaluación de riesgo con escala Braden cada 24 horas, cambios posturales cada 2 horas, uso de superficies de redistribución de presión.",
                "metadata": {
                    "title": "Prevención de LPP",
                    "type": "prevention_protocol",
                    "evidence_level": "high",
                    "references": ["NPUAP Guidelines 2019"]
                },
                "document_type": "medical_protocol"
            },
            {
                "content": "Tratamiento de LPP grado 3: Desbridamiento quirúrgico si necesario, limpieza con suero fisiológico, apósitos de espuma o alginato según exudado, consideración de terapia de presión negativa.",
                "metadata": {
                    "title": "Tratamiento LPP Grado 3",
                    "type": "treatment_protocol",
                    "evidence_level": "high",
                    "references": ["Cochrane Reviews 2023"]
                },
                "document_type": "medical_protocol"
            },
            {
                "content": "Manejo del dolor en lesiones por presión: Analgesia previa a curaciones con lidocaína tópica, uso de técnicas de distracción, evaluación regular con escala EVA.",
                "metadata": {
                    "title": "Manejo del Dolor en LPP",
                    "type": "pain_management",
                    "evidence_level": "moderate",
                    "references": ["Pain Management Guidelines 2023"]
                },
                "document_type": "medical_protocol"
            },
            {
                "content": "Terapia de presión negativa (VAC) para LPP: Indicada en grado 3-4 con lecho limpio, presión 75-125 mmHg continua, cambio de apósito cada 2-3 días.",
                "metadata": {
                    "title": "Terapia de Presión Negativa",
                    "type": "advanced_therapy",
                    "evidence_level": "high",
                    "references": ["VAC Therapy Guidelines 2024"]
                },
                "document_type": "medical_protocol"
            },
            {
                "content": "Antibióticos sistémicos en LPP infectadas: Amoxicilina-clavulánico 875/125mg cada 8h para terapia empírica, vancomicina para MRSA, duración 7-14 días según respuesta.",
                "metadata": {
                    "title": "Antibióticos en LPP Infectadas",
                    "type": "medication_protocol",
                    "evidence_level": "high",
                    "references": ["Infectious Diseases Guidelines 2024"]
                },
                "document_type": "medical_protocol"
            }
        ]
        
        indexed_count = 0
        for protocol in protocols:
            try:
                await self.index_document(
                    content=protocol["content"],
                    metadata=protocol["metadata"],
                    document_type=protocol["document_type"]
                )
                indexed_count += 1
            except Exception as e:
                logger.error(f"Failed to index protocol: {e}")
        
        logger.info(f"Indexed {indexed_count} medical protocols")
        return indexed_count
    
    async def cleanup(self):
        """Limpiar recursos."""
        try:
            if self.redis_client:
                await self.redis_client.close()
            
            # Limpiar caches
            self.embedding_cache.clear()
            self.document_store.clear()
            self.index_to_doc_id.clear()
            
            logger.info("Vector service cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


class VectorServiceFactory:
    """Factory para crear instancias del servicio vectorial."""
    
    @staticmethod
    async def create_service(config: Optional[VectorSearchConfig] = None) -> EnhancedVectorService:
        """Crear servicio vectorial enhanced."""
        service = EnhancedVectorService(config)
        await service.initialize()
        
        # Indexar protocolos básicos si el índice está vacío
        stats = await service.get_stats()
        if stats["indexed_documents"] == 0:
            await service.index_medical_protocols()
        
        return service