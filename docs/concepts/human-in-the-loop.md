# Human-in-the-Loop

Human-in-the-loop (HITL) means the agent pauses and waits for a human decision before proceeding. LangGraph implements this natively with `interrupt()`.

**Source files:** `backend/app/agents/assistant.py`, `backend/app/agents/research.py`

---

## How `interrupt()` works

```python
from langgraph.types import interrupt, Command

def human_approval(state: AgentState) -> Command:
    # 1. Pause the graph. Checkpoint is saved. Control returns to the caller.
    decision = interrupt({
        "type": "tool_approval",
        "tool_calls": [...]   # payload shown to the user
    })
    # 2. When resumed, interrupt() returns whatever the caller passed.
    if decision["action"] == "approve":
        return Command(goto="tools")
    elif decision["action"] == "edit":
        ...
    else:  # reject
        return Command(goto="agent", update={"messages": [rejection_message]})
```

The key insight: `interrupt()` **saves state and stops the graph**. When the caller later calls `graph.ainvoke(Command(resume=decision), config)`, the graph reloads from the checkpoint and `interrupt()` returns `decision` as if it had never paused.

---

## The three decisions

### Approve
```json
{ "action": "approve" }
```
Runs the tool with its original arguments.

### Edit
```json
{
  "action": "edit",
  "edited_args": {
    "call_id_1": { "to": "corrected@email.com", "subject": "...", "body": "..." }
  }
}
```
Replaces the AI message with one carrying updated tool call arguments, then runs the tools.

### Reject
```json
{ "action": "reject", "feedback": "Don't email that address." }
```
Adds a `ToolMessage` with `status="error"` for every pending tool call, then routes back to the agent. The model sees the rejection message and can respond intelligently.

!!! important
    Every tool call in a batch must receive a result. Sending an AI message with tool calls and then asking the model another question without tool results will cause a provider error. Rejection creates synthetic results so the history stays valid.

---

## Which tools require approval

Set in `backend/app/tools/registry.py`:

```python
ToolSpec(send_email,   "communication", requires_approval=True),
ToolSpec(python_repl,  "code",          requires_approval=True),
ToolSpec(write_file,   "files",         requires_approval=True),
```

Any tool with `requires_approval=True` triggers the approval node. The routing function checks this:

```python
def route_after_agent(state, config):
    calls = state["messages"][-1].tool_calls
    if AgentConfig.from_config(config).require_approval:
        if any(requires_approval(c["name"]) for c in calls):
            return "human_approval"
    return "tools"
```

---

## Survives page reloads

Because the graph state lives in the SQLite checkpointer, a pending approval survives:

- Page reloads
- Server restarts (with `CHECKPOINTER=sqlite`)
- Network interruptions

`GET /api/threads/{id}` reads the checkpoint and returns any pending interrupts in the response. The frontend re-shows the approval gate when the thread is opened.

---

## Plan approval (Researcher)

The Researcher uses the same mechanism, but the payload is a plan instead of tool calls:

```python
decision = interrupt({
    "type": "plan_approval",
    "plan": ["step 1", "step 2", "step 3"]
})
```

Decisions: `approve`, `edit` (with a `plan` array), or `cancel`.

---

## Disabling approval

Set `require_approval: false` in the request body, or toggle **Ask before risky actions** off in the Settings panel. This is stored per session in the browser.
