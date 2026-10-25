from fastapi import APIRouter, Request

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("")
async def list_memories(request: Request, user_id: str = "default"):
    """Inspect what the agent has saved to long-term memory (LangGraph store)."""
    items = await request.app.state.store.asearch(("memories", user_id), limit=100)
    return [{"id": i.key, "content": i.value.get("content", "")} for i in items]


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(memory_id: str, request: Request, user_id: str = "default"):
    await request.app.state.store.adelete(("memories", user_id), memory_id)
