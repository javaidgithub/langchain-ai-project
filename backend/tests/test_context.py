from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.agents.context import build_prompt_messages, find_split_index


def _convo():
    return [
        HumanMessage(content="q1", id="1"), AIMessage(content="", id="2", tool_calls=[{"id": "t1", "name": "x", "args": {}}]),
        ToolMessage(content="r", tool_call_id="t1", id="3"), AIMessage(content="a1", id="4"),
        HumanMessage(content="q2", id="5"), AIMessage(content="a2", id="6"),
    ]


def test_split_never_orphans_tool_messages():
    msgs = _convo()
    # keep_last=3 would start at the ToolMessage; it must walk back to the human turn
    assert isinstance(msgs[find_split_index(msgs, 3)], HumanMessage)
    assert find_split_index(msgs, 3) == 4 or find_split_index(msgs, 3) == 0


def test_prompt_includes_summary_and_system():
    out = build_prompt_messages("SYS", {"messages": _convo(), "summary": "user likes tea"})
    assert out[0].type == "system" and "user likes tea" in out[0].content
    assert out[1].type == "human"
