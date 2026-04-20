"""LangChain tools for knowledge-base QA."""
import logging
from langchain_core.tools import tool
from app.rag.vector_store import VectorStoreManager

logger = logging.getLogger(__name__)


@tool
def search_knowledge(query: str, knowledge_base: str = "default", top_k: int = 5) -> str:
    """在知识库中语义搜索相关内容。

    Args:
        query: 搜索查询
        knowledge_base: 知识库名称
        top_k: 返回结果数
    """
    try:
        vs = VectorStoreManager()
        results = vs.query(knowledge_base, query, top_k=top_k)
        if not results:
            return "未在知识库中找到相关内容"
        lines = [f"找到 {len(results)} 条相关内容:"]
        for i, r in enumerate(results, 1):
            src = r.metadata.get("source", "未知")
            lines.append(f"\n--- 结果{i} (来源: {src}, 相关度: {1-r.score:.2f}) ---")
            lines.append(r.text)
        return "\n".join(lines)
    except Exception as e:
        return f"知识库搜索失败: {e}"


@tool
def get_document(file_name: str, knowledge_base: str = "default") -> str:
    """获取知识库中指定文档的内容片段。

    Args:
        file_name: 文档文件名
        knowledge_base: 知识库名称
    """
    try:
        vs = VectorStoreManager()
        coll = vs.get_or_create_collection(knowledge_base)
        results = coll.get(where={"source": file_name}, limit=20)
        if not results["documents"]:
            return f"未找到文档: {file_name}"
        lines = [f"文档 '{file_name}' ({len(results['documents'])} 个片段):"]
        for i, doc in enumerate(results["documents"]):
            lines.append(f"\n--- 片段{i+1} ---\n{doc}")
        return "\n".join(lines)
    except Exception as e:
        return f"获取文档失败: {e}"


search_knowledge_tool = search_knowledge
get_document_tool = get_document
