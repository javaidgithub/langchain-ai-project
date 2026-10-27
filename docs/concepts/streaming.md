# Streaming & SSE

The project streams agent output token-by-token over Server-Sent Events (SSE). SSE is a lightweight HTTP streaming protocol — the server sends a never-ending response with `data:` frames, and the browser reads them live.

**Source file:** `backend/app/services/streaming.py`

---

## Why SSE, not WebSockets?

SSE is one-directional (server → client) and works over plain HTTP/1.1 — no upgrade handshake, no socket management, no CORS complications. For a chat app where the server pushes tokens and the client posts messages, SSE is simpler and more reliable.

---

## The event stream

Every run produces a stream of small JSON objects. The browser reconstructs the UI from these events:

```
data: {"type": "start", "thread_id": "abc123"}

data: {"type": "step", "node": "manage_context"}

data: {"type": "tool_call", "id": "call_1", "name": "web_search", "args": {"query": "..."}}

data: {"type": "token", "content": "According", "node": "agent"}
data: {"type": "token", "content": " to", "node": "agent"}
data: {"type": "token", "content": " Wikipedia", "node": "agent"}

data: {"type": "tool_result", "tool_call_id": "call_1", "name": "web_search", "content": "...", "status": "success"}

data: {"type": "usage", "input_tokens": 412, "output_tokens": 89, "total_tokens": 501, "llm_calls": 2}

data: {"type": "done", "interrupted": false}
```

See the full event reference in [Stream Events](../api/stream-events.md).

---

## How the backend streams

LangGraph's `astream()` supports multiple stream modes simultaneously:

```python
async for mode, data in graph.astream(
    graph_input, config,
    stream_mode=["messages", "updates"],
):
    if mode == "messages":
        chunk, meta = data
        # AIMessageChunk — stream tokens only from designated nodes
        if meta["langgraph_node"] in stream_nodes and isinstance(chunk, AIMessageChunk):
            yield {"type": "token", "content": chunk.content}

    elif mode == "updates":
        for node, update in data.items():
            yield {"type": "step", "node": node}
            yield from events_from_update(node, update)
```

`stream_mode="messages"` delivers token-level deltas. `stream_mode="updates"` delivers completed node outputs (tool calls, tool results, plans, sources).

---

## Controlling which nodes stream

Only nodes in `AGENTS[agent]["stream_nodes"]` produce token events:

```python
AGENTS = {
    "assistant":  {"stream_nodes": {"agent"}},
    "rag":        {"stream_nodes": {"generate"}},
    "research":   {"stream_nodes": {"writer", "cancel"}},
}
```

Internal LLM calls (grading relevance, planning, summarizing) don't leak into the chat.

---

## How the frontend reads the stream

`fetch()` is used instead of `EventSource` because `EventSource` only supports GET, and sending a message body requires POST:

```typescript
const res = await fetch("/api/chat/stream", {
    method: "POST",
    body: JSON.stringify(body),
    headers: { "Content-Type": "application/json" },
});
const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
let buffer = "";
for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += value;
    while (buffer.includes("\n\n")) {
        const [frame, ...rest] = buffer.split("\n\n");
        buffer = rest.join("\n\n");
        const data = frame.split("\n").filter(l => l.startsWith("data: ")).map(l => l.slice(6)).join("");
        onEvent(JSON.parse(data));
    }
}
```

---

## Proxy buffering — the most common problem

If streaming appears all at once instead of incrementally, a proxy is buffering the response. Add to your nginx config:

```nginx
location /api/ {
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 600s;
}
```

The project's `frontend/nginx.conf` already includes this.
