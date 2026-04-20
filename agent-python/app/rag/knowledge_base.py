"""Knowledge base management – index, delete, list."""
import logging
from app.rag.vector_store import VectorStoreManager
from app.rag.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)


class KnowledgeBaseManager:
    def __init__(self):
        self.vector_store = VectorStoreManager()
        self.processor = DocumentProcessor()

    def index_documents(self, kb_name: str, file_paths: list[str]) -> dict:
        total_chunks = 0
        errors: list[dict] = []
        for fp in file_paths:
            try:
                chunks = self.processor.process(fp)
                self.vector_store.add_documents(kb_name, chunks)
                total_chunks += len(chunks)
            except Exception as e:
                logger.error(f"Failed to index {fp}: {e}")
                errors.append({"file": fp, "error": str(e)})
        return {
            "knowledge_base": kb_name,
            "total_chunks": total_chunks,
            "files_processed": len(file_paths) - len(errors),
            "errors": errors,
        }

    def delete_knowledge_base(self, kb_name: str):
        self.vector_store.delete_collection(kb_name)

    def list_knowledge_bases(self) -> list[str]:
        return self.vector_store.list_collections()
