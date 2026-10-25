"""Long-term memory tools backed by a LangGraph `BaseStore`.

Short-term memory is the checkpointed message history; long-term memory is
this cross-thread store, namespaced per user.
"""
import uuid
from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedStore
from langgraph.store.base import BaseStore


def _namespace(config: RunnableConfig) -> tuple[str, str]:
    return ("memories", config.get("configurable", {}).get("user_id", "default"))


@tool
async def save_memory(content: str, config: RunnableConfig, store: Annotated[BaseStore, InjectedStore()]) -> str:
    """Save a durable fact or preference about the user so it can be recalled in future conversations."""
    await store.aput(_namespace(config), str(uuid.uuid4()), {"content": content})
    return f"Saved to long-term memory: {content}"


@tool
async def search_memory(query: str, config: RunnableConfig, store: Annotated[BaseStore, InjectedStore()]) -> str:
    """Search long-term memory for facts previously saved about the user."""
    items = await store.asearch(_namespace(config), query=query, limit=5)
    if not items:
        return "No memories found."
    return "\n".join(f"- {item.value['content']}" for item in items)
