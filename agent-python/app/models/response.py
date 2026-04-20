"""Response models."""
from typing import Optional, List
from pydantic import BaseModel


class ChatResponse(BaseModel):
    answer: str
    intent: str = "general"
    sql: Optional[str] = None
    rag_sources: Optional[List[dict]] = None
    tool_calls: Optional[list] = None
    confidence: Optional[float] = None


class SkillStatusResponse(BaseModel):
    name: str
    description: str
    enabled: bool
    skill_type: str = "BUILTIN"
    tools: List[str] = []
