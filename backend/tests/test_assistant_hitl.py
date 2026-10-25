"""End-to-end tests of the assistant graph through the real HTTP + SSE layer."""
from langchain_core.messages import AIMessage

from tests.conftest import OPTS, read_sse, tool_call_msg


def _chat(client, message, thread_id=None, **extra):
    with client.stream("POST", "/api/chat/stream", json={**OPTS, "message": message, "thread_id": thread_id, **extra}) as r:
        assert r.status_code == 200
        return read_sse(r)


def _resume(client, thread_id, decision):
    with client.stream("POST", "/api/chat/resume", json={**OPTS, "thread_id": thread_id, "decision": decision}) as r:
        return read_sse(r)


def types(events):
    return [e["type"] for e in events]


def test_health_and_catalog(client):
    assert client.get("/api/health").json()["status"] == "ok"
    providers = {p["id"] for p in client.get("/api/models").json()}
    assert {"openai", "gemini", "deepseek", "openrouter", "xai", "anthropic"} <= providers
    assert any(t["name"] == "send_email" and t["requires_approval"] for t in client.get("/api/tools").json())


def test_safe_tool_runs_without_approval(client, use_script):
    use_script([tool_call_msg("calculator", {"expression": "6*7"}), AIMessage(content="The answer is 42.")])
    events = _chat(client, "what is 6*7?")
    kinds = types(events)
    assert "tool_call" in kinds and "tool_result" in kinds and "interrupt" not in kinds
    assert next(e for e in events if e["type"] == "tool_result")["content"] == "42"
    assert events[-1] == {"type": "done", "interrupted": False}


def test_risky_tool_pauses_then_approve(client, use_script):
    use_script([
        tool_call_msg("send_email", {"to": "a@b.com", "subject": "Hi", "body": "Hello"}),
        AIMessage(content="Email sent."),
    ])
    events = _chat(client, "email a@b.com")
    interrupt = next(e for e in events if e["type"] == "interrupt")
    assert interrupt["value"]["type"] == "tool_approval"
    assert interrupt["value"]["tool_calls"][0]["name"] == "send_email"
    assert events[-1]["interrupted"] is True
    thread_id = events[0]["thread_id"]

    # The pause survives a reload: the thread endpoint reports the pending interrupt.
    assert client.get(f"/api/threads/{thread_id}").json()["interrupts"]

    resumed = _resume(client, thread_id, {"action": "approve"})
    result = next(e for e in resumed if e["type"] == "tool_result")
    assert "queued" in result["content"] and result["status"] == "success"
    assert resumed[-1] == {"type": "done", "interrupted": False}
    assert not client.get(f"/api/threads/{thread_id}").json()["interrupts"]


def test_edit_changes_tool_arguments(client, use_script):
    use_script([
        tool_call_msg("send_email", {"to": "wrong@x.com", "subject": "S", "body": "B"}, "call_9"),
        AIMessage(content="Done."),
    ])
    events = _chat(client, "email someone")
    thread_id = events[0]["thread_id"]
    resumed = _resume(client, thread_id, {"action": "edit", "edited_args": {"call_9": {"to": "right@x.com", "subject": "S", "body": "B"}}})
    assert "right@x.com" in next(e for e in resumed if e["type"] == "tool_result")["content"]


def test_reject_skips_tool_and_informs_model(client, use_script):
    model = use_script([
        tool_call_msg("python_repl", {"code": "print(1)"}),
        AIMessage(content="Understood, I won't run it."),
    ])
    events = _chat(client, "run code")
    thread_id = events[0]["thread_id"]
    resumed = _resume(client, thread_id, {"action": "reject", "feedback": "too risky"})
    result = next(e for e in resumed if e["type"] == "tool_result")
    assert result["status"] == "error" and "too risky" in result["content"]
    assert model.calls == 2


def test_approval_can_be_disabled(client, use_script):
    use_script([tool_call_msg("send_email", {"to": "a@b.com", "subject": "S", "body": "B"}), AIMessage(content="ok")])
    events = _chat(client, "email", require_approval=False)
    assert "interrupt" not in types(events) and "tool_result" in types(events)


def test_thread_history_and_delete(client, use_script):
    use_script([AIMessage(content="Hello there!")])
    events = _chat(client, "hi")
    thread_id = events[0]["thread_id"]
    assert "token" in types(events) or any(e["type"] == "token" for e in events)
    history = client.get(f"/api/threads/{thread_id}").json()
    assert [m["role"] for m in history["messages"]] == ["user", "assistant"]
    assert any(t["id"] == thread_id for t in client.get("/api/threads").json())
    assert client.delete(f"/api/threads/{thread_id}").status_code == 204
    assert client.get(f"/api/threads/{thread_id}").status_code == 404


def test_missing_api_key_is_a_friendly_error(client):
    events = _chat(client, "hello")  # real factory, no key configured
    err = next(e for e in events if e["type"] == "error")
    assert "API key" in err["message"]
