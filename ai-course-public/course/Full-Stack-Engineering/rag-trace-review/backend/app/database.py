"""SQLite connection management with parameterized query support."""
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
import os

log = logging.getLogger("rag.db")

DB_PATH = os.environ.get("RAG_DB_PATH", str(Path(__file__).parent.parent / "rag_traces.db"))


def get_connection() -> sqlite3.Connection:
    """Get a new SQLite connection with row factory and WAL mode."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def db_cursor(commit: bool = False):
    """Context manager that yields a cursor and optionally commits."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables and indexes if they do not exist."""
    with db_cursor(commit=True) as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS traces (
                trace_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                prompt_version TEXT NOT NULL,
                user_query TEXT NOT NULL,
                prompt TEXT NOT NULL,
                retrieved_chunks TEXT NOT NULL,
                model_response TEXT NOT NULL,
                citations TEXT NOT NULL,
                token_usage INTEGER NOT NULL,
                latency_ms INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'ok',
                feedback TEXT
            )
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_traces_created_id ON traces(created_at DESC, trace_id DESC)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_traces_prompt_version ON traces(prompt_version)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_traces_latency ON traces(latency_ms)"
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trace_id TEXT NOT NULL,
                rating TEXT NOT NULL CHECK (rating IN ('up', 'down')),
                note TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(trace_id),
                FOREIGN KEY(trace_id) REFERENCES traces(trace_id)
            )
            """
        )
