"""Base class for all pluggable Skills."""
from abc import ABC, abstractmethod
from langchain_core.tools import StructuredTool


class BaseSkill(ABC):
    name: str = ""
    description: str = ""
    intent_tags: list[str] = []
    enabled: bool = True

    @abstractmethod
    def get_tools(self) -> list[StructuredTool]:
        """Return the LangChain tools provided by this skill."""
        ...

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "intent_tags": self.intent_tags,
            "enabled": self.enabled,
            "tools": [t.name for t in self.get_tools()],
        }
