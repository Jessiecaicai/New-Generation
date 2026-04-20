"""Centralized configuration with path management."""
from pathlib import Path
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """All configuration, supports env var override with AGENT_ prefix."""

    # --- LLM (Ollama) ---
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:7b"
    llm_temperature: float = 0
    max_concurrent_llm: int = 5

    # --- Paths ---
    data_root: Path = Path("/data")
    knowledge_upload_dir: Optional[Path] = None
    knowledge_processed_dir: Optional[Path] = None
    knowledge_upload_temp_dir: Optional[Path] = None
    vectordb_dir: Optional[Path] = None
    log_dir: Optional[Path] = None
    log_scan_dir: Optional[Path] = None
    export_dir: Optional[Path] = None
    temp_dir: Optional[Path] = None

    # --- File Limits ---
    knowledge_max_file_size_mb: int = 50
    knowledge_allowed_extensions: str = ".pdf,.txt,.md,.docx"
    temp_cleanup_hours: int = 24

    # --- Service ---
    log_level: str = "INFO"
    java_backend_url: str = "http://localhost:8080"

    def model_post_init(self, __context):
        """Derive paths from data_root if not explicitly set."""
        defaults = {
            "knowledge_upload_dir": self.data_root / "knowledge" / "uploads",
            "knowledge_processed_dir": self.data_root / "knowledge" / "processed",
            "knowledge_upload_temp_dir": self.data_root / "knowledge" / "uploads" / "temp",
            "vectordb_dir": self.data_root / "vectordb" / "chroma",
            "log_dir": self.data_root / "logs" / "python",
            "log_scan_dir": self.data_root / "logs",
            "export_dir": self.data_root / "export",
            "temp_dir": self.data_root / "temp",
        }
        for field, default in defaults.items():
            if getattr(self, field) is None:
                setattr(self, field, default)

    def ensure_dirs(self):
        """Create all configured directories on startup."""
        for field_name in self.model_fields:
            value = getattr(self, field_name)
            if isinstance(value, Path) and "dir" in field_name:
                value.mkdir(parents=True, exist_ok=True)

    class Config:
        env_prefix = "AGENT_"


@lru_cache()
def get_config() -> AppConfig:
    return AppConfig()
