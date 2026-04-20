"""Knowledge base management endpoints."""
import logging
from fastapi import APIRouter, UploadFile, File, Form
from app.config import get_config
from app.rag.knowledge_base import KnowledgeBaseManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/knowledge")
kb_manager = KnowledgeBaseManager()


@router.post("/upload")
async def upload_and_index(
    knowledge_base: str = Form(default="default"),
    files: list[UploadFile] = File(...),
):
    config = get_config()
    kb_dir = config.knowledge_upload_dir / knowledge_base
    kb_dir.mkdir(parents=True, exist_ok=True)

    saved = []
    for f in files:
        path = kb_dir / f.filename
        path.write_bytes(await f.read())
        saved.append(str(path))
        logger.info(f"Saved: {path}")

    return kb_manager.index_documents(knowledge_base, saved)


@router.post("/index")
async def index_documents(knowledge_base_name: str = Form(...), file_paths: str = Form(...)):
    paths = [p.strip() for p in file_paths.split(",") if p.strip()]
    return kb_manager.index_documents(knowledge_base_name, paths)


@router.delete("/{name}")
async def delete_kb(name: str):
    kb_manager.delete_knowledge_base(name)
    return {"message": f"Knowledge base '{name}' deleted"}


@router.get("/list")
async def list_kbs():
    return {"knowledge_bases": kb_manager.list_knowledge_bases()}
