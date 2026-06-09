"""
Agent 引擎核心 —— 整个 AI Agent 的"总指挥"。
职责：把意图识别 / Skill 选择 / Prompt 组装 / LLM 调用 串成一条流水线。

调用方：FastAPI router (routers/chat_router.py) → AgentEngine.run()
"""
import asyncio
import logging
import re
from typing import Optional, List
from langchain_openai import ChatOpenAI           # LangChain 对 OpenAI 协议模型的封装（用来接 DeepSeek）
from langchain_ollama import ChatOllama           # LangChain 对本地 Ollama 的封装（备用方案）
from langchain.agents import AgentExecutor, create_tool_calling_agent  # ReAct Agent 核心
from langchain_core.messages import HumanMessage, AIMessage

from app.config import get_config
from app.core.intent_recognizer import IntentRecognizer
from app.core.context_assembler import ContextAssembler
from app.skills import SkillRegistry
from app.models.request import ChatRequest
from app.models.response import ChatResponse

logger = logging.getLogger(__name__)

# ---------------- 并发限流 ----------------
# 用 asyncio.Semaphore 控制"同时正在调 LLM 的协程数"，防止把 DeepSeek 打爆 / 触发限流。
# 注意：这是协程级别的限流，不是线程；FastAPI 单进程内多个请求并发时生效。
_llm_semaphore = None  # type: Optional[asyncio.Semaphore]


def _get_semaphore() -> asyncio.Semaphore:
    """懒加载的全局信号量（第一次用到时再创建，避免 import 期就读配置）"""
    global _llm_semaphore
    if _llm_semaphore is None:
        # max_concurrent_llm 来自配置，默认 5 —— 同时最多 5 个 LLM 调用在飞
        _llm_semaphore = asyncio.Semaphore(get_config().max_concurrent_llm)
    return _llm_semaphore


