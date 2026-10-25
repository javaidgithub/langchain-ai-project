"""General-purpose tool-using agent with human-in-the-loop approval.

START -> manage_context -> agent -+-> END                      (no tool calls)
                                  +-> tools -> agent            (safe tools)
                                  +-> human_approval -+-> tools (approved / edited)
                                                      +-> agent (rejected, with feedback)
"""
from __future__ import annotations

from typing import Literal

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command, interrupt

from app.agents.config import AgentConfig
from app.agents.context import build_prompt_messages, manage_context
from app.agents.prompts import ASSISTANT_PROMPT, today
from app.agents.state import AgentState
from app.llm.factory import get_chat_model
from app.tools.registry import all_tools, get_tools, requires_approval


async def agent_node(state: AgentState, config: RunnableConfig) -> dict:
    cfg = AgentConfig.from_config(config)
    llm = get_chat_model(cfg.provider, cfg.model, cfg.temperature)
    tools = get_tools(cfg.enabled_tools)
    model = llm.bind_tools(tools) if tools else llm

    system = ASSISTANT_PROMPT.format(today=today())
    if cfg.system_prompt:
        system += f"\n\nAdditional instructions from the user:\n{cfg.system_prompt}"

    response = await model.ainvoke(build_prompt_messages(system, state), config)
    return {"messages": [response]}


def route_after_agent(state: AgentState, config: RunnableConfig) -> Literal["tools", "human_approval", "__end__"]:
    last = state["messages"][-1]
    calls = getattr(last, "tool_calls", None)
    if not calls:
        return END
    if AgentConfig.from_config(config).require_approval and any(requires_approval(c["name"]) for c in calls):
        return "human_approval"
    return "tools"


def human_approval(state: AgentState) -> Command[Literal["tools", "agent"]]:
    """Pause the graph and wait for a human decision.

    `interrupt()` checkpoints the run and returns control to the API caller. The graph resumes
    when the client sends `Command(resume=<decision>)`, and `interrupt()` then returns that value.

    Decision shape: {"action": "approve" | "reject" | "edit",
                     "edited_args": {tool_call_id: {...}},   # for "edit"
                     "feedback": "optional text"}              # for "reject"
    """
    last: AIMessage = state["messages"][-1]
    decision = interrupt({
        "type": "tool_approval",
        "message": "The agent wants to run the following action(s). Approve, edit, or reject.",
        "tool_calls": [
            {"id": c["id"], "name": c["name"], "args": c["args"], "needs_approval": requires_approval(c["name"])}
            for c in last.tool_calls
        ],
    })

    action = (decision or {}).get("action", "reject")

    if action == "approve":
        return Command(goto="tools")

    if action == "edit":
        edits = decision.get("edited_args", {})
        new_calls = [{**c, "args": edits.get(c["id"], c["args"])} for c in last.tool_calls]
        # Same message id => the `add_messages` reducer replaces the original AI message.
        return Command(goto="tools", update={"messages": [last.model_copy(update={"tool_calls": new_calls})]})

    feedback = (decision or {}).get("feedback")
    note = "The user rejected this action." + (f" Their feedback: {feedback}" if feedback else "")
    rejections = [ToolMessage(content=note, tool_call_id=c["id"], name=c["name"], status="error") for c in last.tool_calls]
    return Command(goto="agent", update={"messages": rejections})


def build_assistant_graph(checkpointer, store):
    g = StateGraph(AgentState)
    g.add_node("manage_context", manage_context)
    g.add_node("agent", agent_node)
    g.add_node("human_approval", human_approval)
    g.add_node("tools", ToolNode(all_tools(), handle_tool_errors=True))

    g.add_edge(START, "manage_context")
    g.add_edge("manage_context", "agent")
    g.add_conditional_edges("agent", route_after_agent, {"tools": "tools", "human_approval": "human_approval", END: END})
    g.add_edge("tools", "agent")
    return g.compile(checkpointer=checkpointer, store=store, name="assistant")
