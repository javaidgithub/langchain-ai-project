# Callbacks & Observability

LangChain's callback system lets you hook into model calls, tool executions and chain events without modifying their code.

**Source file:** `backend/app/callbacks/usage.py`

---

## The UsageCallback

Every run attaches a `UsageCallback` that aggregates token counts and tool timings:

```python
class UsageCallback(AsyncCallbackHandler):
    def __init__(self):
        self.input_tokens = 0
        self.output_tokens = 0
        self.llm_calls = 0

    async def on_llm_end(self, response, **kwargs):
        self.llm_calls += 1
        for generations in response.generations:
            for gen in generations:
                usage = getattr(gen.message, "usage_metadata", None)
                if usage:
                    self.input_tokens += usage.get("input_tokens", 0)
                    self.output_tokens += usage.get("output_tokens", 0)

    async def on_tool_start(self, serialized, input_str, *, run_id, **kwargs):
        self._tool_started[run_id] = time.perf_counter()

    async def on_tool_end(self, output, *, run_id, **kwargs):
        elapsed = time.perf_counter() - self._tool_started.pop(run_id, 0)
        log.info("tool finished in %.0f ms", elapsed * 1000)
```

At the end of each run, the totals are emitted as a `usage` stream event and displayed under the assistant reply.

---

## Available callback hooks

| Method | Fires when |
|---|---|
| `on_llm_start` / `on_llm_end` | A model call starts / finishes |
| `on_chat_model_stream` | A streaming chunk arrives |
| `on_tool_start` / `on_tool_end` | A tool starts / finishes |
| `on_chain_start` / `on_chain_end` | A chain (LCEL runnable) starts / finishes |
| `on_retriever_start` / `on_retriever_end` | A retriever runs |
| `on_llm_error` / `on_tool_error` | An error occurs |

---

## LangSmith tracing

For full distributed tracing, enable LangSmith:

```dotenv
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=ls__...
LANGSMITH_PROJECT=langchain-ai-project
```

LangSmith captures every run — inputs, outputs, tool calls, intermediate steps, latency and token counts — in a web dashboard. You can replay, compare and debug runs there.

Get a free API key at [smith.langchain.com](https://smith.langchain.com).

---

## LLM caching

Enable response caching to skip redundant model calls during development:

```dotenv
ENABLE_LLM_CACHE=true
```

```python
# backend/app/main.py
from langchain_core.caches import InMemoryCache
from langchain_core.globals import set_llm_cache
set_llm_cache(InMemoryCache())
```

Identical (prompt, model) pairs return the cached result instantly. Useful when testing prompts. Not recommended in production — it can return stale responses.

---

## Structured logs

The app uses Python's standard `logging`. Set `LOG_LEVEL` in `.env`:

```dotenv
LOG_LEVEL=DEBUG   # DEBUG | INFO | WARNING | ERROR
```

Noisy libraries (httpx, httpcore, chromadb) are pinned to `WARNING` regardless of `LOG_LEVEL`.
