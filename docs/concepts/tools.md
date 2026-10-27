# Tools & Registry

Tools are functions the model can call to take actions in the world. The project ships 14 tools across 6 categories, all registered in one file.

**Source files:** `backend/app/tools/`

---

## Tool catalog

| Tool | Category | Needs approval | Description |
|---|---|:---:|---|
| `web_search` | web | | DuckDuckGo — no key needed |
| `wikipedia` | web | | Introduction of the best-matching article |
| `fetch_url` | web | | Readable text of a public page |
| `get_weather` | web | | Open-Meteo — no key needed |
| `calculator` | utility | | AST-based, no `eval()` |
| `get_current_datetime` | utility | | Any IANA timezone |
| `search_knowledge_base` | knowledge | | Searches your uploaded documents |
| `save_memory` | memory | | Saves a fact to long-term memory |
| `search_memory` | memory | | Recalls facts from long-term memory |
| `list_files` | files | | Lists the agent workspace |
| `read_file` | files | | Reads a file from the workspace |
| `write_file` | files | ✅ | Writes to the workspace |
| `python_repl` | code | ✅ | Runs Python in a subprocess with a timeout |
| `send_email` | communication | ✅ | Simulated: writes to `data/workspace/outbox.jsonl` |

---

## Defining a tool

Every tool is a `@tool`-decorated function. The docstring is what the model reads to decide when to use it.

```python
from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression exactly. Supports +, -, *, /, **, sqrt, sin, cos,
    log, factorial, abs, round, min, max, pi, e.
    Example: "sqrt(144) + 2**10"."""
    try:
        return str(safe_eval(expression))
    except Exception as exc:
        return f"Could not evaluate '{expression}': {exc}"
```

Write a clear, specific docstring — it is the model's only documentation for the tool.

---

## The tool registry

`backend/app/tools/registry.py` centralises all tool metadata:

```python
@dataclass(frozen=True)
class ToolSpec:
    tool: BaseTool
    category: str
    requires_approval: bool = False

_SPECS = [
    ToolSpec(calculator,  "utility"),
    ToolSpec(python_repl, "code",          requires_approval=True),
    ToolSpec(send_email,  "communication", requires_approval=True),
    # ...
]
```

The registry drives the **Settings panel** in the UI (tool checkboxes), the `/api/tools` endpoint, and the approval routing logic. To toggle a tool's approval requirement, change `requires_approval` here.

---

## Adding a tool

**Step 1.** Write the tool in `backend/app/tools/your_tool.py`:

```python
from langchain_core.tools import tool

@tool
def my_tool(param: str) -> str:
    """One sentence explaining when to call this tool."""
    return do_something(param)
```

**Step 2.** Register it in `backend/app/tools/registry.py`:

```python
from app.tools.your_tool import my_tool

_SPECS = [
    ...
    ToolSpec(my_tool, "utility"),                         # auto-approved
    ToolSpec(my_tool, "utility", requires_approval=True), # pauses for human
]
```

**Step 3.** Add a friendly label in `frontend/src/lib/labels.ts` (optional):

```typescript
const TOOL_LABELS: Record<string, [string, string]> = {
    my_tool: ["Running my tool", "Ran my tool"],
};
```

That is all — the tool appears in the Settings panel and the trace rail automatically.

---

## Tools with injected state

Some tools need access to the LangGraph store (for long-term memory) or the run config. Use `InjectedStore` and `RunnableConfig`:

```python
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedStore
from langgraph.store.base import BaseStore
from typing import Annotated

@tool
async def save_memory(
    content: str,
    config: RunnableConfig,
    store: Annotated[BaseStore, InjectedStore()],
) -> str:
    """Save a durable fact about the user."""
    user_id = config["configurable"].get("user_id", "default")
    await store.aput(("memories", user_id), str(uuid.uuid4()), {"content": content})
    return f"Saved: {content}"
```

LangGraph injects `config` and `store` automatically — the model only sees and fills `content`.

---

## Security notes

- **`calculator`** — uses a safe AST evaluator, not `eval()`. It cannot import modules or access the filesystem.
- **`fetch_url`** — resolves the hostname and refuses private/loopback addresses (SSRF protection).
- **`python_repl`** — runs in a subprocess with a configurable timeout. **This is not a real sandbox.** For production, use a container, gVisor or a hosted sandbox like [E2B](https://e2b.dev).
- **`write_file`, `read_file`, `list_files`** — confined to `data/workspace` via path resolution. A path like `../../etc/passwd` raises a `ValueError`.
