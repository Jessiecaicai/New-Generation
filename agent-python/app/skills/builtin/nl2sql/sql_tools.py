"""LangChain tools for NL2SQL skill."""
import contextvars
import json
import sqlparse
from langchain_core.tools import tool

# Per-request schema injected via contextvar
_schema_ctx = contextvars.ContextVar("schema_ctx", default=None)


def set_schema_context(schema: dict):
    _schema_ctx.set(schema)


def get_schema_context() -> dict:
    return _schema_ctx.get() or {}


@tool
def list_tables() -> str:
    """列出数据库中所有可用的表名及其描述。在不确定使用哪些表时调用此工具。"""
    schema = get_schema_context()
    if not schema or "tables" not in schema:
        return "暂无数据库结构信息"
    lines = []
    for t in schema["tables"]:
        lines.append(f"- {t.get('name','')}: {t.get('comment','')} ({len(t.get('columns',[]))} 列)")
    return "\n".join(lines)


@tool
def lookup_schema(table_name: str) -> str:
    """查看指定表的详细结构（列名、类型、是否可空、注释）。

    Args:
        table_name: 要查看的表名
    """
    schema = get_schema_context()
    if not schema or "tables" not in schema:
        return "暂无数据库结构信息"
    for t in schema["tables"]:
        if t.get("name") == table_name:
            lines = [f"表: {table_name} ({t.get('comment','')})"]
            lines.append("-" * 60)
            for c in t.get("columns", []):
                null = "NULL" if c.get("nullable", True) else "NOT NULL"
                lines.append(f"  {c['name']:20s} {c['type']:15s} {null:8s} -- {c.get('comment','')}")
            return "\n".join(lines)
    return f"表 '{table_name}' 不存在"


@tool
def sample_data(table_name: str) -> str:
    """查看指定表的前几行示例数据。

    Args:
        table_name: 要查看示例数据的表名
    """
    schema = get_schema_context()
    for t in (schema or {}).get("tables", []):
        if t.get("name") == table_name:
            samples = t.get("sample_data", [])
            if samples:
                return json.dumps(samples, ensure_ascii=False, indent=2)
            return f"表 '{table_name}' 暂无示例数据"
    return f"表 '{table_name}' 不存在"


@tool
def validate_sql(sql: str) -> str:
    """验证SQL语法是否正确，检查是否为安全的SELECT查询。

    Args:
        sql: 要验证的SQL语句
    """
    try:
        parsed = sqlparse.parse(sql)
        if not parsed:
            return "错误: SQL 为空或无法解析"

        stmt_type = parsed[0].get_type()
        if stmt_type and stmt_type.upper() != "SELECT":
            return f"错误: 只允许 SELECT 查询，检测到 {stmt_type}"

        upper = sql.upper()
        for kw in ("DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"):
            if kw in upper.split():
                return f"错误: 检测到危险关键字 '{kw}'"

        if "LIMIT" not in upper:
            return "警告: 建议添加 LIMIT 子句。其他方面语法正确。"

        return "验证通过: SQL 语法正确，是安全的 SELECT 查询。"
    except Exception as e:
        return f"验证错误: {e}"


# Export
list_tables_tool = list_tables
lookup_schema_tool = lookup_schema
sample_data_tool = sample_data
validate_sql_tool = validate_sql
