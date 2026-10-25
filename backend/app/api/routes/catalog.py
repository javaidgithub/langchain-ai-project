from fastapi import APIRouter

from app.agents.registry import AGENTS
from app.llm.catalog import PROVIDERS
from app.llm.factory import is_configured
from app.tools.registry import describe_tools

router = APIRouter(tags=["catalog"])


@router.get("/models")
async def list_models():
    return [
        {"id": p.id, "label": p.label, "models": p.models, "needs_key": p.needs_key,
         "configured": is_configured(p.id), "docs_url": p.docs_url}
        for p in PROVIDERS.values()
    ]


@router.get("/tools")
async def list_tools():
    return describe_tools()


@router.get("/agents")
async def list_agents():
    return [{"id": k, "label": v["label"], "description": v["description"]} for k, v in AGENTS.items()]
