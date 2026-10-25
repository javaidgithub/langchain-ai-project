import json
import uuid
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agents.config import text_of
from app.api.deps import get_graphs, get_threads
from app.schemas.chat import ChatRequest, ResumeRequest
from app.services.streaming import resume_command, stream_run
from app.services.threads import ThreadRepository

router = APIRouter(prefix="/chat", tags=["chat"])

SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}


async def _sse(events: AsyncIterator[dict]) -> AsyncIterator[str]:
    async for event in events:
        yield f"data: {json.dumps(event, default=str)}\n\n"


@router.post("/stream")
async def chat_stream(req: ChatRequest, graphs: dict = Depends(get_graphs), threads: ThreadRepository = Depends(get_threads)):
    thread_id = req.thread_id or str(uuid.uuid4())
    await threads.upsert(thread_id, req.message, req.agent)
    existing = await threads.get(thread_id)
    if existing and existing["agent"] != req.agent:
        raise HTTPException(409, f"This thread belongs to the '{existing['agent']}' agent. Start a new chat to switch agents.")

    graph_input = {"messages": [HumanMessage(content=req.message)]}
    return StreamingResponse(_sse(stream_run(graphs[req.agent], graph_input, thread_id, req)),
                             media_type="text/event-stream", headers=SSE_HEADERS)


@router.post("/resume")
async def chat_resume(req: ResumeRequest, graphs: dict = Depends(get_graphs), threads: ThreadRepository = Depends(get_threads)):
    """Continue a run that paused for human input (tool approval or plan approval)."""
    if not await threads.get(req.thread_id):
        raise HTTPException(404, "Thread not found")
    return StreamingResponse(_sse(stream_run(graphs[req.agent], resume_command(req.decision), req.thread_id, req)),
                             media_type="text/event-stream", headers=SSE_HEADERS)


def serialize_messages(messages) -> list[dict]:
    out: list[dict] = []
    for m in messages:
        if isinstance(m, HumanMessage):
            out.append({"id": m.id, "role": "user", "content": text_of(m.content)})
        elif isinstance(m, AIMessage):
            out.append({
                "id": m.id, "role": "assistant", "content": text_of(m.content),
                "tool_calls": [{"id": c["id"], "name": c["name"], "args": c["args"]} for c in m.tool_calls or []],
            })
        elif isinstance(m, ToolMessage):
            out.append({"id": m.id, "role": "tool", "tool_call_id": m.tool_call_id, "name": m.name,
                        "content": text_of(m.content)[:4000], "status": m.status or "success"})
    return out
