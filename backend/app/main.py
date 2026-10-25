from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langgraph.store.memory import InMemoryStore

from app.agents.registry import build_graphs
from app.api.router import api_router, public_router
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.logging import setup_logging
from app.services.checkpointer import create_checkpointer
from app.services.threads import ThreadRepository

log = logging.getLogger(__name__)


def _configure_langsmith(s: Settings) -> None:
    if s.langsmith_tracing and s.langsmith_api_key:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGSMITH_API_KEY"] = s.langsmith_api_key
        os.environ["LANGSMITH_PROJECT"] = s.langsmith_project
        log.info("LangSmith tracing enabled (project=%s)", s.langsmith_project)


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    setup_logging(s.log_level)
    s.ensure_dirs()
    _configure_langsmith(s)

    if s.enable_llm_cache:
        from langchain_core.caches import InMemoryCache
        from langchain_core.globals import set_llm_cache

        set_llm_cache(InMemoryCache())

    async with create_checkpointer(s) as checkpointer:
        store = InMemoryStore()  # long-term memory; swap for a Postgres-backed store in production
        app.state.checkpointer = checkpointer
        app.state.store = store
        app.state.graphs = build_graphs(checkpointer, store)
        app.state.threads = ThreadRepository(s.app_db_path)
        await app.state.threads.init()
        log.info("%s %s ready", s.app_name, s.app_version)
        yield


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title=s.app_name, version=s.app_version, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware, allow_origins=s.cors_origin_list, allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError):
        return JSONResponse({"detail": exc.message}, status_code=exc.status_code)

    app.include_router(public_router, prefix=s.api_prefix)
    app.include_router(api_router, prefix=s.api_prefix)
    return app


app = create_app()
