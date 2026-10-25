from fastapi import APIRouter, HTTPException

from app.chains.lcel import CHAINS
from app.core.context import request_credentials
from app.core.errors import AppError
from app.llm.factory import get_chat_model
from app.schemas.chat import ChainRequest

router = APIRouter(prefix="/chains", tags=["chains"])


@router.get("")
async def list_chains():
    return [{"id": k, "description": v["description"], "fields": v["fields"]} for k, v in CHAINS.items()]


@router.post("/{name}")
async def run_chain(name: str, body: ChainRequest):
    spec = CHAINS.get(name)
    if not spec:
        raise HTTPException(404, f"Unknown chain '{name}'")
    missing = [f for f in spec["fields"] if not body.inputs.get(f)]
    if missing:
        raise HTTPException(422, f"Missing inputs: {', '.join(missing)}")

    request_credentials.set({body.model.provider: body.model.api_key} if body.model.api_key else {})
    try:
        llm = get_chat_model(body.model.provider, body.model.model, body.model.temperature)
        output = await spec["builder"](llm).ainvoke(body.inputs)
    except AppError as exc:
        raise HTTPException(exc.status_code, exc.message) from exc
    except Exception as exc:  # provider errors
        raise HTTPException(502, str(exc)[:500]) from exc
    return {"output": output}
