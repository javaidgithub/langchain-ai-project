"""Sandboxed file tools. Everything is confined to `<DATA_DIR>/workspace`."""
from pathlib import Path

from langchain_core.tools import tool

from app.core.config import get_settings


def _safe_path(relative: str) -> Path:
    root = get_settings().workspace_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    target = (root / relative).resolve()
    if root != target and root not in target.parents:
        raise ValueError("Path escapes the workspace")
    return target


@tool
def list_files() -> str:
    """List the files in the agent workspace."""
    root = get_settings().workspace_dir
    root.mkdir(parents=True, exist_ok=True)
    files = sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file())
    return "\n".join(files) or "The workspace is empty."


@tool
def read_file(path: str) -> str:
    """Read a text file from the agent workspace."""
    try:
        return _safe_path(path).read_text(encoding="utf-8")[:10000]
    except Exception as exc:
        return f"Could not read '{path}': {exc}"


@tool
def write_file(path: str, content: str) -> str:
    """Create or overwrite a text file in the agent workspace. Requires human approval."""
    try:
        target = _safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Wrote {len(content)} characters to {path}"
    except Exception as exc:
        return f"Could not write '{path}': {exc}"
