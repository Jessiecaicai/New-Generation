"""
NL2SQL MCP Server (Python 版)
─────────────────────────────────────────────────────────────────
把 NL2SQL 能力包装成符合 Model Context Protocol 的独立服务，
让 Claude Desktop / Cursor / Cline 等 MCP client 能直接调用。

暴露 5 个工具:
   1. list_tables        - 列出业务数据库所有表
   2. lookup_schema      - 查看指定表的字段结构
   3. sample_data        - 获取指定表的前 N 行示例数据
   4. validate_sql       - 校验 SQL 是否合法(只允许 SELECT)
   5. execute_select_sql - 真执行 SELECT 并返回结果

安全设计:
   - 仅允许 SELECT 查询(黑名单关键字检查)
   - 所有查询自动加 LIMIT 兜底(防 LLM 全表扫描)
   - 业务库通常应当用只读账号(本地开发图省事用 root)

协议: MCP over stdio, JSON-RPC 2.0
   - stdin: client 发请求过来
   - stdout: server 发响应回去  ⚠️ 所以 print() / stdout 输出都不能用!
   - stderr: 日志走这里(client 不读 stderr)
─────────────────────────────────────────────────────────────────
"""
import os
import re
import json
import sys
from typing import Optional

import aiomysql
from mcp.server.fastmcp import FastMCP


# ============ 配置(全部从环境变量读，方便 Claude Desktop 配置)============
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "rootpass")
DB_NAME = os.getenv("MYSQL_DATABASE", "business_db")
# 默认 LIMIT 兜底，防止 LLM 写出全表扫描的 SQL
MAX_ROWS = int(os.getenv("MAX_ROWS", "100"))


# ============ MySQL 连接池(进程级别共享)============
# 用 Optional + 懒加载：第一次工具被调用时才建池，避免 import 时连库
_pool: Optional[aiomysql.Pool] = None


async def get_pool() -> aiomysql.Pool:
    """懒加载连接池。同进程内复用同一个池，避免每次 query 新建连接。"""
    global _pool
    if _pool is None:
        _pool = await aiomysql.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME,
            minsize=1,
            maxsize=5,
            charset="utf8mb4",     # 跟 MySQL 容器配置一致，防止中文乱码
            autocommit=True,        # 我们只读，不需要事务
        )
    return _pool


# ============ SQL 安全校验(对应原 TS 版的 validateSqlString) ============
# 这些关键字一旦出现就拒绝，相当于业务库的"白名单只读"安全网
DANGEROUS_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
    "TRUNCATE", "CREATE", "GRANT", "REVOKE", "REPLACE",
]


def validate_sql_string(sql: str) -> tuple[bool, str]:
    """
    校验 SQL 是否安全。返回 (是否通过, 说明消息).

    三层检查:
      1. 必须以 SELECT 或 WITH 开头(WITH 是 CTE 前缀)
      2. 不能包含黑名单关键字(用 \\b 单词边界匹配，避免误伤
         'updated_at' / 'is_deleted' 这类列名)
      3. 建议加 LIMIT(只警告，不阻止；执行层会强制加 LIMIT 兜底)
    """
    cleaned = sql.strip().rstrip(";").strip()
    if not cleaned:
        return False, "错误: SQL 为空"

    upper = cleaned.upper()

    # 检查 1: 必须 SELECT / WITH 开头
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        return False, "错误: 只允许 SELECT 查询(或以 WITH 开头的 CTE)"

    # 检查 2: 黑名单关键字。re.IGNORECASE + \b 单词边界,
    # 避免 'updated_at' 列名里的 'update' 被误判
    for kw in DANGEROUS_KEYWORDS:
        if re.search(rf"\b{kw}\b", cleaned, re.IGNORECASE):
            return False, f"错误: 检测到危险关键字 '{kw}'"

    # 检查 3: 建议 LIMIT(警告级,不拦截)
    if "LIMIT" not in upper:
        return True, "警告: 建议添加 LIMIT 子句(执行时会自动限制返回行数)。其他方面语法正确。"

    return True, "验证通过: SQL 语法正确,是安全的 SELECT 查询。"


# ============ 创建 MCP server 实例 ============
# FastMCP 是 mcp Python SDK 的高级 API:
#   - @mcp.tool() 装饰器自动从函数签名 + docstring 生成 JSON Schema 给 LLM 用
#   - mcp.run() 起 stdio transport
# "nl2sql-mcp-server" 这个 name 会显示在 Claude Desktop 的工具面板里
mcp = FastMCP("nl2sql-mcp-server")


