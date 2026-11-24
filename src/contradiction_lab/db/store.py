import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from contradiction_lab.schemas import Paper


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS papers (id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS cache (id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS evaluations (id INTEGER PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions (id TEXT PRIMARY KEY, updated_at TEXT NOT NULL, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS vectors (
                    namespace TEXT, id TEXT, passage TEXT, embedding TEXT,
                    PRIMARY KEY(namespace, id));
            """)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=30)
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def save_paper(self, paper: Paper):
        self.put("papers", paper.paper_id, paper.model_dump(mode="json"))

    def put(self, table: str, identifier: str, value: dict):
        if table not in {"papers", "runs", "cache"}:
            raise ValueError("Invalid storage table")
        with self.connect() as connection:
            connection.execute(f"INSERT OR REPLACE INTO {table} VALUES (?, ?)", (identifier, json.dumps(value)))

    def get(self, table: str, identifier: str):
        if table not in {"papers", "runs", "cache"}:
            raise ValueError("Invalid storage table")
        with self.connect() as connection:
            row = connection.execute(f"SELECT data FROM {table} WHERE id = ?", (identifier,)).fetchone()
        return json.loads(row[0]) if row else None

    def save_evaluation(self, result: dict):
        with self.connect() as connection:
            connection.execute("INSERT INTO evaluations(data) VALUES (?)", (json.dumps(result),))

    def latest_evaluation(self):
        with self.connect() as connection:
            row = connection.execute("SELECT data FROM evaluations ORDER BY id DESC LIMIT 1").fetchone()
        return json.loads(row[0]) if row else None

    # ---- chat sessions -------------------------------------------------------
    def save_session(self, session: dict):
        with self.connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO sessions VALUES (?, ?, ?)",
                (session["session_id"], str(session["updated_at"]), json.dumps(session, default=str)),
            )

    def get_session(self, session_id: str):
        with self.connect() as connection:
            row = connection.execute("SELECT data FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def list_sessions(self) -> list[dict]:
        with self.connect() as connection:
            rows = connection.execute("SELECT data FROM sessions ORDER BY updated_at DESC").fetchall()
        return [json.loads(row[0]) for row in rows]

    def delete_session(self, session_id: str) -> bool:
        with self.connect() as connection:
            return connection.execute("DELETE FROM sessions WHERE id = ?", (session_id,)).rowcount > 0

    # ---- article library -----------------------------------------------------
    def list_papers(self) -> list[dict]:
        with self.connect() as connection:
            rows = connection.execute("SELECT data FROM papers").fetchall()
        return [json.loads(row[0]) for row in rows]

    def vector_counts(self, namespace: str) -> dict[str, int]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT passage FROM vectors WHERE namespace = ?", (namespace,)
            ).fetchall()
        counts: dict[str, int] = {}
        for (passage,) in rows:
            paper_id = json.loads(passage)["paper_id"]
            counts[paper_id] = counts.get(paper_id, 0) + 1
        return counts
