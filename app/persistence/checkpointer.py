import os
import sqlite3
from pathlib import Path
from typing import Optional
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import MemorySaver

from app.config import settings


_sqlite_conn: Optional[sqlite3.Connection] = None
_checkpointer_instance: Optional[SqliteSaver] = None


def get_sqlite_checkpointer(db_path: str | None = None) -> SqliteSaver:
    """Returns a singleton SQLite checkpointer connected to the checkpoint DB."""
    global _sqlite_conn, _checkpointer_instance
    if _checkpointer_instance is None:
        target_path = db_path or settings.checkpoint_db
        if target_path == ":memory:":
            _sqlite_conn = sqlite3.connect(":memory:", check_same_thread=False)
        else:
            p = Path(target_path).resolve()
            p.parent.mkdir(parents=True, exist_ok=True)
            _sqlite_conn = sqlite3.connect(str(p), check_same_thread=False)
        _checkpointer_instance = SqliteSaver(_sqlite_conn)
    return _checkpointer_instance


def get_memory_checkpointer() -> MemorySaver:
    """Returns an in-memory checkpointer suitable for testing."""
    return MemorySaver()
