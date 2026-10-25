"""Checkpointer factory.

The checkpointer persists graph state per `thread_id`, which provides conversation memory,
pause/resume for human-in-the-loop, and time-travel. SQLite is perfect for a single instance;
for horizontal scaling use `langgraph-checkpoint-postgres` (see docs/ARCHITECTURE.md).
"""
from contextlib import asynccontextmanager

from app.core.config import Settings


@asynccontextmanager
async def create_checkpointer(settings: Settings):
    if settings.checkpointer == "memory":
        from langgraph.checkpoint.memory import MemorySaver

        yield MemorySaver()
        return

    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    async with AsyncSqliteSaver.from_conn_string(str(settings.checkpoint_db_path)) as saver:
        yield saver
