from __future__ import annotations

from dataclasses import dataclass

from langchain_core.messages import AnyMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from app.core.config import get_settings


@dataclass
class AgentConfig:
    """Typed view over `config["configurable"]`, set per request by the API layer."""

    provider: str
    model: str
    temperature: float = 0.2
    enabled_tools: list[str] | None = None
    require_approval: bool = True
    system_prompt: str | None = None
    user_id: str = "default"

    @classmethod
    def from_config(cls, config: RunnableConfig | None) -> AgentConfig:
        c = (config or {}).get("configurable", {})
        s = get_settings()
        return cls(
            provider=c.get("provider") or s.default_provider,
            model=c.get("model") or s.default_model,
            temperature=c.get("temperature", 0.2),
            enabled_tools=c.get("enabled_tools"),
            require_approval=c.get("require_approval", True),
            system_prompt=c.get("system_prompt"),
            user_id=c.get("user_id", "default"),
        )


def text_of(content) -> str:
    """Flatten message content (str or list of content blocks) into plain text."""
    if isinstance(content, str):
        return content
    parts = []
    for block in content or []:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts)


def last_human_text(messages: list[AnyMessage]) -> str:
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            return text_of(m.content)
    return ""
