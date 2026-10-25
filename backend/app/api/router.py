from fastapi import APIRouter, Depends

from app.api.routes import catalog, chains, chat, health, memory, rag, threads
from app.core.security import verify_token

api_router = APIRouter(dependencies=[Depends(verify_token)])
for module in (catalog, chat, threads, rag, chains, memory):
    api_router.include_router(module.router)

public_router = APIRouter()
public_router.include_router(health.router)
