from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Generate embeddings for semantic search"""

    def __init__(self):
        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

    def embed_text(self, text: str):
        """Convert text into embedding vector"""

        return self.model.encode(text).tolist()

    def embed_batch(self, texts):
        """Generate embeddings for multiple texts"""

        return self.model.encode(texts).tolist()