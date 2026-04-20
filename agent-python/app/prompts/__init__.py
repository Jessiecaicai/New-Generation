"""Prompt template manager – loads YAML templates, renders with variables."""
from typing import Optional, Dict, List, Set
import logging
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class PromptManager:
    _templates: Dict[str, dict] = {}
    _loaded: bool = False

    @classmethod
    def load(cls, templates_dir: Optional[str] = None):
        if templates_dir is None:
            templates_dir = str(Path(__file__).parent / "templates")
        cls._templates.clear()
        base = Path(templates_dir)
        for yf in base.rglob("*.yaml"):
            try:
                data = yaml.safe_load(yf.read_text(encoding="utf-8"))
                if data and "name" in data:
                    key = str(yf.relative_to(base).with_suffix("")).replace("\\", "/")
                    cls._templates[key] = data
                    cls._templates[data["name"]] = data
            except Exception as e:
                logger.error(f"Failed to load {yf}: {e}")
        cls._loaded = True
        unique = len(set(id(v) for v in cls._templates.values()))
        logger.info(f"Loaded {unique} prompt templates")

    @classmethod
    def render(cls, name: str, **variables) -> str:
        if not cls._loaded:
            cls.load()
        tpl = cls._templates.get(name)
        if not tpl:
            logger.warning(f"Template '{name}' not found")
            return ""
        text = tpl.get("template", "")
        try:
            return text.format(**variables)
        except KeyError as e:
            logger.warning(f"Missing var {e} in '{name}'")
            return text

    @classmethod
    def get_template(cls, name: str) -> dict:
        if not cls._loaded:
            cls.load()
        return cls._templates.get(name, {})

    @classmethod
    def list_templates(cls) -> List[dict]:
        if not cls._loaded:
            cls.load()
        seen: Set[str] = set()
        result = []
        for data in cls._templates.values():
            n = data.get("name", "")
            if n and n not in seen:
                seen.add(n)
                result.append({"name": n, "version": data.get("version", ""), "description": data.get("description", "")})
        return result

    @classmethod
    def reload(cls):
        cls._loaded = False
        cls.load()
