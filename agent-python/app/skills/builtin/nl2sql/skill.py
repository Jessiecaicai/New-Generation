"""NL2SQL skill – natural language to SQL query generation."""
from app.skills.base import BaseSkill
from app.skills.builtin.nl2sql.sql_tools import (
    lookup_schema_tool,
    list_tables_tool,
    sample_data_tool,
    validate_sql_tool,
)


class NL2SqlSkill(BaseSkill):
    name = "nl2sql"
    description = "将自然语言转换为SQL查询并执行，支持查表结构、生成SQL、语法校验"
    intent_tags = ["nl2sql"]
    enabled = True

    def get_tools(self):
        return [lookup_schema_tool, list_tables_tool, sample_data_tool, validate_sql_tool]
