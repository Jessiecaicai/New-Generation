"""Request models."""
from typing import Optional, List
from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    conversation_history: Optional[List[dict]] = None
    schema: Optional[dict] = None
    error_context: Optional[dict] = None  # {"previousSql": "...", "errorMessage": "..."}
    intent_hint: Optional[str] = None
