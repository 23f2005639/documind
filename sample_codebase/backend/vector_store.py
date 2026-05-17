from qdrant_client import QdrantClient


class VectorStore:
    """Handles semantic search operations"""

    def __init__(self):
        self.client = QdrantClient(url="http://localhost:6333")
        self.collection_name = "documind-vectors"

    def search_documents(self, embedding, limit=5):
        """Search similar vectors in Qdrant"""

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=embedding,
            limit=limit,
        )

        return response.points

    def insert_document(self, vector, payload):
        """Insert vector into collection"""

        self.client.upsert(
            collection_name=self.collection_name,
            points=[{
                "id": payload["id"],
                "vector": vector,
                "payload": payload
            }]
        )