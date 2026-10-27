# Context Management

LLMs have a finite context window. Long conversations would eventually overflow it — and sending thousands of tokens on every turn is expensive. This project uses a three-layer approach.

**Source file:** `backend/app/agents/context.py`

---

## Layer 1 — Summarize old turns

A `manage_context` node runs at the start of every agent turn. If the history exceeds `MAX_CONTEXT_TOKENS`, it:

1. Finds a safe split point (always on a `HumanMessage`, so a tool call is never separated from its result).
2. Calls the model to summarize the old turns into the running `summary` field.
3. Removes the old messages with `RemoveMessage`.

```python
async def manage_context(state, config):
    if count_tokens_approximately(messages) <= MAX_CONTEXT_TOKENS:
        return {}   # nothing to do
    old = messages[:split]
    new_summary = await llm.ainvoke(SUMMARY_PROMPT.format(
        summary=state.get("summary") or "(none yet)",
        transcript=get_buffer_string(old),
    ))
    return {
        "summary": new_summary,
        "messages": [RemoveMessage(id=m.id) for m in old],
    }
```

The `summary` field is part of `AgentState` and is persisted in the checkpointer, so it survives restarts.

---

## Layer 2 — Inject the summary

Before every model call, the summary is prepended to the system prompt:

```python
def build_prompt_messages(system: str, state) -> list[AnyMessage]:
    if state.get("summary"):
        system += f"\n\nSummary of earlier conversation:\n{state['summary']}"
    history = trim_messages(state["messages"], ...)
    return [SystemMessage(content=system), *history]
```

The model always has access to the full conversation context — either as live messages or as the summary.

---

## Layer 3 — Trim as a safety net

`trim_messages` hard-limits what is actually sent:

```python
from langchain_core.messages.utils import trim_messages, count_tokens_approximately

history = trim_messages(
    messages,
    max_tokens=MAX_CONTEXT_TOKENS,
    strategy="last",                  # keep the most recent
    token_counter=count_tokens_approximately,
    start_on="human",                 # never start on a tool result
    include_system=False,
    allow_partial=False,
)
```

`count_tokens_approximately` is fast and provider-independent. For exact counts, swap in `tiktoken` or the provider's own tokenizer.

---

## Why split on a HumanMessage?

Tool call sequences look like:

```
HumanMessage  → AIMessage (with tool_calls) → ToolMessage (result) → AIMessage
```

If you cut in the middle (e.g., before the `ToolMessage`), the model receives an `AIMessage` with tool calls but no results. OpenAI and Anthropic both reject this. The split function walks backward from the target index until it finds a `HumanMessage`:

```python
def find_split_index(messages, keep_last):
    idx = len(messages) - keep_last
    while idx > 0 and not isinstance(messages[idx], HumanMessage):
        idx -= 1
    return max(idx, 0)
```

---

## Long-term vs. short-term

| | Short-term | Long-term |
|---|---|---|
| What | Conversation history | Facts, preferences |
| Where | LangGraph checkpointer (SQLite) | LangGraph `InMemoryStore` |
| Scope | One thread | All threads for a user |
| Survives restart | Yes (SQLite) | No (in-memory — use Postgres in production) |
| How to use | Automatic | `save_memory` / `search_memory` tools |

See [Memory](memory.md) for long-term memory details.
