import sqlite3


class NaiveMemory:
    """全メッセージを保存し、直近 n_recent 件だけ返す"""

    def __init__(self, db_path: str = "pattern1.db", n_recent: int = 6):
        self.conn = sqlite3.connect(db_path)
        self.n_recent = n_recent
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                role    TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def add(self, role: str, content: str):
        self.conn.execute(
            "INSERT INTO messages (role, content) VALUES (?, ?)",
            (role, content),
        )
        self.conn.commit()

    def get_recent(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?",
            (self.n_recent,),
        ).fetchall()
        return [{"role": r[0], "content": r[1]} for r in reversed(rows)]

    def get_all(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, role, content FROM messages ORDER BY id"
        ).fetchall()
        return [{"id": r[0], "role": r[1], "content": r[2]} for r in rows]

    def close(self):
        self.conn.close()
