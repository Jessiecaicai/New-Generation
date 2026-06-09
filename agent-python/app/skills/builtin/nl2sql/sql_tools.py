"""
NL2SQL Skill 的具体 Tool 实现 —— LLM 真正能调用的"工具箱"。

⚠️ 重要设计：所有工具都用 @tool 装饰器封装
    装饰器会自动从函数名 / docstring / 类型注解里提取出：
        - tool name             ← 函数名
        - tool description      ← docstring 首行
        - args schema (JSON Schema) ← 参数类型注解 + Args: 段
    并打包成 LangChain 的 StructuredTool 对象，最终让 LLM 通过 tool calling 协议调用。

⚠️ 数据流：
    Java 后端通过 /chat 请求把 schema 传进来 → routers 调 set_schema_context 注入 →
    Tool 函数从 contextvar 读 → 返回给 LLM
    （为什么用 contextvar 不用全局变量：高并发下不同请求的 schema 不能互相污染）
"""
import contextvars
import json
import sqlparse                            # SQL 解析库，用于语法校验
from langchain_core.tools import tool


# ============ 每请求级别的 schema 上下文 ============
# contextvar 是 Python 3.7+ 提供的"协程/线程局部变量"，
# 在 asyncio 环境下能保证每个请求看到自己的值，不会互相干扰。
# 这里用它在"请求入口"和"工具调用"之间传递 schema，不污染函数签名。
_schema_ctx = contextvars.ContextVar("schema_ctx", default=None)


def set_schema_context(schema: dict):
    """请求入口处调用：把当前请求的数据库 schema 塞进 contextvar"""
    _schema_ctx.set(schema)


def get_schema_context() -> dict:
    """工具内部读取当前请求的 schema"""
    return _schema_ctx.get() or {}


# ============================================================
# Tool 1: list_tables —— "我有哪些表？"
# ============================================================
@tool
def list_tables() -> str:
    """列出数据库中所有可用的表名及其描述。在不确定使用哪些表时调用此工具。"""
    # ↑ 这段 docstring 会被 LangChain 提取出来给 LLM 看，
    #   LLM 通过这段描述判断"什么时候应该调用这个工具"
    schema = get_schema_context()
    if not schema or "tables" not in schema:
        return "暂无数据库结构信息"
    lines = []
    for t in schema["tables"]:
        # 输出格式：- 表名: 注释 (列数)
        lines.append(f"- {t.get('name','')}: {t.get('comment','')} ({len(t.get('columns',[]))} 列)")
    return "\n".join(lines)


# ============================================================
# Tool 2: lookup_schema —— "某张表的详细结构是什么？"
# ============================================================
@tool
def lookup_schema(table_name: str) -> str:
    """查看指定表的详细结构（列名、类型、是否可空、注释）。

    Args:
        table_name: 要查看的表名
    """
    # ↑ Args: 段也会被 LangChain 解析，对应到 JSON Schema 的参数描述
    schema = get_schema_context()
    if not schema or "tables" not in schema:
        return "暂无数据库结构信息"
    for t in schema["tables"]:
        if t.get("name") == table_name:
            # 用对齐格式输出，让 LLM 更容易"看清楚"列对齐关系
            lines = [f"表: {table_name} ({t.get('comment','')})"]
            lines.append("-" * 60)
            for c in t.get("columns", []):
                null = "NULL" if c.get("nullable", True) else "NOT NULL"
                lines.append(f"  {c['name']:20s} {c['type']:15s} {null:8s} -- {c.get('comment','')}")
            return "\n".join(lines)
    return f"表 '{table_name}' 不存在"


# ============================================================
# Tool 3: sample_data —— "这张表里大概长什么样？"
# ============================================================
@tool
def sample_data(table_name: str) -> str:
    """查看指定表的前几行示例数据。

    Args:
        table_name: 要查看示例数据的表名
    """
    # 示例数据由 Java 后端的 SchemaService 预取（避免 Python 直连数据库），
    # 通过 schema 上下文一起带过来
    schema = get_schema_context()
    for t in (schema or {}).get("tables", []):
        if t.get("name") == table_name:
            samples = t.get("sample_data", [])
            if samples:
                # 输出成 JSON 而不是 markdown 表格 —— LLM 处理 JSON 更稳定
                return json.dumps(samples, ensure_ascii=False, indent=2)
            return f"表 '{table_name}' 暂无示例数据"
    return f"表 '{table_name}' 不存在"


# ============================================================
# Tool 4: validate_sql —— "我写的 SQL 对不对？"
# ============================================================
@tool
def validate_sql(sql: str) -> str:
    """验证SQL语法是否正确，检查是否为安全的SELECT查询。

    Args:
        sql: 要验证的SQL语句
    """
    # ⚠️ 这是【第一道安全防线】，Java 后端 SqlExecutionService 还会再校验一次（深度防御）
    # 这里挡掉明显错误，让 LLM 自己能 ReAct 修正，避免错的 SQL 流到执行层
    try:
        parsed = sqlparse.parse(sql)
        if not parsed:
            return "错误: SQL 为空或无法解析"

        # 校验 1：只允许 SELECT，杜绝写操作
        stmt_type = parsed[0].get_type()
        if stmt_type and stmt_type.upper() != "SELECT":
            return f"错误: 只允许 SELECT 查询，检测到 {stmt_type}"

        # 校验 2：黑名单关键字（兜底，防 sqlparse 误识别）
        upper = sql.upper()
        for kw in ("DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"):
            if kw in upper.split():
                return f"错误: 检测到危险关键字 '{kw}'"

        # 校验 3：建议加 LIMIT，避免大查询拖垮数据库
        if "LIMIT" not in upper:
            return "警告: 建议添加 LIMIT 子句。其他方面语法正确。"

        return "验证通过: SQL 语法正确，是安全的 SELECT 查询。"
    except Exception as e:
        return f"验证错误: {e}"


# ============ 对外导出（命名约定：xxx_tool） ============
# 给 skill.py import 用，名字带 _tool 后缀是为了和函数名区分一下
list_tables_tool = list_tables
lookup_schema_tool = lookup_schema
sample_data_tool = sample_data
validate_sql_tool = validate_sql
