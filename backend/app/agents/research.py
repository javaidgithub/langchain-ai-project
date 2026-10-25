"""Plan -> human approves plan -> parallel research workers (map-reduce via `Send`) -> write report.

START -> manage_context -> planner -> approve_plan -+-> research_one (xN, parallel) -> writer -> END
                                                    +-> cancel -> END   (plan rejected)
"""
from __future__ import annotations

from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, Send, interrupt
from pydantic import BaseModel, Field

from app.agents.config import AgentConfig, last_human_text, text_of
from app.agents.context import manage_context
from app.agents.prompts import PLANNER_PROMPT, WRITER_PROMPT
from app.agents.state import RESET, ResearchState
from app.llm.factory import get_chat_model
from app.tools.web import web_search, wikipedia


class Plan(BaseModel):
    steps: list[str] = Field(description="2-4 research questions", min_length=1, max_length=4)


def _llm(config: RunnableConfig, temperature: float | None = None):
    cfg = AgentConfig.from_config(config)
    return get_chat_model(cfg.provider, cfg.model, cfg.temperature if temperature is None else temperature)


async def planner(state: ResearchState, config: RunnableConfig) -> dict:
    topic = last_human_text(state["messages"])
    plan: Plan = await _llm(config, 0).with_structured_output(Plan).ainvoke(
        [("system", PLANNER_PROMPT), ("human", topic)], config
    )
    return {"topic": topic, "plan": plan.steps, "findings": [RESET]}


def approve_plan(state: ResearchState, config: RunnableConfig) -> Command:
    """HITL checkpoint: the user can approve, edit the steps, or cancel before any searching happens."""
    if not AgentConfig.from_config(config).require_approval:
        decision = {"action": "approve"}
    else:
        decision = interrupt({
            "type": "plan_approval",
            "message": "Review the research plan. Approve it, edit the steps, or cancel.",
            "plan": state["plan"],
        })

    action = (decision or {}).get("action", "cancel")
    if action == "cancel":
        return Command(goto="cancel")

    plan = [s.strip() for s in decision.get("plan", state["plan"]) if s.strip()] if action == "edit" else state["plan"]
    return Command(
        goto=[Send("research_one", {"step": step, "topic": state["topic"]}) for step in plan],
        update={"plan": plan},
    )


async def research_one(payload: dict, config: RunnableConfig) -> dict:
    """Worker: search the web (+ Wikipedia), then condense the evidence for one step."""
    step = payload["step"]
    web = await web_search.ainvoke({"query": step, "max_results": 4})
    wiki = await wikipedia.ainvoke({"query": step})
    result = await _llm(config, 0).ainvoke(
        f"Research step: {step}\nOverall topic: {payload['topic']}\n\n"
        f"Web results:\n{web}\n\nWikipedia:\n{wiki[:2000]}\n\n"
        "Extract the key facts relevant to the step as concise bullets. Keep source URLs next to each fact.",
        config,
    )
    return {"findings": [f"### {step}\n{text_of(result.content)}"]}


async def writer(state: ResearchState, config: RunnableConfig) -> dict:
    prompt = WRITER_PROMPT.format(topic=state["topic"], findings="\n\n".join(state["findings"]))
    response = await _llm(config).ainvoke(prompt, config)
    return {"messages": [response]}


async def cancel(state: ResearchState) -> dict:
    return {"messages": [AIMessage(content="Research cancelled. Tell me how you'd like to change the plan and I'll try again.")]}


def build_research_graph(checkpointer, store):
    g = StateGraph(ResearchState)
    g.add_node("manage_context", manage_context)
    g.add_node("planner", planner)
    g.add_node("approve_plan", approve_plan)
    g.add_node("research_one", research_one)
    g.add_node("writer", writer)
    g.add_node("cancel", cancel)

    g.add_edge(START, "manage_context")
    g.add_edge("manage_context", "planner")
    g.add_edge("planner", "approve_plan")
    g.add_edge("research_one", "writer")
    g.add_edge("writer", END)
    g.add_edge("cancel", END)
    return g.compile(checkpointer=checkpointer, store=store, name="research")
