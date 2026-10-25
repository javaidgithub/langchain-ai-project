"""Central tool registry.

To add a tool: write a `@tool` function, then add one `ToolSpec` below.
Set `requires_approval=True` for anything with side effects: the agent graph
will pause and ask the human before running it.
"""
from __future__ import annotations

from dataclasses import dataclass

from langchain_core.tools import BaseTool

from app.tools.calculator import calculator
from app.tools.code_exec import python_repl
from app.tools.datetime_tool import get_current_datetime
from app.tools.email import send_email
from app.tools.files import list_files, read_file, write_file
from app.tools.knowledge import search_knowledge_base
from app.tools.memory import save_memory, search_memory
from app.tools.web import fetch_url, get_weather, web_search, wikipedia


@dataclass(frozen=True)
class ToolSpec:
    tool: BaseTool
    category: str
    requires_approval: bool = False


_SPECS = [
    ToolSpec(calculator, "utility"),
    ToolSpec(get_current_datetime, "utility"),
    ToolSpec(web_search, "web"),
    ToolSpec(wikipedia, "web"),
    ToolSpec(fetch_url, "web"),
    ToolSpec(get_weather, "web"),
    ToolSpec(search_knowledge_base, "knowledge"),
    ToolSpec(save_memory, "memory"),
    ToolSpec(search_memory, "memory"),
    ToolSpec(list_files, "files"),
    ToolSpec(read_file, "files"),
    ToolSpec(write_file, "files", requires_approval=True),
    ToolSpec(python_repl, "code", requires_approval=True),
    ToolSpec(send_email, "communication", requires_approval=True),
]

TOOL_REGISTRY: dict[str, ToolSpec] = {s.tool.name: s for s in _SPECS}


def all_tools() -> list[BaseTool]:
    return [s.tool for s in TOOL_REGISTRY.values()]


def get_tools(names: list[str] | None = None) -> list[BaseTool]:
    """Return the enabled tools. `None` means all; an empty list means none."""
    if names is None:
        return all_tools()
    return [TOOL_REGISTRY[n].tool for n in names if n in TOOL_REGISTRY]


def requires_approval(name: str) -> bool:
    spec = TOOL_REGISTRY.get(name)
    return bool(spec and spec.requires_approval)


def describe_tools() -> list[dict]:
    return [
        {
            "name": s.tool.name,
            "description": (s.tool.description or "").split("\n")[0],
            "category": s.category,
            "requires_approval": s.requires_approval,
        }
        for s in TOOL_REGISTRY.values()
    ]
