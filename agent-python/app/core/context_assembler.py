"""Assemble context from RAG results, schema, and prompts into a ChatPromptTemplate."""
from typing import Optional, List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.prompts import PromptManager


class ContextAssembler:
    def format_rag_results(self, results: list) -> str:
        """Format RAG retrieval results into readable text."""
        if not results:
            return ""
        sections = []
        for i, r in enumerate(results, 1):
            source = r.metadata.get("source", "未知来源")
            sections.append(f"[引用{i}] (来源: {source})\n{r.text}")
        return "\n\n".join(sections)

    def build_prompt(
        self,
        intent: str,
        rag_context: str = "",
        schema: Optional[dict] = None,
        skills: Optional[list] = None,
        error_context: Optional[dict] = None,
    ) -> ChatPromptTemplate:
        """Build the full ChatPromptTemplate for the agent."""
        # Skill descriptions
        skill_desc = ""
        if skills:
            skill_desc = "\n".join(f"- {s.name}: {s.description}" for s in skills)

        system = PromptManager.render(
            "system", available_skills=skill_desc or "暂无可用技能"
        )

        # Intent-specific additions
        if intent == "nl2sql" and schema:
            schema_text = self._format_schema(schema)
            nl2sql_prompt = PromptManager.render(
                "nl2sql/generate", schema_summary=schema_text
            )
            system += f"\n\n{nl2sql_prompt}"

            if error_context:
                error_prompt = PromptManager.render(
                    "nl2sql/error_fix",
                    failed_sql=error_context.get("previousSql", ""),
                    error_message=error_context.get("errorMessage", ""),
                )
                system += f"\n\n{error_prompt}"

        elif intent == "knowledge_qa" and rag_context:
            qa_prompt = PromptManager.render(
                "knowledge_qa/answer", rag_context=rag_context
            )
            system += f"\n\n{qa_prompt}"

        elif intent == "log_analysis":
            log_prompt = PromptManager.render("log_analysis/analyze")
            system += f"\n\n{log_prompt}"

        # Attach RAG context for other intents too
        if rag_context and intent != "knowledge_qa":
            system += f"\n\n## 参考资料（从知识库检索）\n{rag_context}"

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
