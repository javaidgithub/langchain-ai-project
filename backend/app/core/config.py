"""Application settings, loaded from environment variables / `.env`."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    app_name: str = "LangChain AI Project"
    app_version: str = "1.0.0"
    environment: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    # If set, every /api request must send `Authorization: Bearer <token>`.
    api_auth_token: str | None = None
    data_dir: Path = Path("./data")

    # --- Provider keys (all optional; users can also paste a key in the UI) ---
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    deepseek_api_key: str | None = None
    xai_api_key: str | None = None
    openrouter_api_key: str | None = None
    groq_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    # --- Defaults ---
    default_provider: str = "openai"
    default_model: str = "gpt-4o-mini"

    # --- Embeddings / RAG ---
    embeddings_provider: Literal["openai", "google", "ollama", "huggingface"] = "openai"
    embeddings_model: str | None = None
    chunk_size: int = 1000
    chunk_overlap: int = 150
    retriever_k: int = 4
    max_upload_mb: int = 20

    # --- Agents / context management ---
    checkpointer: Literal["sqlite", "memory"] = "sqlite"
    max_context_tokens: int = 6000
    keep_last_messages: int = 6
    recursion_limit: int = 25
    enable_llm_cache: bool = False
    python_repl_timeout: int = 10

    # --- Observability (LangSmith) ---
    langsmith_tracing: bool = False
    langsmith_api_key: str | None = None
    langsmith_project: str = "langchain-ai-project"

    # ---- derived ----
    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def provider_keys(self) -> dict[str, str | None]:
        return {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
            "gemini": self.google_api_key,
            "deepseek": self.deepseek_api_key,
            "xai": self.xai_api_key,
            "openrouter": self.openrouter_api_key,
            "groq": self.groq_api_key,
            "ollama": "local",  # no key needed
        }

    @property
    def app_db_path(self) -> Path:
        return self.data_dir / "app.db"

    @property
    def checkpoint_db_path(self) -> Path:
        return self.data_dir / "checkpoints.db"

    @property
    def chroma_dir(self) -> Path:
        return self.data_dir / "chroma"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def workspace_dir(self) -> Path:
        return self.data_dir / "workspace"

    def ensure_dirs(self) -> None:
        for p in (self.data_dir, self.chroma_dir, self.uploads_dir, self.workspace_dir):
            p.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
