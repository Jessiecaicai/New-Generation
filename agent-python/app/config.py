"""Centralized configuration with path management."""
from pathlib import Path
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """All configuration, supports env var override with AGENT_ prefix."""

    # --- LLM ---
    # provider: "deepseek" | "ollama"
    llm_provider: str = "deepseek"
    llm_temperature: float = 0
    max_concurrent_llm: int = 5

    # DeepSeek (OpenAI-compatible API)
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"

    # Ollama (local fallback)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"

    # --- Paths ---
    data_root: Path = Path("/data")
    log_dir: Optional[Path] = None

    # --- Service ---
    log_level: str = "INFO"
    java_backend_url: str = "http://localhost:8080"

    def model_post_init(self, __context):
        """Derive paths from data_root if not explicitly set."""
        if self.log_dir is None:
            self.log_dir = self.data_root / "logs" / "python"

    def ensure_dirs(self):
        """Create all configured directories on startup."""
        for field_name in self.model_fields:
            value = getattr(self, field_name)
            if isinstance(value, Path) and "dir" in field_name:
                value.mkdir(parents=True, exist_ok=True)

    class Config:
        env_prefix = "AGENT_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_config() -> AppConfig:
    return AppConfig()
