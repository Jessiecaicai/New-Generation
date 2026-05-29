"""
Skill 抽象基类 —— 所有可插拔 Skill 都要继承它。

设计意图：把"业务能力"和"具体 Tool 函数"解耦
    - Skill = 一组相关 Tool 的业务分组（如 NL2SqlSkill 包含 4 个 SQL 相关 tool）
    - Tool  = 单个被 @tool 装饰的函数（LLM 能直接调用的最小单元）

LangChain 本身不知道 Skill 概念，Skill 是我们自己加的一层抽象，用于：
    1. 业务语义分组
    2. 整体启用/禁用
    3. 意图路由筛选
"""
from abc import ABC, abstractmethod
from langchain_core.tools import StructuredTool


class BaseSkill(ABC):
    # 子类必须覆盖这四个类属性 ↓

    name: str = ""                  # 唯一标识，例：'nl2sql'
    description: str = ""           # 给前端展示 + 给 LLM 看的能力描述
    intent_tags: list[str] = []     # 关联的意图标签；AgentEngine 按这个筛 Skill
    enabled: bool = True             # 是否启用，前端可通过 toggle 接口动态开关

    @abstractmethod
    def get_tools(self) -> list[StructuredTool]:
        """
        子类必须实现：返回该 Skill 提供的所有 LangChain Tool。
        这些 Tool 会被 AgentEngine 摊平进同一个工具列表喂给 LLM。
        """
        ...

    def to_dict(self) -> dict:
        """序列化成 dict，给 /api/skills 接口用，前端"技能管理"页面展示。"""
        return {
            "name": self.name,
            "description": self.description,
            "intent_tags": self.intent_tags,
            "enabled": self.enabled,
            "tools": [t.name for t in self.get_tools()],
        }
