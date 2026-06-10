"""背景任務 SQLite 持久化儲存。"""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    pass

_TASK_TTL_DAYS = int(os.getenv("TASK_TTL_DAYS", "7"))
_DB_PATH = Path(os.getenv("TASK_DB_PATH", "data/tasks.db"))


class TaskStore:
    """SQLite 持久化背景任務儲存。

    同時維護一份 in-memory dict 供快速讀取，寫入時同步更新 SQLite。
    進程啟動時從 SQLite 還原未完成任務。
    """

    def __init__(self) -> None:
        self._tasks: dict = {}
        self._lock = asyncio.Lock()
        self._db_path = _DB_PATH
        self._initialized = False

    def _connect(self) -> sqlite3.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id     TEXT PRIMARY KEY,
                    name        TEXT NOT NULL,
                    group_id    TEXT NOT NULL,
                    status      TEXT NOT NULL DEFAULT 'pending',
                    created_at  TEXT NOT NULL,
                    completed_at TEXT,
                    chunks_total INTEGER DEFAULT 0,
                    chunks_done  INTEGER DEFAULT 0,
                    result_json  TEXT,
                    error       TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at)")

    def _load_all(self) -> dict:
        from graphiti_mcp_server import MemoryTask

        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE created_at >= datetime('now', ? || ' days')",
                (f"-{_TASK_TTL_DAYS}",),
            ).fetchall()

        tasks = {}
        for row in rows:
            t = MemoryTask(
                task_id=row["task_id"],
                name=row["name"],
                group_id=row["group_id"],
                status=row["status"],
                created_at=row["created_at"],
                completed_at=row["completed_at"],
                chunks_total=row["chunks_total"] or 0,
                chunks_done=row["chunks_done"] or 0,
                result=json.loads(row["result_json"]) if row["result_json"] else None,
                error=row["error"],
            )
            tasks[t.task_id] = t
        return tasks

    def _upsert(self, task) -> None:
        with self._connect() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tasks
                    (task_id, name, group_id, status, created_at, completed_at,
                     chunks_total, chunks_done, result_json, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.task_id, task.name, task.group_id, task.status,
                task.created_at, task.completed_at,
                task.chunks_total, task.chunks_done,
                json.dumps(task.result) if task.result else None,
                task.error,
            ))

    def _cleanup_old(self) -> int:
        with self._connect() as conn:
            cur = conn.execute(
                "DELETE FROM tasks WHERE created_at < datetime('now', ? || ' days')",
                (f"-{_TASK_TTL_DAYS}",),
            )
            return cur.rowcount

    async def initialize(self) -> None:
        """初始化 DB 並從磁碟還原任務。"""
        if self._initialized:
            return
        await asyncio.to_thread(self._init_db)
        loaded = await asyncio.to_thread(self._load_all)
        async with self._lock:
            self._tasks.update(loaded)
            self._initialized = True

    async def put(self, task) -> None:
        """儲存或更新任務（in-memory + SQLite）。"""
        async with self._lock:
            self._tasks[task.task_id] = task
        await asyncio.to_thread(self._upsert, task)

    def get(self, task_id: str):
        """取得任務（in-memory）。"""
        return self._tasks.get(task_id)

    def keys(self):
        return self._tasks.keys()

    def values(self):
        return self._tasks.values()

    def items(self):
        return self._tasks.items()

    def __getitem__(self, task_id: str):
        return self._tasks[task_id]

    def __setitem__(self, task_id: str, task) -> None:
        """同步設定（供現有程式碼相容；背景寫 SQLite）。"""
        self._tasks[task_id] = task
        asyncio.create_task(asyncio.to_thread(self._upsert, task))

    async def cleanup(self) -> int:
        """清除超過 TTL 的舊任務，返回刪除筆數。"""
        n = await asyncio.to_thread(self._cleanup_old)
        cutoff = datetime.now(timezone.utc).isoformat()[:10]
        async with self._lock:
            stale = [
                tid for tid, t in self._tasks.items()
                if t.created_at[:10] < cutoff and
                   (datetime.now(timezone.utc) - datetime.fromisoformat(
                       t.created_at.replace("Z", "+00:00")
                   )).days >= _TASK_TTL_DAYS
            ]
            for tid in stale:
                del self._tasks[tid]
        return n


_store: Optional[TaskStore] = None


def get_task_store() -> TaskStore:
    """取得全域 TaskStore 實例（必須在 initialize_task_store() 後呼叫）。"""
    global _store
    if _store is None:
        _store = TaskStore()
    return _store


async def initialize_task_store() -> TaskStore:
    """初始化並返回全域 TaskStore 實例。"""
    store = get_task_store()
    await store.initialize()
    return store
