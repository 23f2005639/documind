"""
Hybrid Search Service for DocuMind
Combines semantic search (vector) with keyword search (BM25)
"""

from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import re
import math
from collections import defaultdict
import structlog

from app.services.vector_store import vector_store
from app.services.embedding import embedding_service
from app.models.query import SearchResult

logger = structlog.get_logger()


class BM25:
    """BM25 ranking algorithm for keyword search"""
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 with parameters
        
        Args:
            k1: Term frequency saturation parameter (default: 1.5)
            b: Length normalization parameter (default: 0.75)
        """
        self.k1 = k1
        self.b = b
        self.corpus: List[Dict[str, Any]] = []
        self.doc_freqs: Dict[str, int] = defaultdict(int)
        self.idf: Dict[str, float] = {}
        self.doc_len: List[int] = []
        self.avgdl: float = 0.0
        self.N: int = 0
        
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Convert to lowercase and split on non-alphanumeric
        tokens = re.findall(r'\w+', text.lower())
        return tokens
    
    def fit(self, corpus: List[Dict[str, Any]]):
        """
        Fit BM25 on a corpus of documents
        
        Args:
            corpus: List of documents with 'id', 'content', and 'metadata'
        """
        self.corpus = corpus
        self.N = len(corpus)
        
        # Calculate document frequencies and lengths
        for doc in corpus:
            tokens = self._tokenize(doc['content'])
            self.doc_len.append(len(tokens))
            
            # Count unique terms in document
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] += 1
        
        # Calculate average document length
        self.avgdl = sum(self.doc_len) / self.N if self.N > 0 else 0
        
        # Calculate IDF for each term
        for term, freq in self.doc_freqs.items():
            self.idf[term] = math.log((self.N - freq + 0.5) / (freq + 0.5) + 1.0)
        
        logger.info(
            "BM25 fitted",
            corpus_size=self.N,
            unique_terms=len(self.idf),
            avg_doc_length=self.avgdl
        )
    
    def search(self, query: str, limit: int = 10) -> List[Tuple[int, float]]:
        """
        Search corpus using BM25
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of (doc_index, score) tuples
        """
        query_tokens = self._tokenize(query)
        scores = []
        
        for idx, doc in enumerate(self.corpus):
            doc_tokens = self._tokenize(doc['content'])
            doc_len = self.doc_len[idx]
            
            # Calculate BM25 score
            score = 0.0
            term_freqs = defaultdict(int)
            for token in doc_tokens:
                term_freqs[token] += 1
            
            for token in query_tokens:
                if token not in self.idf:
                    continue
                
                tf = term_freqs[token]
                idf = self.idf[token]
                
                # BM25 formula
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
                score += idf * (numerator / denominator)
            
            scores.append((idx, score))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[:limit]


class HybridSearch:
    """Hybrid search combining semantic and keyword search"""
    
    def __init__(self):
        self.bm25: Optional[BM25] = None
        self.corpus: List[Dict[str, Any]] = []
        self.corpus_indexed = False
        
        logger.info("Hybrid search initialized")
    
    async def index_corpus(self, documents: List[Dict[str, Any]]):
        """
        Index documents for keyword search
        
        Args:
            documents: List of documents with 'id', 'content', and 'metadata'
        """
        self.corpus = documents
        self.bm25 = BM25()
        self.bm25.fit(documents)
        self.corpus_indexed = True
        
        logger.info("Corpus indexed for hybrid search", doc_count=len(documents))
    
    async def semantic_search(
        self,
        query: str,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using vector similarity
        
        Args:
            query: Search query
            limit: Maximum number of results
            filters: Optional metadata filters
            
        Returns:
            List of search results with scores
        """
        results = await vector_store.search(
            query=query,
            limit=limit,
            filters=filters,
            score_threshold=0.3  # Minimum relevance threshold
        )
        
        logger.info("Semantic search completed", results_count=len(results))
        return results
    
    async def keyword_search(
        self,
        query: str,
        limit: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform keyword search using BM25
        
        Args:
            query: Search query
            limit: Maximum number of results
            filters: Optional metadata filters
            
        Returns:
            List of search results with scores
        """
        if not self.corpus_indexed or self.bm25 is None:
            logger.warning("Corpus not indexed, returning empty results")
            return []
        
        # Get BM25 scores
        bm25_results = self.bm25.search(query, limit=limit)
        
        # Format results
        results = []
        for idx, score in bm25_results:
            if score <= 0:
                continue
            
            doc = self.corpus[idx]
            
            # Apply filters if provided
            if filters:
                match = all(
                    doc.get('metadata', {}).get(k) == v
                    for k, v in filters.items()
                )
                if not match:
                    continue
            
            results.append({
                "id": doc['id'],
                "score": score,
                "doc_id": doc.get('doc_id', doc['id']),
                "content": doc['content'],
                "metadata": doc.get('metadata', {})
            })
        
        logger.info("Keyword search completed", results_count=len(results))
        return results
    
    def _normalize_scores(
        self,
        results: List[Dict[str, Any]],
        method: str = "minmax"
    ) -> List[Dict[str, Any]]:
        """
        Normalize scores to [0, 1] range
        
        Args:
            results: Search results with scores
            method: Normalization method ('minmax' or 'zscore')
            
        Returns:
            Results with normalized scores
        """
        if not results:
            return results
        
        scores = [r['score'] for r in results]
        
        if method == "minmax":
            min_score = min(scores)
            max_score = max(scores)
            score_range = max_score - min_score
            
            if score_range == 0:
                # All scores are the same
                for r in results:
                    r['normalized_score'] = 1.0
            else:
                for r in results:
                    r['normalized_score'] = (r['score'] - min_score) / score_range
        
        elif method == "zscore":
            mean_score = sum(scores) / len(scores)
            std_score = math.sqrt(sum((s - mean_score) ** 2 for s in scores) / len(scores))
            
            if std_score == 0:
                for r in results:
                    r['normalized_score'] = 0.5
            else:
                for r in results:
                    z = (r['score'] - mean_score) / std_score
                    # Convert z-score to [0, 1] using sigmoid
                    r['normalized_score'] = 1 / (1 + math.exp(-z))
        
        return results
    
    def _fuse_results(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.4
    ) -> List[Dict[str, Any]]:
        """
        Fuse semantic and keyword search results
        
        Args:
            semantic_results: Results from semantic search
            keyword_results: Results from keyword search
            semantic_weight: Weight for semantic scores (default: 0.6)
            keyword_weight: Weight for keyword scores (default: 0.4)
            
        Returns:
            Fused and ranked results
        """
        # Normalize scores
        semantic_results = self._normalize_scores(semantic_results)
        keyword_results = self._normalize_scores(keyword_results)
        
        # Combine results by doc_id
        combined: Dict[str, Dict[str, Any]] = {}
        
        for result in semantic_results:
            doc_id = result['doc_id']
            combined[doc_id] = {
                **result,
                'semantic_score': result['normalized_score'],
                'keyword_score': 0.0,
                'combined_score': result['normalized_score'] * semantic_weight
            }
        
        for result in keyword_results:
            doc_id = result['doc_id']
            if doc_id in combined:
                # Document found in both searches
                combined[doc_id]['keyword_score'] = result['normalized_score']
                combined[doc_id]['combined_score'] += result['normalized_score'] * keyword_weight
            else:
                # Document only in keyword search
                combined[doc_id] = {
                    **result,
                    'semantic_score': 0.0,
                    'keyword_score': result['normalized_score'],
                    'combined_score': result['normalized_score'] * keyword_weight
                }
        
        # Convert to list and sort by combined score
        fused_results = list(combined.values())
        fused_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        logger.info(
            "Results fused",
            semantic_count=len(semantic_results),
            keyword_count=len(keyword_results),
            combined_count=len(fused_results)
        )
        
        return fused_results
    
    async def search(
        self,
        query: str,
        search_type: str = "hybrid",
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.4
    ) -> List[SearchResult]:
        """
        Perform hybrid search
        
        Args:
            query: Search query
            search_type: Type of search ('semantic', 'keyword', or 'hybrid')
            limit: Maximum number of results
            filters: Optional metadata filters
            semantic_weight: Weight for semantic search (default: 0.6)
            keyword_weight: Weight for keyword search (default: 0.4)
            
        Returns:
            List of search results
        """
        logger.info(
            "Performing search",
            query=query[:50],
            search_type=search_type,
            limit=limit
        )
        
        if search_type == "semantic":
            results = await self.semantic_search(query, limit=limit, filters=filters)
            results = self._normalize_scores(results)
            
        elif search_type == "keyword":
            results = await self.keyword_search(query, limit=limit, filters=filters)
            results = self._normalize_scores(results)
            
        else:  # hybrid
            # Perform both searches with higher limits
            semantic_results = await self.semantic_search(
                query, limit=limit * 2, filters=filters
            )
            keyword_results = await self.keyword_search(
                query, limit=limit * 2, filters=filters
            )
            
            # Fuse results
            results = self._fuse_results(
                semantic_results,
                keyword_results,
                semantic_weight,
                keyword_weight
            )
        
        # Limit final results
        results = results[:limit]
        
        # Convert to SearchResult models
        search_results = []
        for r in results:
            metadata = r.get('metadata', {})
            
            # Extract highlights (first 200 chars of content)
            content = r.get('content', '')
            highlight = content[:200] + "..." if len(content) > 200 else content
            
            search_results.append(SearchResult(
                id=str(r['id']),
                type=metadata.get('type', 'documentation'),
                title=metadata.get('title', 'Untitled'),
                content=content,
                score=r.get('combined_score', r.get('normalized_score', r['score'])),
                metadata=metadata,
                highlights=[highlight]
            ))
        
        logger.info("Search completed", results_count=len(search_results))
        
        return search_results


# Global instance
hybrid_search = HybridSearch()

# Made with Bob