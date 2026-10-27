# REST Endpoints

Interactive docs are at `http://localhost:8000/docs` (Swagger) and `/redoc`.

All endpoints except `/api/health` require `Authorization: Bearer <token>` when `API_AUTH_TOKEN` is set in `.env`.

---

## Health

### `GET /api/health`

No auth required.

**Response**
```json
{ "status": "ok", "version": "1.0.0", "environment": "development" }
```

---

## Catalog

### `GET /api/models`

Returns providers, suggested model ids and whether a server-side API key is configured.

```json
[
  {
    "id": "openai",
    "label": "OpenAI",
    "models": ["gpt-4o-mini", "gpt-4o", "gpt-4.1"],
    "needs_key": true,
    "configured": true,
    "docs_url": "https://platform.openai.com/api-keys"
  }
]
```

### `GET /api/tools`

Returns the tool catalog with approval flags.

```json
[
  { "name": "web_search",  "description": "Search the web...", "category": "web",  "requires_approval": false },
  { "name": "send_email",  "description": "Send an email...",  "category": "communication", "requires_approval": true }
]
```

### `GET /api/agents`

```json
[
  { "id": "assistant", "label": "Assistant", "description": "Tool-using agent..." },
  { "id": "rag",       "label": "Documents", "description": "Agentic RAG..." },
  { "id": "research",  "label": "Researcher", "description": "Plans, researches..." }
]
```

---

## Chat

### `POST /api/chat/stream`

Send a message. Returns a `text/event-stream` response.

**Body**
```json
{
  "message": "What is the capital of France?",
  "thread_id": null,
  "agent": "assistant",
  "model": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "temperature": 0.2,
    "api_key": null
  },
  "enabled_tools": null,
  "require_approval": true,
  "system_prompt": null
}
```

- `thread_id` — omit or `null` to start a new thread; provide an existing id to continue.
- `enabled_tools` — `null` means all tools enabled; an empty list means no tools.
- `api_key` — optional per-request key; stored in memory only.

See [Stream Events](stream-events.md) for the response format.

### `POST /api/chat/resume`

Resume a run paused by `interrupt()`.

**Body**
```json
{
  "thread_id": "abc123",
  "agent": "assistant",
  "model": { "provider": "openai", "model": "gpt-4o-mini", "temperature": 0.2, "api_key": null },
  "decision": { "action": "approve" }
}
```

Decision options — see [Human-in-the-Loop](../concepts/human-in-the-loop.md).

---

## Threads

### `GET /api/threads`

List all conversation threads, newest first.

### `GET /api/threads/{id}`

Full thread detail including message history, running summary and any pending interrupt.

```json
{
  "id": "abc123",
  "title": "What is the capital of France?",
  "agent": "assistant",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:01:00Z",
  "messages": [...],
  "summary": null,
  "interrupts": []
}
```

### `PATCH /api/threads/{id}`

Rename a thread.

```json
{ "title": "Paris conversation" }
```

### `DELETE /api/threads/{id}`

Delete a thread and its checkpoint.

---

## Documents (RAG)

### `POST /api/rag/upload`

Upload and index a document. `multipart/form-data`, field name `file`.

Supported types: `.pdf`, `.txt`, `.md`, `.markdown`, `.csv`, `.json`. Max size: `MAX_UPLOAD_MB` (default 20 MB).

```json
{ "name": "report.pdf", "chunks": 42 }
```

### `GET /api/rag/documents`

List indexed documents.

```json
[{ "name": "report.pdf", "chunks": 42 }]
```

### `DELETE /api/rag/documents/{name}`

Remove a document and all its chunks.

### `POST /api/rag/query`

One-shot RAG query (no agent loop).

```json
{
  "question": "What does the report say about revenue?",
  "model": { "provider": "openai", "model": "gpt-4o-mini", "temperature": 0.2, "api_key": null }
}
```

Response:
```json
{
  "answer": "According to [1], revenue grew 12%...",
  "sources": [
    { "index": 1, "source": "report.pdf", "page": 3, "snippet": "Revenue grew 12%..." }
  ]
}
```

---

## Chains

### `GET /api/chains`

List available LCEL chains.

### `POST /api/chains/{name}`

Run a chain. Available names: `summarize`, `translate`, `extract`, `analyze`, `route`.

```json
{
  "model": { "provider": "openai", "model": "gpt-4o-mini", "temperature": 0.2, "api_key": null },
  "inputs": { "text": "LangChain is a framework...", "style": "3 bullet points" }
}
```

---

## Memory

### `GET /api/memory?user_id=default`

List long-term memories for a user.

### `DELETE /api/memory/{id}?user_id=default`

Delete a memory by id.
