"""FastAPI application entry point for New-Generation Agent Service."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_config
from app.skills import SkillRegistry
from app.prompts import PromptManager
from app.routers import chat_router, knowledge_router, skill_router
from app.middleware.exception_reporter import ExceptionReporterMiddleware
from app.middleware.rate_limiter import RateLimiterMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    config = get_config()
    logging.basicConfig(level=getattr(logging, config.log_level, logging.INFO))
    logger.info("Starting New-Generation Agent Service...")

    config.ensure_dirs()
    SkillRegistry.discover()
    PromptManager.load()

    logger.info(f"Skills: {[s.name for s in SkillRegistry.get_all_skills()]}")
    logger.info(f"Prompts: {[t['name'] for t in PromptManager.list_templates()]}")
    logger.info("Agent Service ready.")
    yield
    # Shutdown
    logger.info("Shutting down Agent Service.")


app = FastAPI(
    title="New-Generation Agent Service",
    description="RAG Agent with pluggable Skills",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 异常上报中间件（将未处理异常发送到 Java 后端入库）
app.add_middleware(ExceptionReporterMiddleware)

# 限流中间件（POST /chat 每客户端 10 次/分钟）
app.add_middleware(RateLimiterMiddleware, max_requests=10, window_seconds=60)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"error": str(exc)})


# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "service": "agent-python"}


# Include routers
app.include_router(chat_router.router, tags=["Chat"])
app.include_router(knowledge_router.router, tags=["Knowledge"])
app.include_router(skill_router.router, tags=["Skills"])
