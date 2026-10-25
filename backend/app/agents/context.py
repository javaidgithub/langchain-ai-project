"""Context-window management for long conversations.

Three layers:
1. `manage_context` node  - once the history exceeds a token budget, older turns are
   summarized into `state["summary"]` and removed from `messages`.
2. `build_prompt_messages` - injects that summary as system context on every model call.
3. `trim_messages` safety net - hard-limits what is actually sent to the model.
"""
from __future__ import annotations

from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    RemoveMessage,
    SystemMessage,
    get_buffer_string,
)
from langchain_core.messages.utils import count_tokens_approximately, trim_messages
from langchain_core.runnables import RunnableConfig

from app.agents.config import AgentConfig, text_of
from app.agents.prompts import SUMMARY_PROMPT
from app.core.config import get_settings
from app.llm.factory import get_chat_model


def find_split_index(messages: list[AnyMessage], keep_last: int) -> int:
    """Index where the 'kept' tail begins. Always starts on a human turn so a tool call is
    never separated from its tool result (providers reject orphaned tool messages)."""
    idx = len(messages) - keep_last
    while idx > 0 and not isinstance(messages[idx], HumanMessage):
        idx -= 1
    return max(idx, 0)


async def manage_context(state, config: RunnableConfig) -> dict:
    s = get_settings()
    messages = state["messages"]
    if count_tokens_approximately(messages) <= s.max_context_tokens:
        return {}
    split = find_split_index(messages, s.keep_last_messages)
    if split <= 0:
        return {}

    old = messages[:split]
    cfg = AgentConfig.from_config(config)
    llm = get_chat_model(cfg.provider, cfg.model, temperature=0)
    prompt = SUMMARY_PROMPT.format(
        summary=state.get("summary") or "(none yet)",
        transcript=get_buffer_string(old)[:20000],
    )
    result = await llm.ainvoke(prompt, config)
    return {
        "summary": text_of(result.content).strip(),
        "messages": [RemoveMessage(id=m.id) for m in old if m.id],
    }


def build_prompt_messages(system: str, state, max_tokens: int | None = None) -> list[AnyMessage]:
    """System prompt (+ running summary) followed by a token-bounded slice of history."""
    summary = state.get("summary")
    if summary:
        system = f"{system}\n\nSummary of earlier conversation:\n{summary}"
    history = trim_messages(
        state["messages"],
        max_tokens=max_tokens or get_settings().max_context_tokens,
        strategy="last",
        token_counter=count_tokens_approximately,
        start_on="human",
        include_system=False,
        allow_partial=False,
    )
    return [SystemMessage(content=system), *(history or state["messages"][-1:])]
