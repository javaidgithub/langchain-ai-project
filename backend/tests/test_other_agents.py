"""Research (plan approval + parallel workers) and RAG (grade/rewrite loop) graphs."""
from langchain_core.messages import AIMessage

from tests.conftest import read_sse, tool_call_msg


def _stream(client, url, body):
    with client.stream("POST", url, json=body) as r:
        assert r.status_code == 200, r.read()
        return read_sse(r)


def _opts(agent):
    return {"agent": agent, "model": {"provider": "openai", "model": "fake"}, "require_approval": True}


def test_research_plan_approval_then_report(client, use_script, monkeypatch):
    async def fake_search(*a, **k):
        return "result"

    from types import SimpleNamespace

    monkeypatch.setattr("app.agents.research.web_search", SimpleNamespace(ainvoke=fake_search))
    monkeypatch.setattr("app.agents.research.wikipedia", SimpleNamespace(ainvoke=fake_search))
    use_script([
        tool_call_msg("Plan", {"steps": ["What is X?", "Why does X matter?"]}),   # planner (structured output)
        AIMessage(content="- fact"),                                               # one worker (plan was edited to 1 step)
        AIMessage(content="# Report\nAll done."),                                  # writer
    ])
    events = _stream(client, "/api/chat/stream", {**_opts("research"), "message": "Research X"})
    assert next(e for e in events if e["type"] == "plan")["plan"] == ["What is X?", "Why does X matter?"]
    interrupt = next(e for e in events if e["type"] == "interrupt")
    assert interrupt["value"]["type"] == "plan_approval"
    thread_id = events[0]["thread_id"]

    resumed = _stream(client, "/api/chat/resume", {**_opts("research"), "thread_id": thread_id,
                                                    "decision": {"action": "edit", "plan": ["Only this step"]}})
    steps = [e["node"] for e in resumed if e["type"] == "step"]
    assert steps.count("research_one") == 1  # the edited plan has one step
    assert "writer" in steps
    assert "".join(e["content"] for e in resumed if e["type"] == "token") == "# Report\nAll done."


def test_research_cancel(client, use_script):
    use_script([tool_call_msg("Plan", {"steps": ["a"]})])
    events = _stream(client, "/api/chat/stream", {**_opts("research"), "message": "topic"})
    resumed = _stream(client, "/api/chat/resume", {**_opts("research"), "thread_id": events[0]["thread_id"],
                                                    "decision": {"action": "cancel"}})
    assert any("cancelled" in e.get("content", "") for e in resumed if e["type"] == "token")


def test_rag_rewrites_then_answers_with_sources(client, use_script, monkeypatch):
    from langchain_core.documents import Document

    queries = []

    async def fake_search(q, k=None):
        queries.append(q)
        return [] if len(queries) == 1 else [Document(page_content="Paris is the capital.", metadata={"source": "geo.txt", "page": 2})]

    monkeypatch.setattr("app.agents.rag_agent.search_documents", fake_search)
    use_script([
        # 1st retrieval is empty -> grading is skipped -> rewrite is the first LLM call
        AIMessage(content="better query"),                              # rewrite
        tool_call_msg("Grade", {"sufficient": True, "reason": "ok"}),   # grade (docs found on 2nd retrieval)
        AIMessage(content="Paris [1]."),                                # generate
    ])
    events = _stream(client, "/api/chat/stream", {**_opts("rag"), "message": "capital of France?"})
    assert len(queries) == 2 and queries[1] == "better query"
    assert next(e for e in events if e["type"] == "sources")["sources"][0]["source"] == "geo.txt"
    assert "Paris" in "".join(e["content"] for e in events if e["type"] == "token")
