"""Central Agent Engine – orchestrates intent recognition, RAG, skills, and LLM."""
import asyncio
import logging
import re
from typing import Optional, List
from langchain_ollama import ChatOllama
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.messages import HumanMessage, AIMessage

from app.config import get_config
from app.core.intent_recognizer import IntentRecognizer
from app.core.context_assembler import ContextAssembler
from app.rag.retriever import RAGRetriever
from app.rag.vector_store import VectorStoreManager
from app.skills import SkillRegistry
from app.models.request import ChatRequest
from app.models.response import ChatResponse

logger = logging.getLogger(__name__)

_llm_semaphore = None  # type: Optional[asyncio.Semaphore]


def _get_semaphore() -> asyncio.Semaphore:
    global _llm_semaphore
    if _llm_semaphore is None:
        _llm_semaphore = asyncio.Semaphore(get_config().max_concurrent_llm)
    return _llm_semaphore


class AgentEngine:
    """Core agent: intent -> RAG -> context -> tool-calling -> response."""

    def __init__(self):
        cfg = get_config()
        self.llm = ChatOllama(
            model=cfg.llm_model,
            temperature=cfg.llm_temperature,
            base_url=cfg.ollama_base_url,
        )
        self.intent_recognizer = IntentRecognizer(self.llm)
        self.rag_retriever = RAGRetriever(VectorStoreManager())
        self.context_assembler = ContextAssembler()

    # ------------------------------------------------------------------
    async def run(self, request: ChatRequest) -> ChatResponse:
        async with _get_semaphore():
            return await self._execute(request)

    # ------------------------------------------------------------------
    async def _execute(self, request: ChatRequest) -> ChatResponse:
        try:
            # 1. Intent recognition
            if request.intent_hint:
                intent = request.intent_hint
                needs_rag = intent == "knowledge_qa"
            else:
                ir = await self.intent_recognizer.recognize(
                    request.question, request.conversation_history or []
                )
                intent = ir["intent"]
                needs_rag = ir.get("needs_rag", False)

            # 2. RAG retrieval
            rag_context = ""
            rag_sources = []  # type: List[dict]
            if needs_rag and request.knowledge_bases:
                results = self.rag_retriever.retrieve(
                    request.question, request.knowledge_bases
                )
                rag_context = self.context_assembler.format_rag_results(results)
                rag_sources = [
                    {"text": r.text, "source": r.metadata.get("source", ""), "score": r.score}
                    for r in results
                ]

            # 3. Gather tools
            active_skills = SkillRegistry.get_skills_for_intent(intent)
            tools = []
            for s in active_skills:
                tools.extend(s.get_tools())
            if not tools:
                tools = SkillRegistry.get_all_tools()

            # 4. Build prompt
            prompt = self.context_assembler.build_prompt(
                intent=intent,
                rag_context=rag_context,
                schema=request.schema,
                skills=active_skills,
                error_context=request.error_context,
            )

            # 5. Execute
            history = self._format_history(request.conversation_history)
            if tools:
                agent = create_tool_calling_agent(self.llm, tools, prompt)
                executor = AgentExecutor(
                    agent=agent,
                    tools=tools,
                    max_iterations=8,
                    verbose=True,
                    handle_parsing_errors=True,
                )
                result = await executor.ainvoke(
                    {"input": request.question, "chat_history": history}
                )
                answer = result["output"]
            else:
                msgs = prompt.format_messages(
                    input=request.question,
                    chat_history=history,
                    agent_scratchpad=[],
                )
                resp = await self.llm.ainvoke(msgs)
                answer = resp.content

            # 6. Extract SQL for nl2sql
            sql = self._extract_sql(answer) if intent == "nl2sql" else None

            return ChatResponse(
                answer=answer,
                intent=intent,
                sql=sql,
                rag_sources=rag_sources or None,
                confidence=0.9,
            )
        except Exception as e:
            logger.error(f"Agent execution error: {e}", exc_info=True)
            return ChatResponse(
                answer=f"处理请求时发生错误: {e}",
                intent="error",
                confidence=0.0,
            )

    # ------------------------------------------------------------------
    @staticmethod
    def _format_history(history: Optional[list]) -> list:
        msgs = []
        for m in history or []:
            if m.get("role") == "user":
                msgs.append(HumanMessage(content=m["content"]))
            elif m.get("role") == "assistant":
                msgs.append(AIMessage(content=m["content"]))
        return msgs

    @staticmethod
    def _extract_sql(text: str) -> Optional[str]:
        match = re.search(r"```sql\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        match = re.search(r"(SELECT\s+.+?;)", text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return None


# Singleton ----------------------------------------------------------------
_engine = None  # type: Optional[AgentEngine]


def get_engine() -> AgentEngine:
    global _engine
    if _engine is None:
        _engine = AgentEngine()
    return _engine
