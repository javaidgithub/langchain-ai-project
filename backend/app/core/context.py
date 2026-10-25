"""Request-scoped context.

Per-request API keys (pasted in the UI) are kept in a ContextVar instead of the
LangGraph `configurable` dict, because configurable values can be persisted in
checkpoint metadata. A ContextVar never touches disk.
"""
from contextvars import ContextVar

request_credentials: ContextVar[dict[str, str] | None] = ContextVar("request_credentials", default=None)
