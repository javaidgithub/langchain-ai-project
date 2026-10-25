"""Turns a LangGraph run into a stream of small, UI-friendly JSON events.

Events (all have a `type`):
  start        {thread_id}
  step         {node}                       a graph node finished (powers the trace rail)
  token        {content, node}              assistant text delta
  reasoning    {content}                    reasoning-model thinking delta (e.g. deepseek-reasoner)
  tool_call    {id, name, args}             the model asked for a tool
  tool_result  {tool_call_id, name, content, status}
  context      {summary}                    older turns were compacted into a summary
  plan         {plan}                       research plan produced
  sources      {sources}                    RAG citations
  interrupt    {id, value}                  graph paused: human input needed
  usage        {input_tokens, output_tokens, total_tokens, llm_calls}
  error        {message}
  done         {interrupted}
"""
from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage
from langgraph.types import Command

from app.agents.config import text_of
from app.agents.registry import AGENTS
from app.callbacks.usage import UsageCallback
from app.core.config import get_settings
from app.core.context import request_credentials
from app.core.errors import AppError
from app.schemas.chat import AgentOptions

log = logging.getLogger(__name__)
MAX_TOOL_RESULT_CHARS = 4000


def build_run_config(thread_id: str, opts: AgentOptions, callback: UsageCallback) -> dict:
    return {
        "configurable": {
            "thread_id": thread_id,
            "provider": opts.model.provider,
            "model": opts.model.model,
            "temperature": opts.model.temperature,
            "enabled_tools": opts.enabled_tools,
            "require_approval": opts.require_approval,
            "system_prompt": opts.system_prompt,
            "user_id": opts.user_id,
        },
        "callbacks": [callback],
        "recursion_limit": get_settings().recursion_limit,
        "metadata": {"agent": opts.agent},
    }


async def stream_run(graph, graph_input: Any, thread_id: str, opts: AgentOptions) -> AsyncIterator[dict]:
    """Run (or resume) a graph and yield events. Never raises: errors become `error` events."""
    # Set inside the generator so it lives in the context that actually executes the run.
    request_credentials.set({opts.model.provider: opts.model.api_key} if opts.model.api_key else {})

    usage = UsageCallback()
    config = build_run_config(thread_id, opts, usage)
    stream_nodes = AGENTS[opts.agent]["stream_nodes"]
    streamed: set[str] = set()

    yield {"type": "start", "thread_id": thread_id}
    try:
        async for mode, data in graph.astream(graph_input, config, stream_mode=["messages", "updates"]):
            if mode == "messages":
                chunk, meta = data
                node = meta.get("langgraph_node")
                if node not in stream_nodes or not isinstance(chunk, AIMessageChunk):
                    continue
                reasoning = chunk.additional_kwargs.get("reasoning_content")
                if reasoning:
                    yield {"type": "reasoning", "content": reasoning}
                text = text_of(chunk.content)
                if text:
                    streamed.add(node)
                    yield {"type": "token", "content": text, "node": node}
                continue

            for node, update in data.items():
                if node.startswith("__") or not isinstance(update, dict):
                    continue
                yield {"type": "step", "node": node}
                for event in _events_from_update(node, update, node in stream_nodes and node not in streamed):
                    yield event
        yield {"type": "usage", **usage.summary()}

        snapshot = await graph.aget_state({"configurable": {"thread_id": thread_id}})
        interrupts = [i for task in snapshot.tasks for i in task.interrupts]
        for intr in interrupts:
            yield {"type": "interrupt", "id": intr.id, "value": intr.value}
        yield {"type": "done", "interrupted": bool(interrupts)}
    except AppError as exc:
        yield {"type": "error", "message": exc.message}
        yield {"type": "done", "interrupted": False}
    except Exception as exc:  # noqa: BLE001 - surface provider errors to the UI
        log.exception("Agent run failed")
        yield {"type": "error", "message": _friendly(exc)}
        yield {"type": "done", "interrupted": False}


def _events_from_update(node: str, update: dict, emit_full_text: bool) -> list[dict]:
    events: list[dict] = []
    for msg in update.get("messages", []) or []:
        if isinstance(msg, ToolMessage):
            events.append({
                "type": "tool_result", "tool_call_id": msg.tool_call_id, "name": msg.name,
                "content": text_of(msg.content)[:MAX_TOOL_RESULT_CHARS], "status": msg.status or "success",
            })
        elif isinstance(msg, AIMessage):
            for call in msg.tool_calls or []:
                events.append({"type": "tool_call", "id": call["id"], "name": call["name"], "args": call["args"]})
            if emit_full_text and not msg.tool_calls and text_of(msg.content):
                events.append({"type": "token", "content": text_of(msg.content), "node": node})
    if update.get("summary") and node == "manage_context":
        events.append({"type": "context", "summary": update["summary"]})
    if node == "planner" and update.get("plan"):
        events.append({"type": "plan", "plan": update["plan"]})
    if update.get("sources"):
        events.append({"type": "sources", "sources": update["sources"]})
    return events


def _friendly(exc: Exception) -> str:
    msg = str(exc) or exc.__class__.__name__
    lowered = msg.lower()
    if "401" in msg or "invalid api key" in lowered or "incorrect api key" in lowered or "authentication" in lowered:
        return "The provider rejected the API key. Check it in Settings or your .env file."
    if "429" in msg or "rate limit" in lowered or "quota" in lowered:
        return "The provider is rate-limiting this key or the quota is exhausted. Try again shortly or switch model."
    if "recursion" in lowered:
        return "The agent hit its step limit before finishing. Try a more specific request."
    return msg[:500]


def resume_command(decision: dict) -> Command:
    return Command(resume=decision)
