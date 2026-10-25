# Architecture

This document explains the decisions behind the project. For setup and usage see the [README](../README.md).

## Layers

```
React UI  ──SSE/REST──▶  FastAPI  ──▶  LangGraph graph  ──▶  LangChain (models, tools, retrievers)
                                              │
                                    checkpointer (SQLite) + store (memory)
```

- **API layer** (`app/api`): thin. Validates input, selects the graph, returns a `StreamingResponse`.
- **Streaming service** (`app/services/streaming.py`): the only place that knows LangGraph's stream format. It converts it into the stable event protocol below, so the UI never depends on LangGraph internals.
- **Agents** (`app/agents`): pure graph logic. They read per-request options from `config["configurable"]` through `AgentConfig`, so one compiled graph serves every provider, model and tool selection.
- **Tools / RAG / chains**: plain LangChain code with no knowledge of HTTP.

## Why one compiled graph, many models

Graphs are compiled once at startup with the shared checkpointer and store. The model is **not** baked in: each node calls `get_chat_model(provider, model, temperature)` using values from the run config. That is what makes provider switching a UI dropdown rather than a redeploy, and a conversation can even change model between turns.

## Per-request API keys

Keys pasted in the UI travel in the request body and are stored in a `ContextVar` (`core/context.py`), not in `config["configurable"]`. LangGraph copies configurable values into checkpoint metadata, so putting a secret there could persist it. The context variable lives only for the request. `resolve_api_key` prefers the per-request key and falls back to the server environment.

## Stream events

`POST /api/chat/stream` and `POST /api/chat/resume` return `text/event-stream`. Each frame is `data: <json>\n\n`.

| `type` | Payload | Meaning |
| --- | --- | --- |
| `start` | `thread_id` | Run started (new threads get their id here) |
| `step` | `node` | A graph node finished |
| `token` | `content`, `node` | Assistant text delta |
| `reasoning` | `content` | Reasoning-model thinking delta |
| `tool_call` | `id`, `name`, `args` | The model requested a tool |
| `tool_result` | `tool_call_id`, `name`, `content`, `status` | Tool finished (`status` is `success` or `error`) |
| `context` | `summary` | Older turns were compacted |
| `plan` | `plan` | Research plan produced |
| `sources` | `sources[]` | RAG citations |
| `usage` | token counts, `llm_calls` | Aggregated by the callback handler |
| `interrupt` | `id`, `value` | Run paused for a human decision |
| `error` | `message` | Friendly error; the stream still ends with `done` |
| `done` | `interrupted` | Always the last event |

The generator never raises. Provider errors (bad key, rate limit, recursion limit) become `error` events with actionable text.

Only nodes listed in `AGENTS[...]["stream_nodes"]` stream tokens to the user. Internal LLM calls (grading, planning, summarizing) do not leak into the chat. If a streamed node produces a full message without tokens (a provider that does not stream, or a static message), the full text is emitted once.

## Human-in-the-loop protocol

1. A node calls `interrupt(payload)`. LangGraph saves a checkpoint and stops the run.
2. After the stream ends, the service reads `graph.aget_state(...)` and emits an `interrupt` event for each pending interrupt, then `done` with `interrupted: true`. Reading from state (rather than only from the stream) is more robust across LangGraph versions and also powers reload.
3. The client posts `{thread_id, decision, ...options}` to `/api/chat/resume`. The service runs the graph with `Command(resume=decision)`. The node re-executes from the start and `interrupt()` now returns `decision`.

Because the node re-runs, **code before `interrupt()` must be idempotent**. The approval nodes only read state before interrupting.

**Edit** works by replacing the AI message that holds the tool calls. A message with the same `id` replaces the original through the `add_messages` reducer.

**Reject** adds a `ToolMessage` (with `status="error"`) for every tool call in that AI message and routes back to the agent. Every tool call must receive a result or providers reject the next request, which is why rejecting applies to all calls in the batch.

## Context management

See `app/agents/context.py`. The summarizer is a graph node that runs first on every turn, so all three agents get it. It only fires above the token budget, so short chats pay nothing.

Token counts use `count_tokens_approximately`, which is fast and provider-independent. For exact budgets, replace it with the provider's tokenizer.

## Persistence

| Data | Store | Notes |
| --- | --- | --- |
| Conversation state, pending interrupts | LangGraph checkpointer (`data/checkpoints.db`) | Keyed by `thread_id` |
| Sidebar index (title, agent, timestamps) | `data/app.db` | The checkpointer has no cheap "list threads" |
| Vector store | Chroma (`data/chroma`) | One collection, chunks tagged with `source` |
| Long-term memory | LangGraph `InMemoryStore` | Lost on restart; swap for Postgres |
| Agent workspace and email outbox | `data/workspace` | Sandboxed file tools |

## Scaling out

SQLite and the in-memory store assume one process. For several replicas:

```python
# app/services/checkpointer.py
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

@asynccontextmanager
async def create_checkpointer(settings):
    async with AsyncPostgresSaver.from_conn_string(settings.database_url) as saver:
        await saver.setup()   # creates tables on first run
        yield saver
```

Install `langgraph-checkpoint-postgres` and `psycopg[binary,pool]`, and add a `database_url` setting. Use the matching Postgres store for long-term memory in `main.py`, and move `ThreadRepository` to the same database. Replace Chroma's local persistence with a client/server vector database. Long agent runs hold an HTTP connection open, so tune proxy and load balancer timeouts.

## Frontend design notes

- **Trace rail.** Tool calls, retrieval steps, plans and context compaction are rendered as nodes on a vertical rail beside the answer. A node is a spinner while running, a filled dot when done, and a saffron square while waiting on the human. The approval gate uses the same saffron so the pause is unmistakable.
- **State.** Three small Zustand stores: `settings` (persisted), `chat` (ephemeral) and `catalog` (server metadata). `hooks/chatActions.ts` is the only code that mutates chat state from stream events.
- **Reload safety.** Opening a thread rebuilds messages from server history and re-attaches any pending interrupt.
- **Accessibility.** Visible focus, labelled controls, `role="alertdialog"` on the approval gate, reduced-motion support, light and dark themes via `prefers-color-scheme`.
