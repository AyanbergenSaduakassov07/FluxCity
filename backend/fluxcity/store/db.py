"""SQLite connection: WAL, foreign keys, schema applied on open."""

import sqlite3
from pathlib import Path

_SCHEMA = (Path(__file__).parent / "schema.sql").read_text()


def connect(path: Path | str) -> sqlite3.Connection:
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(_SCHEMA)
    return conn
