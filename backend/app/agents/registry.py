from app.agents.assistant import build_assistant_graph
from app.agents.rag_agent import build_rag_graph
from app.agents.research import build_research_graph

AGENTS = {
    "assistant": {
        "label": "Assistant",
        "description": "Tool-using agent with web search, code, files, email and memory. Risky tools ask for approval.",
        "stream_nodes": {"agent"},
    },
    "rag": {
        "label": "Documents",
        "description": "Agentic RAG over your uploads: retrieves, grades, rewrites the query if needed, cites sources.",
        "stream_nodes": {"generate"},
    },
    "research": {
        "label": "Researcher",
        "description": "Plans, waits for your approval, researches steps in parallel, then writes a report.",
        "stream_nodes": {"writer", "cancel"},
    },
}


def build_graphs(checkpointer, store) -> dict:
    return {
        "assistant": build_assistant_graph(checkpointer, store),
        "rag": build_rag_graph(checkpointer, store),
        "research": build_research_graph(checkpointer, store),
    }
