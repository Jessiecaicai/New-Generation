"""ChromaDB vector store manager – singleton, persistent."""
import logging
from dataclasses import dataclass, field
from pathlib import Path
import chromadb
from chromadb.config import Settings
from app.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    text: str
    metadata: dict = field(default_factory=dict)
    score: float = 0.0


class VectorStoreManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        config = get_config()
        db_path = str(config.vectordb_dir)
        Path(db_path).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False),
        )
        self._initialized = True
        logger.info(f"ChromaDB initialized at {db_path}")

    def get_or_create_collection(self, name: str):
        return self.client.get_or_create_collection(
            name=name, metadata={"hnsw:space": "cosine"}
        )

    def add_documents(self, collection_name: str, chunks: list):
        if not chunks:
            return
        coll = self.get_or_create_collection(collection_name)
        coll.add(
            ids=[c.id for c in chunks],
            documents=[c.text for c in chunks],
            metadatas=[c.metadata for c in chunks],
        )
        logger.info(f"Added {len(chunks)} chunks to '{collection_name}'")

    def query(self, collection_name: str, question: str, top_k: int = 5) -> list[RetrievalResult]:
        try:
            coll = self.get_or_create_collection(collection_name)
            results = coll.query(query_texts=[question], n_results=top_k)
            return [
                RetrievalResult(text=doc, metadata=meta, score=dist)
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ]
        except Exception as e:
            logger.error(f"Vector query error: {e}")
            return []

    def delete_collection(self, name: str):
        try:
            self.client.delete_collection(name)
            logger.info(f"Deleted collection '{name}'")
        except Exception as e:
            logger.warning(f"Failed to delete collection '{name}': {e}")

    def list_collections(self) -> list[str]:
        return [c.name for c in self.client.list_collections()]
