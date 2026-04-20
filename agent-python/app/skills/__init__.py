"""Skill registry – auto-discovers skills from builtin/ and custom/ packages."""
import importlib
import pkgutil
import logging
from app.skills.base import BaseSkill

logger = logging.getLogger(__name__)


class SkillRegistry:
    _skills: dict[str, BaseSkill] = {}
    _discovered: bool = False

    @classmethod
    def discover(cls):
        cls._skills.clear()
        cls._scan("app.skills.builtin")
        cls._scan("app.skills.custom")
        cls._discovered = True
        logger.info(f"Discovered {len(cls._skills)} skills: {list(cls._skills.keys())}")

    @classmethod
    def _scan(cls, package_name: str):
        try:
            pkg = importlib.import_module(package_name)
        except ImportError:
            logger.debug(f"Package {package_name} not found, skipping")
            return
        for _imp, modname, _ispkg in pkgutil.walk_packages(
            pkg.__path__, prefix=package_name + "."
        ):
            try:
                module = importlib.import_module(modname)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseSkill)
                        and attr is not BaseSkill
                        and getattr(attr, "name", "")
                    ):
                        try:
                            inst = attr()
                            if inst.name and inst.name not in cls._skills:
                                cls._skills[inst.name] = inst
                        except Exception as e:
                            logger.warning(f"Cannot instantiate {attr_name}: {e}")
            except Exception as e:
                logger.warning(f"Cannot import {modname}: {e}")

    # --- public API ---------------------------------------------------
    @classmethod
    def get_skills_for_intent(cls, intent: str) -> list[BaseSkill]:
        if not cls._discovered:
            cls.discover()
        return [s for s in cls._skills.values() if intent in s.intent_tags and s.enabled]

    @classmethod
    def get_all_tools(cls):
        if not cls._discovered:
            cls.discover()
        tools = []
        for s in cls._skills.values():
            if s.enabled:
                tools.extend(s.get_tools())
        return tools

    @classmethod
    def get_all_skills(cls) -> list[BaseSkill]:
        if not cls._discovered:
            cls.discover()
        return list(cls._skills.values())

    @classmethod
    def toggle_skill(cls, name: str, enabled: bool) -> bool:
        if name in cls._skills:
            cls._skills[name].enabled = enabled
            return True
        return False

    @classmethod
    def reload(cls):
        cls._discovered = False
        cls.discover()
