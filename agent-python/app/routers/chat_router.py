"""Agent unified chat endpoint."""
import logging
from fastapi import APIRouter
from app.models.request import ChatRequest
from app.models.response import ChatResponse
from app.core.agent_engine import get_engine
from app.skills.builtin.nl2sql.sql_tools import set_schema_context

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    logger.info(f"Chat: {request.question[:100]}...")
    if request.schema:
        set_schema_context(request.schema)
    response = await get_engine().run(request)
    logger.info(f"Intent: {response.intent}")
    return response
