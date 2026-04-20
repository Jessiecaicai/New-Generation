"""Lightweight intent classification using LLM."""
import json
import logging
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

INTENT_SYSTEM_PROMPT = """你是一个意图分类器。根据用户的问题，判断其意图类别。

可选意图：
- nl2sql: 用户想查询数据库中的数据（涉及查询、统计、报表、销售额、客户、订单等）
- knowledge_qa: 用户想问知识库中的文档内容（涉及文档、资料、规范、手册等）
- log_analysis: 用户想分析系统日志或排查错误（涉及日志、报错、异常、故障等）
- general: 一般性对话或无法归类的问题

请以 JSON 格式返回：{"intent": "xxx", "needs_rag": true/false, "confidence": 0.9}
只返回 JSON，不要其他文字。"""


class IntentRecognizer:
    def __init__(self, llm):
        self.llm = llm

    async def recognize(self, question: str, history: list) -> dict:
        """Classify user intent with a single fast LLM call."""
        try:
            messages = [
                SystemMessage(content=INTENT_SYSTEM_PROMPT),
                HumanMessage(content=f"用户问题: {question}"),
            ]
            response = await self.llm.ainvoke(messages)
            text = response.content.strip()
            # Handle possible markdown wrapping
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            result = json.loads(text.strip())
            logger.info(f"Intent recognized: {result}")
            return result
        except Exception as e:
            logger.warning(f"Intent recognition failed: {e}, defaulting to general")
            return {"intent": "general", "needs_rag": False, "confidence": 0.5}
