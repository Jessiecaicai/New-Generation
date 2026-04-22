"""Response models."""
from typing import Optional, List
from pydantic import BaseModel


class ChatResponse(BaseModel):
    answer: str
    intent: str = "general"
    sql: Optional[str] = None           # 标准 SQL（数据库执行用）
    display_sql: Optional[str] = None   # 直观 SQL（给用户看的，带中文别名）
    rag_sources: Optional[List[dict]] = None
    tool_calls: Optional[list] = None
    confidence: Optional[float] = None


class SkillStatusResponse(BaseModel):
    name: str
    description: str
    enabled: bool
    skill_type: str = "BUILTIN"
    tools: List[str] = []
