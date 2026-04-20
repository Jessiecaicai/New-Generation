"""Log analyzer skill – search, stats, context analysis."""
from app.skills.base import BaseSkill
from app.skills.builtin.log_analyzer.log_tools import (
    search_logs_tool, get_error_stats_tool, get_log_context_tool,
)


class LogAnalyzerSkill(BaseSkill):
    name = "log_analyzer"
    description = "分析系统日志，定位异常和错误根因，提供统计和趋势分析"
    intent_tags = ["log_analysis"]
    enabled = True

    def get_tools(self):
        return [search_logs_tool, get_error_stats_tool, get_log_context_tool]
