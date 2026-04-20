"""RAG retriever – semantic search + relevance filtering."""
import logging
from app.rag.vector_store import VectorStoreManager, RetrievalResult

logger = logging.getLogger(__name__)


class RAGRetriever:
    def __init__(self, vector_store: VectorStoreManager):
        self.vector_store = vector_store

    def retrieve(
        self,
        question: str,
        collection_names: list[str],
        top_k: int = 5,
        score_threshold: float = 1.5,
    ) -> list[RetrievalResult]:
        all_results: list[RetrievalResult] = []
        for name in collection_names:
            try:
                results = self.vector_store.query(name, question, top_k=top_k)
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"Retrieval from '{name}' failed: {e}")

        filtered = [r for r in all_results if r.score <= score_threshold]
        filtered.sort(key=lambda r: r.score)
        logger.info(f"Retrieved {len(filtered)}/{len(all_results)} results")
        return filtered[:top_k]
