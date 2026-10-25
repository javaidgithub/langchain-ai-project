from typing import Any, Literal

from pydantic import BaseModel, Field

AgentName = Literal["assistant", "rag", "research"]


class ModelSelection(BaseModel):
    provider: str
    model: str
    temperature: float = Field(default=0.2, ge=0, le=2)
    api_key: str | None = Field(default=None, repr=False, description="Optional per-request key; never stored.")


class AgentOptions(BaseModel):
    agent: AgentName = "assistant"
    model: ModelSelection
    enabled_tools: list[str] | None = None
    require_approval: bool = True
    system_prompt: str | None = Field(default=None, max_length=4000)
    user_id: str = "default"


class ChatRequest(AgentOptions):
    thread_id: str | None = None
    message: str = Field(min_length=1, max_length=20000)


class ResumeRequest(AgentOptions):
    thread_id: str
    decision: dict[str, Any]


class ThreadOut(BaseModel):
    id: str
    title: str
    agent: str
    created_at: str
    updated_at: str


class ChainRequest(BaseModel):
    model: ModelSelection
    inputs: dict[str, str]