class AgentEngine:
    """
    Agent 核心引擎。

    一次对话的完整流程（_execute 方法里）：
        1. 意图识别  —— 这条问题是 查数据库 / 查日志 / 闲聊？
        2. 选 Skill  —— 根据意图筛出相关的 Skill，摊平成 Tool 列表
        3. 组装 Prompt —— system + few-shot + schema + 历史对话
        4. 跑 Agent —— LangChain 的 ReAct 循环，LLM 边想边调工具
        5. 解析输出 —— 从最终回答里抠出 SQL（如果是 NL2SQL 意图）
    """

    def __init__(self):
        """构造期完成的事：选 LLM 厂商 + 实例化各个子模块（意图器/检索器/组装器）"""
        cfg = get_config()
        # LLM 厂商可在配置里切换：deepseek（线上）/ ollama（本地白嫖）
        if cfg.llm_provider == "deepseek":
            if not cfg.deepseek_api_key:
                raise RuntimeError(
                    "AGENT_DEEPSEEK_API_KEY is not set. "
                    "Get one at https://platform.deepseek.com/api_keys"
                )
            # DeepSeek 走 OpenAI 兼容协议，直接复用 ChatOpenAI，只是换 base_url
            self.llm = ChatOpenAI(
                model=cfg.deepseek_model,
                temperature=cfg.llm_temperature,    # 0 = 最确定，越高越发散
                api_key=cfg.deepseek_api_key,
                base_url=cfg.deepseek_base_url,     # https://api.deepseek.com
                timeout=120,                        # LLM 响应慢，给 2 分钟
            )
            logger.info(f"LLM: DeepSeek ({cfg.deepseek_model})")
        else:
            # Ollama 本地推理，无 API key，开发期没网也能跑
            self.llm = ChatOllama(
                model=cfg.ollama_model,
                temperature=cfg.llm_temperature,
                base_url=cfg.ollama_base_url,
            )
            logger.info(f"LLM: Ollama ({cfg.ollama_model})")

        # 两个子模块共享同一个 self.llm 实例（意图识别也用 LLM，少花一次实例化成本）
        self.intent_recognizer = IntentRecognizer(self.llm)
        self.context_assembler = ContextAssembler()

    # ------------------------------------------------------------------
    async def run(self, request: ChatRequest) -> ChatResponse:
        """对外入口。用信号量包一层，保证并发上限。"""
        # async with 进入时尝试拿信号量，超过上限就 await 排队（不会阻塞 event loop）
        async with _get_semaphore():
            return await self._execute(request)

    # ------------------------------------------------------------------
    async def _execute(self, request: ChatRequest) -> ChatResponse:
        """单次对话的完整 6 步流水线。"""
        try:
            # ========== Step 1. 意图识别 ==========
            # 如果调用方已经预判好意图（intent_hint），直接用，省一次 LLM 调用
            # 否则跑一次 IntentRecognizer（一次轻量 LLM 调用，返回 JSON）
            if request.intent_hint:
                intent = request.intent_hint
            else:
                ir = await self.intent_recognizer.recognize(
                    request.question, request.conversation_history or []
                )
                intent = ir["intent"]                       # nl2sql / log_analysis / general

            # ========== Step 2. 根据意图筛选 Skill，摊平成 Tool 列表 ==========
            # 例：intent="nl2sql" → 拿到 NL2SqlSkill → 它的 get_tools() 返回 4 个 SQL 相关 tool
            active_skills = SkillRegistry.get_skills_for_intent(intent)
            tools = []
            for s in active_skills:
                tools.extend(s.get_tools())     # 把每个 Skill 的 tool 列表全部摊平到一个大 list
            # 兜底：意图没匹配到任何 Skill 时，把所有启用的 Skill 工具一股脑给 LLM
            if not tools:
                tools = SkillRegistry.get_all_tools()

            # ========== Step 3. 组装 Prompt ==========
            # 把 system prompt + 意图专属 prompt + schema + 错误上下文 拼成一个 ChatPromptTemplate
            prompt = self.context_assembler.build_prompt(
                intent=intent,
                schema=request.schema,
                skills=active_skills,
                error_context=request.error_context,        # SQL 自纠错时回传上次错误
            )

            # ========== Step 4. 执行 Agent ==========
            # 把上层传来的"角色 + 内容"字典数组，转成 LangChain 的 HumanMessage/AIMessage 对象
            history = self._format_history(request.conversation_history)
            if tools:
                # ===== 有工具：跑 ReAct 循环（边想边调工具）=====
                # create_tool_calling_agent：把 llm / tools / prompt 三件套绑定成 Agent
                agent = create_tool_calling_agent(self.llm, tools, prompt)
                # AgentExecutor：实际驱动 ReAct 循环的执行器
                executor = AgentExecutor(
                    agent=agent,
                    tools=tools,
                    max_iterations=8,                # 最多 8 轮工具调用，防止死循环烧钱
                    verbose=True,                    # 打印中间思考过程，便于调试
                    handle_parsing_errors=True,      # LLM 输出格式错乱时不直接崩，自动重试
                )
                # ainvoke = async invoke，跑完整个 ReAct 循环
                result = await executor.ainvoke(
                    {"input": request.question, "chat_history": history}
                )
                answer = result["output"]            # LLM 最终回答
            else:
                # ===== 没工具：单轮直接问 LLM（一般是 general 闲聊场景）=====
                msgs = prompt.format_messages(
                    input=request.question,
                    chat_history=history,
                    agent_scratchpad=[],             # 没工具就没思考草稿，传空 list
                )
                resp = await self.llm.ainvoke(msgs)
                answer = resp.content

            # ========== Step 5. 从回答里抠 SQL（仅 NL2SQL 意图）==========
            # LLM 输出是一段文本，里面同时含 "标准 SQL" 和 "直观 SQL"两个代码块，
            # 这里用正则解析出来，分别给 Java 后端执行（标准）和前端展示（直观）
            sql, display_sql = (None, None)
            if intent == "nl2sql":
                sql, display_sql = self._extract_sqls(answer)

            return ChatResponse(
                answer=answer,
                intent=intent,
                sql=sql,                            # 给 Java 后端拿去真正执行的 SQL
                display_sql=display_sql,            # 给前端展示的中文别名版 SQL
                confidence=0.9,                     # 置信度（目前是固定值，可改成意图识别返回的真实值）
            )
        except Exception as e:
            # 任何阶段出错都兜底返回错误响应，避免 500
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
    def _extract_sqls(text: str) -> tuple[Optional[str], Optional[str]]:
        """
        Returns (standard_sql, display_sql).
        标准 SQL = 用于执行（纯英文字段）
        直观 SQL = 给用户看（带中文别名）
        """
        # 优先：按 "标准 SQL" / "直观 SQL" 标题定位代码块
        std = AgentEngine._extract_labeled_sql(text, ["标准 SQL", "标准SQL", "Standard SQL"])
        disp = AgentEngine._extract_labeled_sql(text, ["直观 SQL", "直观SQL", "Readable SQL", "友好 SQL"])

        # 兜底：抓所有 ```sql 代码块；第一段当标准，第二段当直观
        if std is None or disp is None:
            blocks = re.findall(r"```sql\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
            if blocks:
                if std is None:
                    std = blocks[0].strip()
                if disp is None and len(blocks) >= 2:
                    disp = blocks[1].strip()

        # 再兜底：裸 SELECT
        if std is None:
            m = re.search(r"(SELECT\s+.+?;)", text, re.DOTALL | re.IGNORECASE)
            if m:
                std = m.group(1).strip()

        # 如果只解出一份，用同一份兜底另一份
        if std and not disp:
            disp = std
        if disp and not std:
            std = disp

        return std, disp

    @staticmethod
    def _extract_labeled_sql(text: str, labels: list) -> Optional[str]:
        for lbl in labels:
            pattern = re.escape(lbl) + r".*?```sql\s*(.*?)\s*```"
            m = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None


# ---------------- 单例模式 ----------------
# AgentEngine 构造代价较高（要初始化 LLM 客户端、连接 ChromaDB 等），
# 整个进程共用同一个实例即可，不必每次请求都新建。
_engine = None  # type: Optional[AgentEngine]


def get_engine() -> AgentEngine:
    """FastAPI 的依赖注入会调这个函数；首次调用时实例化，之后直接复用。"""
    global _engine
    if _engine is None:
        _engine = AgentEngine()
    return _engine
