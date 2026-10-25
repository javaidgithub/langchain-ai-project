"""Callback handler that collects token usage and tool timings for one run."""
from __future__ import annotations

import logging
import time
from typing import Any
from uuid import UUID

from langchain_core.callbacks import AsyncCallbackHandler

log = logging.getLogger("agent.callbacks")


class UsageCallback(AsyncCallbackHandler):
    def __init__(self) -> None:
        self.input_tokens = 0
        self.output_tokens = 0
        self.llm_calls = 0
        self._tool_started: dict[UUID, float] = {}

    async def on_llm_end(self, response, **kwargs: Any) -> None:
        self.llm_calls += 1
        for generations in response.generations:
            for gen in generations:
                usage = getattr(getattr(gen, "message", None), "usage_metadata", None)
                if usage:
                    self.input_tokens += usage.get("input_tokens", 0)
                    self.output_tokens += usage.get("output_tokens", 0)

    async def on_tool_start(self, serialized, input_str, *, run_id: UUID, **kwargs: Any) -> None:
        self._tool_started[run_id] = time.perf_counter()

    async def on_tool_end(self, output, *, run_id: UUID, **kwargs: Any) -> None:
        started = self._tool_started.pop(run_id, None)
        if started:
            log.info("tool finished in %.0f ms", (time.perf_counter() - started) * 1000)

    def summary(self) -> dict:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.input_tokens + self.output_tokens,
            "llm_calls": self.llm_calls,
        }
