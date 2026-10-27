# Request Schemas

Key Pydantic models. All are validated by FastAPI before the handler runs.

---

## ModelSelection

```python
class ModelSelection(BaseModel):
    provider: str          # e.g. "openai", "anthropic", "gemini"
    model: str             # e.g. "gpt-4o-mini" — any id your provider supports
    temperature: float     # 0.0–2.0, default 0.2
    api_key: str | None    # per-request key; never stored
```

## ChatRequest

```python
class ChatRequest(BaseModel):
    message: str                   # 1–20000 characters
    thread_id: str | None          # null to start a new thread
    agent: "assistant" | "rag" | "research"
    model: ModelSelection
    enabled_tools: list[str] | None  # null = all tools; [] = no tools
    require_approval: bool           # default True
    system_prompt: str | None        # max 4000 characters
```

## ResumeRequest

```python
class ResumeRequest(BaseModel):
    thread_id: str
    agent: "assistant" | "rag" | "research"
    model: ModelSelection
    decision: dict     # see Human-in-the-Loop docs for decision shapes
```

## ChainRequest

```python
class ChainRequest(BaseModel):
    model: ModelSelection
    inputs: dict[str, str]   # keys depend on the chain (see GET /api/chains)
```