# ============ Tool 1: list_tables ============
@mcp.tool()
async def list_tables() -> str:
    """列出业务数据库 business_db 中所有可用的表(含注释和行数)。

    在用户问数据查询相关问题时,先调这个工具看有哪些表。
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """
                SELECT TABLE_NAME, TABLE_COMMENT, TABLE_ROWS
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
                """,
                (DB_NAME,),
            )
            rows = await cur.fetchall()

    if not rows:
        return f"数据库 {DB_NAME} 下没有任何表。"

    lines = [f"数据库 {DB_NAME} 的表列表:", ""]
    for r in rows:
        comment = r["TABLE_COMMENT"] or "(无注释)"
        lines.append(f"- {r['TABLE_NAME']}: {comment} (约 {r['TABLE_ROWS']} 行)")
    return "\n".join(lines)


# ============ Tool 2: lookup_schema ============
@mcp.tool()
async def lookup_schema(table_name: str) -> str:
    """查看指定表的详细结构(列名、类型、是否可空、主键、注释)。

    在生成 SQL 前调用此工具了解表结构。

    Args:
        table_name: 要查看的表名,例如 'customers' 或 'orders'
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """
                SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_COMMENT
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
                """,
                (DB_NAME, table_name),
            )
            rows = await cur.fetchall()

    if not rows:
        return f"表 '{table_name}' 在数据库 {DB_NAME} 中不存在。"

    lines = [f"表: {table_name}", "─" * 70]
    for r in rows:
        nullable = "NULL    " if r["IS_NULLABLE"] == "YES" else "NOT NULL"
        if r["COLUMN_KEY"] == "PRI":
            key = "[PK]"
        elif r["COLUMN_KEY"] == "UNI":
            key = "[UQ]"
        else:
            key = "    "
        comment = f" -- {r['COLUMN_COMMENT']}" if r["COLUMN_COMMENT"] else ""
        # 24/20 是 column 对齐的列宽
        lines.append(
            f"  {r['COLUMN_NAME']:<24} {r['COLUMN_TYPE']:<20} {nullable} {key}{comment}"
        )
    return "\n".join(lines)


# ============ Tool 3: sample_data ============
@mcp.tool()
async def sample_data(table_name: str, limit: int = 5) -> str:
    """获取指定表的前几行示例数据,帮助理解数据格式和取值范围。

    Args:
        table_name: 要查看示例数据的表名
        limit: 返回行数(1-20,默认 5)
    """
    # ⚠️ SQL 注入防护:
    # 表名不能用参数化(%s)传 —— 参数化只能传"值",不能传"标识符"。
    # 所以表名必须自己白名单校验:只允许 [字母_数字] 且首字符不是数字。
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
        return f"错误: 非法的表名 '{table_name}'"

    # 数值范围 clamp 到 1-20,防止恶意传 limit=999999
    safe_limit = max(1, min(limit, 20))

    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # 表名用 f-string 拼接(已经白名单校验过),limit 走参数化
            await cur.execute(
                f"SELECT * FROM `{table_name}` LIMIT %s",
                (safe_limit,),
            )
            rows = await cur.fetchall()

    if not rows:
        return f"表 {table_name} 暂无数据"

    # ensure_ascii=False:让中文直接显示,不转 \uXXXX
    # default=str:datetime / Decimal 这类不能直接 JSON 化的对象用 str() 兜底
    return (
        f"表 {table_name} 的前 {len(rows)} 行数据:\n"
        + json.dumps(rows, ensure_ascii=False, indent=2, default=str)
    )


# ============ Tool 4: validate_sql ============
@mcp.tool()
async def validate_sql(sql: str) -> str:
    """校验 SQL 语句是否安全(只允许 SELECT,禁止 DROP/DELETE/UPDATE 等)。

    在 execute_select_sql 之前可以用这个工具预校验。

    Args:
        sql: 要校验的 SQL 语句
    """
    _, message = validate_sql_string(sql)
    return message


# ============ Tool 5: execute_select_sql ============
@mcp.tool()
async def execute_select_sql(sql: str) -> str:
    """执行 SELECT 查询并返回结果。会先做安全校验,自动加 LIMIT 兜底。

    这是最终拿数据的工具。

    Args:
        sql: 要执行的 SELECT SQL
    """
    ok, message = validate_sql_string(sql)
    if not ok:
        return message  # 校验没过直接退,不执行

    # 强制加 LIMIT 兜底(LLM 经常写忘)
    final_sql = sql.strip().rstrip(";").strip()
    if "LIMIT" not in final_sql.upper():
        final_sql += f" LIMIT {MAX_ROWS}"

    pool = await get_pool()
    try:
        async with pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(final_sql)
                rows = await cur.fetchall()

        if not rows:
            return "查询执行成功,但没有返回任何行。"
        return (
            f"查询执行成功,返回 {len(rows)} 行:\n\n"
            + json.dumps(rows, ensure_ascii=False, indent=2, default=str)
        )
    except Exception as e:
        # 异常消息回给 LLM,它可以根据错误自己改 SQL 重试(项目的"自纠错"机制)
        return f"SQL 执行失败: {e}"


# ============ 启动入口 ============
if __name__ == "__main__":
    # 日志走 stderr(不能用 print!print 写到 stdout,会污染 MCP 协议)
    print(
        f"[nl2sql-mcp-server] starting, db={DB_HOST}:{DB_PORT}/{DB_NAME}",
        file=sys.stderr,
    )
    # mcp.run() 会:
    #   1. 启动 stdio transport
    #   2. 监听 stdin 上的 JSON-RPC 请求
    #   3. 把响应写到 stdout
    # 直到 client 关闭 stdin(EOF),进程结束
    mcp.run()
