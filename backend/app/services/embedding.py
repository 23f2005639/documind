"""
Embedding Service for DocuMind
Generates vector embeddings for semantic search using sentence-transformers
"""

from typing import List, Dict, Optional
import hashlib
from datetime import datetime, timedelta
import structlog
from sentence_transformers import SentenceTransformer
import numpy as np

from app.config import settings

logger = structlog.get_logger()


class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self):
        self.model_name = settings.embedding_model
        self.dimension = settings.embedding_dimension
        self.model: Optional[SentenceTransformer] = None
        self.cache: Dict[str, tuple[List[float], datetime]] = {}
        self.cache_ttl = timedelta(days=7)
        
        logger.info("Initializing embedding service", model=self.model_name)
    
    def _load_model(self):
        """Lazy load the embedding model"""
        if self.model is None:
            logger.info("Loading embedding model", model=self.model_name)
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully")
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from text"""
        return hashlib.sha256(text.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[List[float]]:
        """Get embedding from cache if not expired"""
        if cache_key in self.cache:
            embedding, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                logger.debug("Cache hit", cache_key=cache_key[:16])
                return embedding
            else:
                # Remove expired entry
                del self.cache[cache_key]
        return None
    
    def _add_to_cache(self, cache_key: str, embedding: List[float]):
        """Add embedding to cache"""
        self.cache[cache_key] = (embedding, datetime.now())
    
    def preprocess_text(self, text: str) -> str:
        """
        Preprocess text before embedding
        
        Args:
            text: Input text
            
        Returns:
            Preprocessed text
        """
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        # Truncate if too long (model limit is typically 512 tokens)
        max_chars = 2000
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
            logger.debug("Text truncated", original_length=len(text))
        
        return text
    
    def embed(self, texts: List[str], use_cache: bool = True) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of texts to embed
            use_cache: Whether to use caching
            
        Returns:
            List of embedding vectors
        """
        self._load_model()
        
        # Preprocess texts
        processed_texts = [self.preprocess_text(t) for t in texts]
        
        # Check cache
        embeddings = []
        uncached_indices = []
        uncached_texts = []
        
        if use_cache:
            for i, text in enumerate(processed_texts):
                cache_key = self._get_cache_key(text)
                cached_embedding = self._get_from_cache(cache_key)
                
                if cached_embedding is not None:
                    embeddings.append(cached_embedding)
                else:
                    embeddings.append(None)
                    uncached_indices.append(i)
                    uncached_texts.append(text)
        else:
            uncached_indices = list(range(len(processed_texts)))
            uncached_texts = processed_texts
            embeddings = [None] * len(processed_texts)
        
        # Generate embeddings for uncached texts
        if uncached_texts:
            logger.info(
                "Generating embeddings",
                count=len(uncached_texts),
                cached=len(texts) - len(uncached_texts)
            )
            
            new_embeddings = self.model.encode(
                uncached_texts,
                convert_to_numpy=True,
                show_progress_bar=False,
                normalize_embeddings=True
            )
            
            # Update cache and results
            for idx, embedding in zip(uncached_indices, new_embeddings):
                embedding_list = embedding.tolist()
                embeddings[idx] = embedding_list
                
                if use_cache:
                    cache_key = self._get_cache_key(processed_texts[idx])
                    self._add_to_cache(cache_key, embedding_list)
        
        return embeddings
    
    def embed_single(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            use_cache: Whether to use caching
            
        Returns:
            Embedding vector
        """
        return self.embed([text], use_cache=use_cache)[0]
    
    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 32,
        use_cache: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings in batches for memory efficiency
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch
            use_cache: Whether to use caching
            
        Returns:
            List of embedding vectors
        """
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = self.embed(batch, use_cache=use_cache)
            all_embeddings.extend(batch_embeddings)
            
            logger.debug(
                "Batch processed",
                batch_num=i // batch_size + 1,
                total_batches=(len(texts) + batch_size - 1) // batch_size
            )
        
        return all_embeddings
    
    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0 to 1)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Cosine similarity
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        
        return float(similarity)
    
    def find_most_similar(
        self,
        query_embedding: List[float],
        candidate_embeddings: List[List[float]],
        top_k: int = 5
    ) -> List[tuple[int, float]]:
        """
        Find most similar embeddings to a query
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embeddings
            top_k: Number of top results to return
            
        Returns:
            List of (index, similarity_score) tuples
        """
        similarities = [
            (i, self.compute_similarity(query_embedding, emb))
            for i, emb in enumerate(candidate_embeddings)
        ]
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def clear_cache(self):
        """Clear the embedding cache"""
        self.cache.clear()
        logger.info("Embedding cache cleared")
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Get cache statistics"""
        now = datetime.now()
        valid_entries = sum(
            1 for _, timestamp in self.cache.values()
            if now - timestamp < self.cache_ttl
        )
        
        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.cache) - valid_entries,
            "cache_ttl_days": self.cache_ttl.days,
            "model": self.model_name,
            "dimension": self.dimension
        }
    
    def get_model_info(self) -> Dict[str, any]:
        """Get embedding model information"""
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "max_sequence_length": 512 if self.model is None else self.model.max_seq_length,
            "loaded": self.model is not None
        }


# Global instance
embedding_service = EmbeddingService()

# Made with Bob
