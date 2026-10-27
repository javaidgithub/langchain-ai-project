# Stream Events

`POST /api/chat/stream` and `POST /api/chat/resume` both return `text/event-stream`. Each frame is:

```
data: <json>\n\n
```

The stream always ends with a `done` event.

---

## Event reference

### `start`

The run has begun. New threads get their id here.

```json
{ "type": "start", "thread_id": "abc123" }
```

### `step`

A graph node has finished. Used to power the trace rail.

```json
{ "type": "step", "node": "manage_context" }
```

Possible nodes: `manage_context`, `agent`, `tools`, `human_approval`, `prepare`, `retrieve`, `grade`, `rewrite`, `generate`, `planner`, `approve_plan`, `research_one`, `writer`, `cancel`.

### `token`

An assistant text delta. Concatenate these to build the full reply.

```json
{ "type": "token", "content": "Paris is", "node": "agent" }
```

### `reasoning`

A reasoning-model thinking delta (e.g. `deepseek-reasoner`). Shown in a collapsible block.

```json
{ "type": "reasoning", "content": "Let me think..." }
```

### `tool_call`

The model has requested a tool. Appears before the tool runs.

```json
{ "type": "tool_call", "id": "call_1", "name": "web_search", "args": { "query": "langchain 2025" } }
```

### `tool_result`

A tool has finished.

```json
{
  "type": "tool_result",
  "tool_call_id": "call_1",
  "name": "web_search",
  "content": "LangChain released version...",
  "status": "success"
}
```

`status` is `"success"` or `"error"`. A rejected tool has `status: "error"` and `content` starting with `"The user rejected"`.

### `context`

Older messages were summarized. The `summary` is the updated rolling context.

```json
{ "type": "context", "summary": "User asked about Paris. Agent confirmed it is the capital of France." }
```

### `plan`

The Researcher produced a research plan.

```json
{ "type": "plan", "plan": ["History of Paris", "Paris economy", "Paris tourism"] }
```

### `sources`

RAG citations from the Documents agent.

```json
{
  "type": "sources",
  "sources": [
    { "index": 1, "source": "report.pdf", "page": 3, "snippet": "Paris is the capital..." }
  ]
}
```

### `usage`

Aggregated token usage for the run.

```json
{ "type": "usage", "input_tokens": 412, "output_tokens": 89, "total_tokens": 501, "llm_calls": 2 }
```

### `interrupt`

The run is paused for a human decision. The stream ends after this.

**Tool approval:**
```json
{
  "type": "interrupt",
  "id": "interrupt_id_1",
  "value": {
    "type": "tool_approval",
    "message": "The agent wants to run the following action(s). Approve, edit, or reject.",
    "tool_calls": [
      { "id": "call_1", "name": "send_email", "args": { "to": "a@b.com", "subject": "Hi", "body": "Hello" }, "needs_approval": true }
    ]
  }
}
```

**Plan approval:**
```json
{
  "type": "interrupt",
  "id": "interrupt_id_2",
  "value": {
    "type": "plan_approval",
    "message": "Review the research plan. Approve, edit the steps, or cancel.",
    "plan": ["Step 1", "Step 2"]
  }
}
```

### `error`

A friendly error message. The stream still ends with `done`.

```json
{ "type": "error", "message": "No API key for OpenAI. Add it to your .env file or paste it in Settings." }
```

### `done`

Always the last event. `interrupted: true` means the run paused for human input.

```json
{ "type": "done", "interrupted": false }
```

---

## Handling interrupts

When `done.interrupted` is `true`:

1. Read the `interrupt` event(s) — there is one per pending approval.
2. Show the approval UI.
3. When the user decides, `POST /api/chat/resume` with `{ thread_id, agent, model, decision }`.
4. The stream resumes from the saved checkpoint.

If the user reloads the page before deciding, `GET /api/threads/{thread_id}` returns `interrupts: [...]` so you can re-show the approval UI.
