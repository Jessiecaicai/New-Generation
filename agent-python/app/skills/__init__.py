"""
Skill 注册中心 —— Agent 框架的"插件管理器"。

核心机制：启动时自动扫描 builtin/ 和 custom/ 两个目录，
找出所有继承了 BaseSkill 的类，实例化后注册到一个全局字典里。

这样加新 Skill 只需要：
    1. 在 builtin/ 或 custom/ 下新建一个目录
    2. 写一个继承 BaseSkill 的类
    3. 重启服务（或调 reload()），就自动被发现并注册

—— 不用改任何核心代码（开闭原则）
"""
import importlib   # 动态 import 模块
import pkgutil     # 遍历包内所有子模块
import logging
from app.skills.base import BaseSkill

logger = logging.getLogger(__name__)


class SkillRegistry:
    """全类方法的"全局注册表"（用类做单例，比单例对象更简洁）"""

    # 注册表：{ skill_name: skill_instance }，进程内只有一份
    _skills: dict[str, BaseSkill] = {}
    # 标记位：避免每次查询都重新扫描（懒加载 + 缓存）
    _discovered: bool = False

    @classmethod
    def discover(cls):
        """扫描所有 Skill 包，把找到的全部注册进来。"""
        cls._skills.clear()                          # 清空，支持重新加载
        cls._scan("app.skills.builtin")              # 内置 Skill：NL2SQL / KnowledgeQA / LogAnalyzer
        cls._scan("app.skills.custom")               # 用户自定义 Skill 目录（开放扩展）
        cls._discovered = True
        logger.info(f"Discovered {len(cls._skills)} skills: {list(cls._skills.keys())}")

    @classmethod
    def _scan(cls, package_name: str):
        """扫描指定包，找出里面所有 BaseSkill 子类并实例化。"""
        try:
            pkg = importlib.import_module(package_name)
        except ImportError:
            # 包不存在不算错，custom/ 目录可能是空的
            logger.debug(f"Package {package_name} not found, skipping")
            return

        # walk_packages 会递归遍历包内所有 .py 模块
        for _imp, modname, _ispkg in pkgutil.walk_packages(
            pkg.__path__, prefix=package_name + "."
        ):
            try:
                module = importlib.import_module(modname)
                # 遍历模块的所有顶层属性，挑出 BaseSkill 子类
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)                # 是个类（不是实例 / 函数）
                        and issubclass(attr, BaseSkill)       # 继承自 BaseSkill
                        and attr is not BaseSkill             # 排除基类本身
                        and getattr(attr, "name", "")         # 必须设置了 name 属性
                    ):
                        try:
                            inst = attr()                     # 实例化
                            # 同名 Skill 只注册第一个（防止 import 多次导致重复）
                            if inst.name and inst.name not in cls._skills:
                                cls._skills[inst.name] = inst
                        except Exception as e:
                            # 单个 Skill 加载失败不影响其他 Skill
                            logger.warning(f"Cannot instantiate {attr_name}: {e}")
            except Exception as e:
                logger.warning(f"Cannot import {modname}: {e}")

    # --- 对外 API（给 AgentEngine 用）---------------------------------
    @classmethod
    def get_skills_for_intent(cls, intent: str) -> list[BaseSkill]:
        """
        意图路由：根据用户意图筛出相关的 Skill。
        例：intent="nl2sql" → 返回 [NL2SqlSkill]（它的 intent_tags 包含 "nl2sql"）
        """
        if not cls._discovered:
            cls.discover()                                    # 懒加载
        # 双重过滤：意图匹配 + 该 Skill 处于启用状态
        return [s for s in cls._skills.values() if intent in s.intent_tags and s.enabled]

    @classmethod
    def get_all_tools(cls):
        """兜底：返回所有启用 Skill 的全部 Tool。意图没匹配到时用。"""
        if not cls._discovered:
            cls.discover()
        tools = []
        for s in cls._skills.values():
            if s.enabled:
                tools.extend(s.get_tools())
        return tools

    @classmethod
    def get_all_skills(cls) -> list[BaseSkill]:
        """给前端"技能管理"页面用的：列出所有 Skill 含禁用的"""
        if not cls._discovered:
            cls.discover()
        return list(cls._skills.values())

    @classmethod
    def toggle_skill(cls, name: str, enabled: bool) -> bool:
        """前端"技能开关"调的接口：启用/禁用某个 Skill。返回是否操作成功。"""
        if name in cls._skills:
            cls._skills[name].enabled = enabled
            return True
        return False

    @classmethod
    def reload(cls):
        """热加载：开发期改完 Skill 代码不重启服务，调一下这个就刷新注册表。"""
        cls._discovered = False
        cls.discover()
