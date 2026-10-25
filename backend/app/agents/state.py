import operator
from typing import Annotated

from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """`messages` is the short-term memory; `summary` holds compacted older context."""

    summary: str


class RAGState(MessagesState):
    question: str
    documents: list[dict]
    sources: list[dict]
    rewrites: int
    sufficient: bool
    summary: str


RESET = "<<reset>>"


def merge_findings(old: list[str] | None, new: list[str]) -> list[str]:
    """Append findings from parallel workers; a [RESET] update clears them for a new run."""
    if new and new[0] == RESET:
        return new[1:]
    return (old or []) + new


class ResearchState(MessagesState):
    topic: str
    plan: list[str]
    findings: Annotated[list[str], merge_findings]
    summary: str


__all__ = ["AgentState", "RAGState", "ResearchState", "RESET", "operator"]
