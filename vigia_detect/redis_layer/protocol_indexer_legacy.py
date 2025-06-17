"""Medical protocol indexing service for RAG operations."""
import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import PyPDF2
import redis
from redis.commands.search.field import TextField, NumericField, VectorField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
import numpy as np

from .config import get_redis_config
from .embeddings import MedicalEmbeddingService

logger = logging.getLogger(__name__)


class MedicalProtocolIndexer:
    """Service for indexing and searching medical protocols."""
    
    def __init__(self):
        self.config = get_redis_config()
        self.embedding_service = MedicalEmbeddingService()
        self.embedding_dim = self.embedding_service.embedding_dim
        
        # Initialize Redis client
        self.client = redis.Redis(
            host=self.config.host,
            port=self.config.port,
            password=self.config.password,
            ssl=self.config.ssl,
            decode_responses=True
        )
        
        # Index configuration
        self.index_name = "idx:medical_protocols"
        self.key_prefix = "protocol:"
        
        # Create index
        self._create_index()
        
    def _create_index(self):
        """Create Redis search index for medical protocols."""
        try:
            self.client.ft(self.index_name).info()
            logger.info(f"Index {self.index_name} already exists")
        except redis.ResponseError:
            logger.info(f"Creating index {self.index_name}")
            
            schema = (
                TextField("title", no_stem=True, weight=2.0),
                TextField("content", weight=1.0),
                TextField("source", no_stem=True),
                TagField("tags"),
                TagField("lpp_grades"),
                NumericField("page_number"),
                VectorField(
                    "embedding",
                    "HNSW",  # Use HNSW for better performance
                    {
                        "TYPE": "FLOAT32",
                        "DIM": self.embedding_dim,
                        "DISTANCE_METRIC": "COSINE",
                        "M": 16,
                        "EF_CONSTRUCTION": 200
                    }
                )
            )
            
            definition = IndexDefinition(
                prefix=[self.key_prefix],
                index_type=IndexType.HASH
            )
            
            self.client.ft(self.index_name).create_index(
                fields=schema,
                definition=definition
            )
            
    def index_protocols_from_directory(self, directory: str):
        """
        Index all protocol documents from a directory.
        
        Args:
            directory: Path to directory containing protocol PDFs
        """
        protocol_dir = Path(directory)
        if not protocol_dir.exists():
            logger.error(f"Directory not found: {directory}")
            return
            
        pdf_files = list(protocol_dir.glob("*.pdf"))
        logger.info(f"Found {len(pdf_files)} PDF files to index")
        
        for pdf_file in pdf_files:
            try:
                self._index_pdf_protocol(pdf_file)
            except Exception as e:
                logger.error(f"Failed to index {pdf_file}: {e}")
                
    def _index_pdf_protocol(self, pdf_path: Path):
        """Index a single PDF protocol document."""
        logger.info(f"Indexing protocol: {pdf_path.name}")
        
        # Extract text from PDF
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if not text.strip():
                    continue
                    
                # Split into chunks (simple paragraph-based splitting)
                chunks = self._chunk_text(text, chunk_size=500)
                
                for i, chunk in enumerate(chunks):
                    # Extract metadata
                    metadata = self._extract_metadata(chunk, pdf_path.name)
                    
                    # Generate embedding
                    embedding = self.embedding_service.generate_medical_embedding(chunk)
                    
                    # Create document key
                    doc_key = f"{self.key_prefix}{pdf_path.stem}:p{page_num}:c{i}"
                    
                    # Store document
                    doc_data = {
                        "title": f"{pdf_path.stem} - Page {page_num + 1}",
                        "content": chunk,
                        "source": pdf_path.name,
                        "tags": ",".join(metadata.get("tags", [])),
                        "lpp_grades": ",".join(metadata.get("lpp_grades", [])),
                        "page_number": page_num + 1,
                        "embedding": embedding.astype(np.float32).tobytes()
                    }
                    
                    self.client.hset(doc_key, mapping=doc_data)
                    
        logger.info(f"Successfully indexed {pdf_path.name}")
        
    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into chunks for indexing."""
        # Simple sentence-aware chunking
        sentences = text.split('. ')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > chunk_size and current_chunk:
                chunks.append('. '.join(current_chunk) + '.')
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
                
        if current_chunk:
            chunks.append('. '.join(current_chunk))
            
        return chunks
        
    def _extract_metadata(self, text: str, source: str) -> Dict[str, List[str]]:
        """Extract metadata from protocol text."""
        metadata = {
            "tags": [],
            "lpp_grades": []
        }
        
        # Extract LPP grades mentioned
        text_lower = text.lower()
        for grade in ["grado i", "grado ii", "grado iii", "grado iv", "estadio 1", "estadio 2", "estadio 3", "estadio 4"]:
            if grade in text_lower:
                grade_num = grade.split()[-1].replace("i", "1").replace("ii", "2").replace("iii", "3").replace("iv", "4")
                metadata["lpp_grades"].append(f"grade_{grade_num}")
                
        # Extract common medical tags
        medical_terms = {
            "prevención": "prevention",
            "tratamiento": "treatment",
            "diagnóstico": "diagnosis",
            "evaluación": "assessment",
            "cuidados": "care",
            "riesgo": "risk",
            "úlcera": "ulcer",
            "presión": "pressure"
        }
        
        for spanish, english in medical_terms.items():
            if spanish in text_lower:
                metadata["tags"].append(english)
                
        # Add source-based tags
        if "epuap" in source.lower():
            metadata["tags"].append("epuap")
        if "minsal" in source.lower():
            metadata["tags"].append("minsal")
            
        return metadata
        
    async def search_protocols(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search medical protocols using vector similarity.
        
        Args:
            query: Search query
            filters: Optional filters (lpp_grade, tags)
            limit: Maximum number of results
            
        Returns:
            List of relevant protocol sections
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.generate_medical_embedding(query)
            
            # Build filter string
            filter_parts = []
            if filters:
                if "lpp_grade" in filters:
                    filter_parts.append(f"@lpp_grades:{{{filters['lpp_grade']}}}")
                if "tags" in filters:
                    tags = filters["tags"] if isinstance(filters["tags"], list) else [filters["tags"]]
                    filter_parts.append(f"@tags:{{{' | '.join(tags)}}}")
                    
            filter_string = " ".join(filter_parts) if filter_parts else "*"
            
            # Build search query
            search_query = (
                Query(f"({filter_string})=>[KNN {limit} @embedding $vector AS score]")
                .return_fields("title", "content", "source", "tags", "lpp_grades", "page_number", "score")
                .sort_by("score")
                .dialect(2)
            )
            
            # Execute search
            results = self.client.ft(self.index_name).search(
                search_query,
                query_params={
                    "vector": query_embedding.astype(np.float32).tobytes()
                }
            )
            
            # Format results
            formatted_results = []
            for doc in results.docs:
                formatted_results.append({
                    "title": doc.title,
                    "content": doc.content,
                    "source": doc.source,
                    "page": int(doc.page_number),
                    "tags": doc.tags.split(",") if doc.tags else [],
                    "lpp_grades": doc.lpp_grades.split(",") if doc.lpp_grades else [],
                    "relevance_score": 1 - float(doc.score)  # Convert distance to similarity
                })
                
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching protocols: {e}")
            return []
            
    async def get_protocol_context(
        self,
        lpp_grade: int,
        context_type: str = "treatment"
    ) -> List[Dict[str, Any]]:
        """
        Get specific protocol context for a given LPP grade.
        
        Args:
            lpp_grade: LPP grade (1-4)
            context_type: Type of context (treatment, prevention, assessment)
            
        Returns:
            Relevant protocol sections
        """
        query = f"LPP grado {lpp_grade} {context_type}"
        filters = {
            "lpp_grade": f"grade_{lpp_grade}",
            "tags": context_type
        }
        
        return await self.search_protocols(query, filters, limit=3)
        
    def index_protocol_json(self, protocol_data: Dict[str, Any]):
        """Index a protocol from JSON format (for structured data)."""
        try:
            # Generate unique key
            doc_key = f"{self.key_prefix}{protocol_data.get('id', 'unknown')}"
            
            # Generate embedding
            content = f"{protocol_data.get('title', '')} {protocol_data.get('content', '')}"
            embedding = self.embedding_service.generate_medical_embedding(content)
            
            # Prepare data
            doc_data = {
                "title": protocol_data.get("title", ""),
                "content": protocol_data.get("content", ""),
                "source": protocol_data.get("source", "manual"),
                "tags": ",".join(protocol_data.get("tags", [])),
                "lpp_grades": ",".join(protocol_data.get("lpp_grades", [])),
                "page_number": protocol_data.get("page", 1),
                "embedding": embedding.astype(np.float32).tobytes()
            }
            
            self.client.hset(doc_key, mapping=doc_data)
            logger.info(f"Indexed protocol: {protocol_data.get('title', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Error indexing protocol JSON: {e}")
            
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the protocol index."""
        try:
            info = self.client.ft(self.index_name).info()
            return {
                "num_docs": info.get("num_docs", 0),
                "index_name": self.index_name,
                "index_options": info.get("index_options", {}),
                "fields": info.get("fields", [])
            }
        except Exception as e:
            logger.error(f"Error getting index stats: {e}")
            return {}


# Legacy alias for backward compatibility
ProtocolIndexer = MedicalProtocolIndexer