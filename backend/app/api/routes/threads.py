from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.api.deps import get_graphs, get_threads
from app.api.routes.chat import serialize_messages
from app.services.threads import ThreadRepository

router = APIRouter(prefix="/threads", tags=["threads"])


class RenameBody(BaseModel):
    title: str


@router.get("")
async def list_threads(threads: ThreadRepository = Depends(get_threads)):
    return await threads.list()


@router.get("/{thread_id}")
async def get_thread(thread_id: str, graphs: dict = Depends(get_graphs), threads: ThreadRepository = Depends(get_threads)):
    """Full history plus any pending human-in-the-loop interrupt, so a page reload can resume."""
    meta = await threads.get(thread_id)
    if not meta:
        raise HTTPException(404, "Thread not found")
    snapshot = await graphs[meta["agent"]].aget_state({"configurable": {"thread_id": thread_id}})
    interrupts = [{"id": i.id, "value": i.value} for t in snapshot.tasks for i in t.interrupts]
    return {
        **meta,
        "messages": serialize_messages(snapshot.values.get("messages", [])),
        "summary": snapshot.values.get("summary"),
        "interrupts": interrupts,
    }


@router.patch("/{thread_id}")
async def rename_thread(thread_id: str, body: RenameBody, threads: ThreadRepository = Depends(get_threads)):
    await threads.rename(thread_id, body.title)
    return {"ok": True}


@router.delete("/{thread_id}", status_code=204)
async def delete_thread(thread_id: str, request: Request, threads: ThreadRepository = Depends(get_threads)):
    await threads.delete(thread_id)
    saver = request.app.state.checkpointer
    if hasattr(saver, "adelete_thread"):
        await saver.adelete_thread(thread_id)
