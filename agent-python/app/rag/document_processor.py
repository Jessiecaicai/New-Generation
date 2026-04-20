"""Load documents (PDF/TXT/MD/DOCX), split into chunks."""
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    id: str
    text: str
    metadata: dict = field(default_factory=dict)


class DocumentProcessor:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", "。", "；", ".", " "],
        )

    def process(self, file_path: str) -> list[DocumentChunk]:
        ext = Path(file_path).suffix.lower()
        logger.info(f"Processing {file_path} (type: {ext})")

        text = self._load(file_path, ext)
        if not text.strip():
            logger.warning(f"Empty content: {file_path}")
            return []

        parts = self.splitter.split_text(text)
        fname = Path(file_path).name
        return [
            DocumentChunk(
                id=f"{Path(file_path).stem}_{i}_{uuid.uuid4().hex[:8]}",
                text=part,
                metadata={
                    "source": fname,
                    "file_path": file_path,
                    "chunk_index": i,
                    "total_chunks": len(parts),
                },
            )
            for i, part in enumerate(parts)
        ]

    # ------------------------------------------------------------------
    def _load(self, path: str, ext: str) -> str:
        if ext in (".txt", ".md"):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        if ext == ".pdf":
            return self._load_pdf(path)
        if ext == ".docx":
            return self._load_docx(path)
        raise ValueError(f"Unsupported file type: {ext}")

    @staticmethod
    def _load_pdf(path: str) -> str:
        try:
            from pypdf import PdfReader
            reader = PdfReader(path)
            return "\n\n".join(p.extract_text() or "" for p in reader.pages)
        except ImportError:
            logger.error("pypdf not installed")
            return ""

    @staticmethod
    def _load_docx(path: str) -> str:
        try:
            import docx2txt
            return docx2txt.process(path)
        except ImportError:
            logger.error("docx2txt not installed")
            return ""
