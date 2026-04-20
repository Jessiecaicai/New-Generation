"""Skill and prompt management endpoints."""
import logging
from fastapi import APIRouter
from app.skills import SkillRegistry
from app.prompts import PromptManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/skills")


@router.get("/status")
async def status():
    return {"skills": [s.to_dict() for s in SkillRegistry.get_all_skills()]}


@router.put("/{name}/toggle")
async def toggle(name: str, enabled: bool = True):
    ok = SkillRegistry.toggle_skill(name, enabled)
    if ok:
        return {"message": f"Skill '{name}' {'enabled' if enabled else 'disabled'}"}
    return {"error": f"Skill '{name}' not found"}


@router.post("/reload")
async def reload():
    SkillRegistry.reload()
    PromptManager.reload()
    return {
        "message": "Reloaded",
        "skills": [s.to_dict() for s in SkillRegistry.get_all_skills()],
        "prompts": PromptManager.list_templates(),
    }


@router.get("/prompts")
async def prompts():
    return {"prompts": PromptManager.list_templates()}
