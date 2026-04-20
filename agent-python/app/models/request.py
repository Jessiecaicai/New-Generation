"""Request models."""
from typing import Optional, List, Dict
from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    conversation_history: Optional[List[dict]] = None
    schema: Optional[dict] = None
    knowledge_bases: Optional[List[str]] = None
    error_context: Optional[dict] = None  # {"previousSql": "...", "errorMessage": "..."}
    intent_hint: Optional[str] = None


class KnowledgeIndexRequest(BaseModel):
    knowledge_base_name: str
    file_paths: List[str]
