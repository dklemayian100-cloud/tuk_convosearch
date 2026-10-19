"""
SQLite query logging for TUK-ConvoSearch.

Stores every query + response so the admin panel can display a log.
Failures are silent — logging must never break the chat.

Location: app/services/database.py
"""

import os
import json
import sqlite3
from typing import List, Dict, Any, Optional


# Store the SQLite file next to the repo root
DB_PATH = os.getenv("DATABASE_PATH", "./data/tuk_convosearch.db")


def _get_connection() -> sqlite3.Connection:
    """Open a connection to the SQLite database, creating the folder if needed."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the query_log table if it doesn't exist. Safe to call repeatedly."""
    with _get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS query_log (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id      TEXT NOT NULL,
                question        TEXT NOT NULL,
                answer          TEXT NOT NULL,
                sources         TEXT,
                chunks_found    INTEGER DEFAULT 0,
                response_time   REAL DEFAULT 0.0,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_query_log_session
            ON query_log(session_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_query_log_created
            ON query_log(created_at DESC)
        """)


def log_query(
    session_id: str,
    question: str,
    answer: str,
    sources: Optional[List[Dict[str, Any]]] = None,
    chunks_found: int = 0,
    response_time: float = 0.0,
) -> None:
    """Insert a query record. Safe to call repeatedly."""
    sources_json = json.dumps(sources or [], ensure_ascii=False)

    with _get_connection() as conn:
        conn.execute(
            """
            INSERT INTO query_log
                (session_id, question, answer, sources, chunks_found, response_time)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (session_id, question, answer, sources_json, chunks_found, response_time),
        )


def get_recent_queries(limit: int = 100) -> List[Dict[str, Any]]:
    """Return the most recent N queries for the admin panel."""
    with _get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT id, session_id, question, answer, sources,
                   chunks_found, response_time, created_at
            FROM query_log
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()

    results = []
    for row in rows:
        record = dict(row)
        try:
            record["sources"] = json.loads(record["sources"] or "[]")
        except (json.JSONDecodeError, TypeError):
            record["sources"] = []
        results.append(record)
    return results


def get_stats() -> Dict[str, Any]:
    """Return summary statistics for the admin panel."""
    with _get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM query_log").fetchone()[0]
        avg_time_row = conn.execute(
            "SELECT AVG(response_time) FROM query_log"
        ).fetchone()[0]
        avg_time = float(avg_time_row) if avg_time_row is not None else 0.0

    return {
        "total_queries": int(total),
        "average_response_time": round(avg_time, 2),
    }


# Create the table on import so the first log_query call always succeeds
init_db()