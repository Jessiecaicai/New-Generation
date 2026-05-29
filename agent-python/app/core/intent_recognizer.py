"""
意图识别器 —— 用一次轻量 LLM 调用判断"用户想干什么"。

作用：路由前置。Agent 不可能把所有工具都喂给 LLM（费 token、降准确率），
所以先用便宜快速的 LLM 调用做"意图分类"，再根据意图筛选对应的 Skill / Tool。

类比：餐厅前台先问"您是来吃饭还是开会"，再带你去不同区域。
"""
import json
import logging
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

# ============ 意图分类的 system prompt ============
# 这是个零样本（zero-shot）分类提示词，全靠 LLM 的语义理解能力。
# 让 LLM 输出 JSON 而不是自然语言，方便代码解析。
# 让 LLM 输出 JSON 而不是自然语言，方便代码解析。
INTENT_SYSTEM_PROMPT = """你是一个意图分类器。根据用户的问题，判断其意图类别。

可选意图：
- nl2sql: 用户想查询数据库中的数据（涉及查询、统计、报表、销售额、客户、订单等）
- log_analysis: 用户想分析系统日志或排查错误（涉及日志、报错、异常、故障等）
- general: 一般性对话或无法归类的问题

请以 JSON 格式返回：{"intent": "xxx", "confidence": 0.9}
只返回 JSON，不要其他文字。"""


class IntentRecognizer:
    def __init__(self, llm):
        # 复用 AgentEngine 的同一个 LLM 实例，省一次客户端初始化
        self.llm = llm

    async def recognize(self, question: str, history: list) -> dict:
        """
        分类用户意图，返回 {"intent": str, "confidence": float}

        注意：history 参数目前没用到——可优化空间是把对话历史也喂进去，
        让 LLM 结合上下文判断意图（比如"那帮我导出一下"在不同上下文里意图不同）。
        """
        try:
            # 一次 LLM 调用：system 给规则 + human 给问题
            messages = [
                SystemMessage(content=INTENT_SYSTEM_PROMPT),
                HumanMessage(content=f"用户问题: {question}"),
            ]
            response = await self.llm.ainvoke(messages)
            text = response.content.strip()

            # 有些 LLM 喜欢把 JSON 包在 ```json ... ``` 代码块里，要剥掉
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            result = json.loads(text.strip())
            logger.info(f"Intent recognized: {result}")
            return result
        except Exception as e:
            # LLM 输出格式错乱 / 网络挂了 / JSON 解析失败 —— 都兜底成 general
            # 这样不会因为意图识别挂掉就让整个对话流程崩溃
            logger.warning(f"Intent recognition failed: {e}, defaulting to general")
            return {"intent": "general", "confidence": 0.5}
