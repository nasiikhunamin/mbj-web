"""Dense retriever over a ChromaDB strategy collection (Task 2.8)."""

from typing import List, Optional

from rag_service.embeddings.e5_encoder import E5Encoder
from rag_service.retrievers.base import RetrievedChunk
from rag_service.stores.chroma_manager import ChromaManager


class DenseRetriever:
    """Cosine similarity search with automatic ``"query: "`` prefixing."""

    def __init__(
        self,
        store: ChromaManager,
        strategy: str = "structure_aware",
        encoder: Optional[E5Encoder] = None,
    ):
        self.store = store
        self.strategy = strategy
        self.encoder = encoder or E5Encoder()
        self.store.collection_name(strategy)  # validate strategy early

    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """Return the top-k dense matches with similarity score and source metadata."""
        if not query or not query.strip():
            return []
        query_embedding = self.encoder.embed_query(query)
        records = self.store.query(self.strategy, query_embedding, top_k=top_k)
        return [
            RetrievedChunk.from_record(record, rank=index + 1)
            for index, record in enumerate(records)
        ]
