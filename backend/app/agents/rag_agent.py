"""Agentic RAG: retrieve -> grade -> (rewrite query -> retrieve)* -> generate with citations.

START -> prepare -> retrieve -> grade -+-> generate -> END
                       ^               |
                       +-- rewrite <---+  (documents insufficient, max 2 rewrites)
"""
from __future__ import annotations

from typing import Literal

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from app.agents.config import AgentConfig, last_human_text, text_of
from app.agents.context import build_prompt_messages, manage_context
from app.agents.prompts import RAG_PROMPT
from app.agents.state import RAGState
from app.llm.factory import get_chat_model
from app.rag.service import docs_to_sources, format_docs, search_documents

MAX_REWRITES = 2


class Grade(BaseModel):
    sufficient: bool = Field(description="True if the documents contain enough information to answer the question")
    reason: str = Field(description="One short sentence explaining the verdict")


def _llm(config: RunnableConfig, temperature: float | None = None):
    cfg = AgentConfig.from_config(config)
    return get_chat_model(cfg.provider, cfg.model, cfg.temperature if temperature is None else temperature)


async def prepare(state: RAGState) -> dict:
    return {"question": last_human_text(state["messages"]), "rewrites": 0, "documents": [], "sources": []}


async def retrieve(state: RAGState) -> dict:
    docs = await search_documents(state["question"])
    return {
        "documents": [{"page_content": d.page_content, "metadata": d.metadata} for d in docs],
    }


async def grade(state: RAGState, config: RunnableConfig) -> dict:
    if not state["documents"]:
        return {"sufficient": False}
    context = "\n\n".join(d["page_content"][:600] for d in state["documents"])
    try:
        verdict: Grade = await _llm(config, 0).with_structured_output(Grade).ainvoke(
            f"Question: {state['question']}\n\nDocuments:\n{context}\n\nDo these documents contain enough information to answer?",
            config,
        )
        return {"sufficient": verdict.sufficient}
    except Exception:  # model without structured-output support: be permissive
        return {"sufficient": True}


def route_after_grade(state: RAGState) -> Literal["generate", "rewrite"]:
    if state.get("sufficient") or state.get("rewrites", 0) >= MAX_REWRITES:
        return "generate"
    return "rewrite"


async def rewrite(state: RAGState, config: RunnableConfig) -> dict:
    result = await _llm(config, 0).ainvoke(
        "Rewrite this question as a better search query for a document index. "
        f"Return only the query.\n\nQuestion: {state['question']}",
        config,
    )
    return {"question": text_of(result.content).strip() or state["question"], "rewrites": state.get("rewrites", 0) + 1}


async def generate(state: RAGState, config: RunnableConfig) -> dict:
    from langchain_core.documents import Document

    docs = [Document(page_content=d["page_content"], metadata=d["metadata"]) for d in state["documents"]]
    context = format_docs(docs) if docs else "(no relevant documents were found)"
    msgs = build_prompt_messages(RAG_PROMPT.format(context=context), state)
    response = await _llm(config).ainvoke(msgs, config)
    return {"messages": [response], "sources": docs_to_sources(docs)}


def build_rag_graph(checkpointer, store):
    g = StateGraph(RAGState)
    g.add_node("manage_context", manage_context)
    g.add_node("prepare", prepare)
    g.add_node("retrieve", retrieve)
    g.add_node("grade", grade)
    g.add_node("rewrite", rewrite)
    g.add_node("generate", generate)

    g.add_edge(START, "manage_context")
    g.add_edge("manage_context", "prepare")
    g.add_edge("prepare", "retrieve")
    g.add_edge("retrieve", "grade")
    g.add_conditional_edges("grade", route_after_grade, {"generate": "generate", "rewrite": "rewrite"})
    g.add_edge("rewrite", "retrieve")
    g.add_edge("generate", END)
    return g.compile(checkpointer=checkpointer, store=store, name="rag")
