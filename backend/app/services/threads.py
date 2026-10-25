"""Tiny SQLite repository for thread metadata (title, agent, timestamps).

Conversation *content* lives in the LangGraph checkpointer; this table only powers the sidebar.
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import aiosqlite


def _now() -> str:
    return datetime.now(UTC).isoformat()


class ThreadRepository:
    def __init__(self, path: Path):
        self.path = str(path)

    async def init(self) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """CREATE TABLE IF NOT EXISTS threads (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, agent TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL)"""
            )
            await db.commit()

    async def upsert(self, thread_id: str, title: str, agent: str) -> None:
        now = _now()
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """INSERT INTO threads (id, title, agent, created_at, updated_at) VALUES (?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET updated_at = excluded.updated_at""",
                (thread_id, title[:80], agent, now, now),
            )
            await db.commit()

    async def list(self) -> list[dict]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM threads ORDER BY updated_at DESC LIMIT 200")
            return [dict(r) for r in await cur.fetchall()]

    async def get(self, thread_id: str) -> dict | None:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM threads WHERE id = ?", (thread_id,))
            row = await cur.fetchone()
            return dict(row) if row else None

    async def rename(self, thread_id: str, title: str) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE threads SET title = ? WHERE id = ?", (title[:80], thread_id))
            await db.commit()

    async def delete(self, thread_id: str) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
            await db.commit()
