"""Shared fixtures: a scripted fake chat model so graphs can be tested without API keys."""
from __future__ import annotations

import json
import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult

os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="lc-test-"))
os.environ["CHECKPOINTER"] = "memory"
os.environ["ENVIRONMENT"] = "test"


class ScriptedChat(BaseChatModel):
    """Returns pre-scripted AIMessages in order. Supports bind_tools / structured output as no-ops."""

    script: list = []
    calls: int = 0

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        msg = self.script[min(self.calls, len(self.script) - 1)]
        self.calls += 1
        return ChatResult(generations=[ChatGeneration(message=msg)])

    def bind_tools(self, tools, **kwargs):
        return self


def tool_call_msg(name: str, args: dict, call_id: str = "call_1") -> AIMessage:
    return AIMessage(content="", tool_calls=[{"id": call_id, "name": name, "args": args}])


@pytest.fixture
def client():
    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c


@pytest.fixture
def use_script(monkeypatch):
    """Install a scripted model for every module that builds chat models."""

    def _install(script: list[AIMessage]):
        model = ScriptedChat(script=script)
        for module in ("app.agents.assistant", "app.agents.context", "app.agents.rag_agent", "app.agents.research"):
            monkeypatch.setattr(f"{module}.get_chat_model", lambda *a, **k: model, raising=False)
        return model

    return _install


def read_sse(response) -> list[dict]:
    events = []
    for line in response.iter_lines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


OPTS = {"agent": "assistant", "model": {"provider": "openai", "model": "fake"}, "require_approval": True}
