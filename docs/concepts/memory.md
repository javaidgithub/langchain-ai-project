# Memory — Short & Long Term

The project uses two separate memory systems that work together.

---

## Short-term memory — conversation history

Short-term memory is the **message history** in `AgentState.messages`. It is persisted in the SQLite checkpointer, keyed by `thread_id`.

```
Thread A  ──► checkpoint A: [HumanMessage, AIMessage, HumanMessage, ...]
Thread B  ──► checkpoint B: [HumanMessage, AIMessage, ...]
```

Every time you send a message, the graph loads the checkpoint for that thread, appends the new message, runs, and saves the updated state back.

When the history gets too long, `manage_context` summarizes it — see [Context Management](context-management.md).

**Scope:** one conversation thread.
**Survives restart:** yes (SQLite).

---

## Long-term memory — the store

Long-term memory is a **key-value store** shared across all threads for a user. The agent can read and write it with two tools:

| Tool | When to use it |
|---|---|
| `save_memory` | "Remember that I prefer dark mode." |
| `search_memory` | Recalled automatically when personalizing answers. |

### How it works

```python
@tool
async def save_memory(
    content: str,
    config: RunnableConfig,
    store: Annotated[BaseStore, InjectedStore()],
) -> str:
    """Save a durable fact or preference about the user."""
    user_id = config["configurable"].get("user_id", "default")
    await store.aput(("memories", user_id), str(uuid.uuid4()), {"content": content})
    return f"Saved: {content}"
```

Memories are namespaced under `("memories", user_id)` so different users cannot see each other's memories.

### Viewing and deleting memories

Open **Settings → Long-term memory** in the UI. You can see every saved fact and delete individual ones. The `/api/memory` endpoint also exposes them directly.

---

## Default store — in-memory

By default the project uses `InMemoryStore`, which is fast but does not persist across server restarts.

```python
# backend/app/main.py
store = InMemoryStore()
```

### Upgrading to persistent storage

For production, replace with a Postgres-backed store:

```python
# install: pip install langgraph-checkpoint-postgres psycopg[binary,pool]
from langgraph.store.postgres.aio import AsyncPostgresStore

store = AsyncPostgresStore.from_conn_string(settings.database_url)
await store.setup()   # creates tables
```

---

## Summary

| | Short-term | Long-term |
|---|---|---|
| **What** | Conversation messages | Facts and preferences |
| **Where** | LangGraph checkpointer | LangGraph store |
| **Keyed by** | `thread_id` | `(user_id, memory_id)` |
| **Scope** | One thread | All threads for a user |
| **Persists** | Yes (SQLite) | No by default — use Postgres |
| **How accessed** | Automatic | `save_memory` / `search_memory` tools |
