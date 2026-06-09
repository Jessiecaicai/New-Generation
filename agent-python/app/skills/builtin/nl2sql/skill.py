"""
NL2SQL Skill —— 自然语言转 SQL 的能力包。

这个 Skill 本身不写业务逻辑，只负责"把 4 个 SQL 相关 Tool 打包注册"。
真正的工具实现在 sql_tools.py 里。

被 SkillRegistry.discover() 扫描到时会自动实例化、注册到全局表。
"""
from app.skills.base import BaseSkill
from app.skills.builtin.nl2sql.sql_tools import (
    lookup_schema_tool,    # 查指定表的列结构
    list_tables_tool,      # 列出所有表
    sample_data_tool,      # 查看表的示例数据
    validate_sql_tool,     # SQL 语法校验
)


class NL2SqlSkill(BaseSkill):
    name = "nl2sql"                                           # 唯一标识
    description = "将自然语言转换为SQL查询并执行，支持查表结构、生成SQL、语法校验"
    intent_tags = ["nl2sql"]                                  # 仅在意图 = nl2sql 时被激活
    enabled = True                                            # 默认启用

    def get_tools(self):
        # 返回的 4 个 tool 会被 AgentEngine 摊平进 tool 列表，喂给 LLM。
        # LLM 拿到这些工具的 name/description/参数 schema 后，自行决定调用顺序：
        #   典型路径：list_tables → lookup_schema → sample_data → 写 SQL → validate_sql
        return [lookup_schema_tool, list_tables_tool, sample_data_tool, validate_sql_tool]
