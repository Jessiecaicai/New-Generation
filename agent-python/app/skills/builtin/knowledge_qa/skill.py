"""Knowledge QA skill – RAG-based document question answering."""
from app.skills.base import BaseSkill
from app.skills.builtin.knowledge_qa.qa_tools import (
    search_knowledge_tool, get_document_tool,
)


class KnowledgeQaSkill(BaseSkill):
    name = "knowledge_qa"
    description = "基于知识库文档回答问题，支持语义检索和引用溯源"
    intent_tags = ["knowledge_qa"]
    enabled = True

    def get_tools(self):
        return [search_knowledge_tool, get_document_tool]
