"""
Prompt 上下文组装器 —— 把各种信息片段拼成一个完整的 ChatPromptTemplate。

为什么需要它：
    一个完整的 prompt 包含很多部分，且每种意图组合不同：
        - 通用 system prompt（永远有）
        - 意图专属 prompt（nl2sql / log_analysis 各一份）
        - 数据库 schema（仅 nl2sql 用）
        - 错误上下文（仅 SQL 自纠错时有）
        - 对话历史（多轮对话）
        - agent_scratchpad（LangChain ReAct 内部用的思考草稿）
    把这些组合逻辑集中到一个类里，避免散在各处。
"""
from typing import Optional, List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.prompts import PromptManager


class ContextAssembler:
    def build_prompt(
        self,
        intent: str,
        schema: Optional[dict] = None,
        skills: Optional[list] = None,
        error_context: Optional[dict] = None,
    ) -> ChatPromptTemplate:
        """
        组装完整 prompt 的核心方法。
        返回 LangChain 标准的 ChatPromptTemplate，可以直接喂给 create_tool_calling_agent。
        """
        # ---------- 1. 构造可用技能描述 ----------
        # 让 LLM 知道当前有哪些 Skill 可用（这是给"人看"的概述，真正的工具调用还是看 Tool 列表）
        skill_desc = ""
        if skills:
            skill_desc = "\n".join(f"- {s.name}: {s.description}" for s in skills)

        # ---------- 2. 渲染基础 system prompt ----------
        # PromptManager 加载 prompts/templates/system.yaml，把 {available_skills} 占位符填上
        system = PromptManager.render(
            "system", available_skills=skill_desc or "暂无可用技能"
        )

        # ---------- 3. 按意图追加专属 prompt ----------
        if intent == "nl2sql" and schema:
            # NL2SQL：把数据库 schema 格式化成 markdown 表格塞进 prompt
            schema_text = self._format_schema(schema)
            nl2sql_prompt = PromptManager.render(
                "nl2sql/generate", schema_summary=schema_text
            )
            system += f"\n\n{nl2sql_prompt}"

            # SQL 自纠错：如果上次执行失败，把"上次的 SQL + 错误信息"喂回去让 LLM 修
            # 这是 Java 层 SqlExecutionService 报错后，回调本服务时回传的字段
            if error_context:
                error_prompt = PromptManager.render(
                    "nl2sql/error_fix",
                    failed_sql=error_context.get("previousSql", ""),
                    error_message=error_context.get("errorMessage", ""),
                )
                system += f"\n\n{error_prompt}"

        elif intent == "log_analysis":
            # 日志分析：纯指令式 prompt（具体日志数据通过 Tool 调用拿到）
            log_prompt = PromptManager.render("log_analysis/analyze")
            system += f"\n\n{log_prompt}"

        # ---------- 4. 拼成 ChatPromptTemplate ----------
        # 这是 LangChain Agent 标准的"四件套"结构：
        #   system          —— 角色定义 + 规则 + 上下文
        #   chat_history    —— 占位符，运行时填入多轮历史
        #   human           —— 占位符 {input}，当前问题
        #   agent_scratchpad —— ReAct 循环里 LLM 自己的思考草稿（工具调用 + observation 回写）
        return ChatPromptTemplate.from_messages(
            [
                ("system", system),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder("agent_scratchpad"),
            ]
        )

    # ------------------------------------------------------------------
    def _format_schema(self, schema: dict) -> str:
        """
        把 Java 后端通过 INFORMATION_SCHEMA 提取的库表结构，
        格式化成 LLM 友好的 markdown：
            ### 表: orders (订单表)
              - id (BIGINT, NOT NULL) -- 订单ID
              - customer_id (BIGINT, NOT NULL) -- 客户ID
              ...
        """
        if not schema or "tables" not in schema:
            return "无可用数据库结构信息"
        lines: list[str] = []
        for table in schema["tables"]:
            name = table.get("name", "")
            comment = table.get("comment", "")
            lines.append(f"\n### 表: {name} ({comment})")
            for col in table.get("columns", []):
                nullable = "NULL" if col.get("nullable", True) else "NOT NULL"
                lines.append(
                    f"  - {col['name']} ({col['type']}, {nullable}) -- {col.get('comment', '')}"
                )
        return "\n".join(lines)
