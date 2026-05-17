"""
Vector Store Service for DocuMind using Qdrant Cloud
Manages vector storage and similarity search
"""

from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
import structlog
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    PointIdsList,
)

from app.config import settings
from app.services.embedding import embedding_service

logger = structlog.get_logger()


class VectorStore:
    """Service for managing vector storage with Qdrant"""
    
    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self.collection_name = "documind-vectors"
        self.dimension = settings.embedding_dimension
        
        logger.info("Initializing vector store", collection=self.collection_name)
    
    def _connect(self):
        """Lazy connect to Qdrant Cloud"""
        if self.client is None:
            logger.info("Connecting to Qdrant Cloud")
            self.client = QdrantClient(
    url=settings.qdrant_url,
    api_key=settings.qdrant_api_key,
    prefer_grpc=False,
    timeout=60,
)
            logger.info("Connected to Qdrant Cloud")
    
    async def initialize_collection(self):
        """Initialize the vector collection if it doesn't exist"""
        self._connect()
        
        # Check if collection exists
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.collection_name not in collection_names:
            logger.info("Creating collection", name=self.collection_name)
            
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.dimension,
                    distance=Distance.COSINE
                )
            )
            
            logger.info("Collection created successfully")
        else:
            logger.info("Collection already exists", name=self.collection_name)
    
    async def index_document(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Index a single document
        
        Args:
            doc_id: Document ID
            content: Document content
            metadata: Document metadata
            
        Returns:
            Point ID
        """
        self._connect()
        
        # Generate embedding
        embedding = embedding_service.embed_single(content)
        
        # Create point
        point_id = str(uuid4())
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "doc_id": doc_id,
                "content": content,
                **metadata
            }
        )
        
        # Upsert to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        
        logger.info(
            "Document indexed",
            doc_id=doc_id,
            point_id=point_id,
            content_length=len(content)
        )
        
        return point_id
    
    async def index_documents_batch(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Index multiple documents in batch
        
        Args:
            documents: List of documents with 'doc_id', 'content', and 'metadata'
            
        Returns:
            List of point IDs
        """
        self._connect()
        
        # Extract content for batch embedding
        contents = [doc["content"] for doc in documents]
        
        # Generate embeddings in batch
        logger.info("Generating embeddings for batch", count=len(documents))
        embeddings = embedding_service.embed_batch(contents, batch_size=32)
        
        # Create points
        points = []
        point_ids = []
        
        for doc, embedding in zip(documents, embeddings):
            point_id = str(uuid4())
            point_ids.append(point_id)
            
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "doc_id": doc["doc_id"],
                    "content": doc["content"],
                    **doc.get("metadata", {})
                }
            )
            points.append(point)
        
        # Batch upsert
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        logger.info("Batch indexed successfully", count=len(points))
        
        return point_ids
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents
        
        Args:
            query: Search query
            limit: Maximum number of results
            filters: Optional metadata filters
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results with scores
        """
        self._connect()
        
        # Generate query embedding
        query_embedding = embedding_service.embed_single(query)
        
        # Build filter if provided
        query_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            query_filter = Filter(must=conditions)
        
        # Search
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=limit,
            query_filter=query_filter,
            score_threshold=score_threshold,
            with_payload=True,
        )

        # Format results
        formatted_results = []
        for result in response.points:
            formatted_results.append({
                "id": result.id,
                "score": result.score,
                "doc_id": result.payload.get("doc_id"),
                "content": result.payload.get("content"),
                "metadata": {
                    k: v for k, v in result.payload.items()
                    if k not in ["doc_id", "content"]
                }
            })

        logger.info(
            "Search completed",
            query_length=len(query),
            results_count=len(formatted_results)
        )

        return formatted_results
    
    async def search_by_vector(
        self,
        vector: List[float],
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search using a pre-computed vector
        
        Args:
            vector: Query vector
            limit: Maximum number of results
            filters: Optional metadata filters
            
        Returns:
            List of search results
        """
        self._connect()
        
        # Build filter if provided
        query_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                )
            query_filter = Filter(must=conditions)
        
        # Search
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=limit,
            query_filter=query_filter,
            with_payload=True,
        )

        # Format results
        formatted_results = []
        for result in response.points:
            formatted_results.append({
                "id": result.id,
                "score": result.score,
                "doc_id": result.payload.get("doc_id"),
                "content": result.payload.get("content"),
                "metadata": {
                    k: v for k, v in result.payload.items()
                    if k not in ["doc_id", "content"]
                }
            })

        return formatted_results
    
    async def delete_by_doc_id(self, doc_id: str) -> int:
        """
        Delete all points associated with a document ID
        
        Args:
            doc_id: Document ID
            
        Returns:
            Number of points deleted
        """
        self._connect()
        
        # Search for points with this doc_id
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=doc_id)
                    )
                ]
            ),
            limit=1000
        )
        
        point_ids = [point.id for point in results[0]]
        
        if point_ids:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=PointIdsList(points=point_ids),
            )
            
            logger.info("Points deleted", doc_id=doc_id, count=len(point_ids))
        
        return len(point_ids)
    
    async def update_document(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Update a document (delete old, insert new)
        
        Args:
            doc_id: Document ID
            content: New content
            metadata: New metadata
            
        Returns:
            New point ID
        """
        # Delete old version
        await self.delete_by_doc_id(doc_id)
        
        # Index new version
        return await self.index_document(doc_id, content, metadata)
    
    async def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection"""
        self._connect()
        
        info = self.client.get_collection(self.collection_name)
        
        return {
            "name": info.config.params.vectors.size,
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "indexed_vectors_count": info.indexed_vectors_count,
            "status": info.status
        }
    
    async def clear_collection(self):
        """Delete all points in the collection"""
        self._connect()
        
        logger.warning("Clearing entire collection", name=self.collection_name)
        
        self.client.delete_collection(self.collection_name)
        await self.initialize_collection()
        
        logger.info("Collection cleared and recreated")


# Global instance
vector_store = VectorStore()

# Made with Bob
