"""LangChain tools for log analysis – calls Java backend APIs."""
from typing import Optional
import logging
import httpx
from langchain_core.tools import tool
from app.config import get_config

logger = logging.getLogger(__name__)


def _java_get(path: str, params: Optional[dict] = None) -> dict:
    base = get_config().java_backend_url.rstrip("/")
    try:
        r = httpx.get(f"{base}{path}", params=params, timeout=10.0)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"Java API error: {e}")
        return {"error": str(e)}


@tool
def search_logs(level: str = "ERROR", keyword: str = "", limit: int = 20) -> str:
    """搜索系统日志，可按级别和关键词筛选。

    Args:
        level: 日志级别 (INFO/WARN/ERROR/FATAL)
        keyword: 搜索关键词
        limit: 返回条数
    """
    data = _java_get("/api/logs", {"level": level, "keyword": keyword, "size": limit})
    if "error" in data:
        return f"查询失败: {data['error']}"
    logs = data.get("content", [])
    if not logs:
        return f"未找到 {level} 级别的日志"
    lines = [f"找到 {len(logs)} 条 {level} 日志:"]
    for lg in logs:
        lines.append(f"  [{lg.get('createdAt','')}] [{lg.get('serviceName','')}] {lg.get('message','')[:200]}")
    return "\n".join(lines)


@tool
def get_error_stats(hours: int = 24) -> str:
    """获取最近N小时的错误统计。

    Args:
        hours: 统计时间范围（小时）
    """
    data = _java_get("/api/logs/stats", {"hours": hours})
    if "error" in data:
        return f"获取统计失败: {data['error']}"
    return (
        f"最近 {hours} 小时日志统计:\n"
        f"  ERROR: {data.get('errorCount',0)} 条\n"
        f"  WARN: {data.get('warnCount',0)} 条\n"
        f"  未处理: {data.get('unresolvedCount',0)} 条\n"
        f"  分类: {data.get('categoryStats',{})}"
    )


@tool
def get_log_context(log_id: str) -> str:
    """获取指定日志的上下文（前后相关日志），用于根因分析。

    Args:
        log_id: 日志条目ID
    """
    data = _java_get(f"/api/logs/{log_id}/context")
    if "error" in data:
        return f"获取上下文失败: {data['error']}"
    lines = ["日志上下文:"]
    for lg in data.get("context", []):
        marker = ">>>" if str(lg.get("id")) == str(log_id) else "   "
        lines.append(f"{marker} [{lg.get('createdAt','')}] [{lg.get('logLevel','')}] {lg.get('message','')[:200]}")
    stack = data.get("stackTrace", "")
    if stack:
        lines.append(f"\n堆栈:\n{stack[:1000]}")
    return "\n".join(lines)


search_logs_tool = search_logs
get_error_stats_tool = get_error_stats
get_log_context_tool = get_log_context
