import pytest

from app.tools.calculator import calculator, safe_eval
from app.tools.files import _safe_path
from app.tools.registry import TOOL_REGISTRY, describe_tools, get_tools, requires_approval


def test_calculator_basic():
    assert safe_eval("2 + 3 * 4") == 14
    assert safe_eval("sqrt(144) + 2**10") == 1036
    assert calculator.invoke({"expression": "(1+2)**2"}) == "9"


@pytest.mark.parametrize("bad", ["__import__('os').system('ls')", "open('x')", "2**100000", "a + 1"])
def test_calculator_rejects_unsafe(bad):
    assert "Could not evaluate" in calculator.invoke({"expression": bad})


def test_workspace_blocks_path_traversal():
    with pytest.raises(ValueError):
        _safe_path("../../etc/passwd")
    assert _safe_path("notes/a.txt").name == "a.txt"


def test_registry_flags_risky_tools():
    assert requires_approval("send_email") and requires_approval("python_repl") and requires_approval("write_file")
    assert not requires_approval("calculator")
    assert len(get_tools(None)) == len(TOOL_REGISTRY)
    assert get_tools([]) == []
    assert {t["name"] for t in describe_tools()} == set(TOOL_REGISTRY)
