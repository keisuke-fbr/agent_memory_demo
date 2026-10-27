import time
import sqlite3
from google import genai

MODEL = "gemini-2.5-flash-lite"


class KeywordMemory:
    """LLMが重要情報を選別して保存し、3-gram部分一致で検索する"""

    def __init__(self, client: genai.Client, db_path: str = "pattern2.db"):
        self.client = client
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def _generate(self, prompt: str, max_retries: int = 5) -> str:
        for attempt in range(max_retries):
            try:
                return self.client.models.generate_content(model=MODEL, contents=prompt).text.strip()
            except Exception as e:
                if attempt < max_retries - 1 and "503" in str(e):
                    time.sleep(2 ** attempt)
                else:
                    raise

    def maybe_store(self, user_msg: str, assistant_msg: str) -> str | None:
        """LLMが将来役立つ情報かを判断し、あれば1行で保存する"""
        prompt = f"""以下の会話から、将来の会話で役立つ情報があれば1行で抽出してください。
重要な情報がなければ「なし」とだけ答えてください。

user: {user_msg}
assistant: {assistant_msg}

抽出した情報:"""

        result = self._generate(prompt)
        if result and result != "なし":
            self.conn.execute(
                "INSERT INTO memories (content) VALUES (?)", (result,)
            )
            self.conn.commit()
            return result
        return None

    def search(self, query: str, n_gram: int = 3) -> tuple[list[str], dict[str, list[str]]]:
        """クエリを3-gramに分割し部分一致検索。記憶とマッチしたチャンクを返す"""
        match_info: dict[str, list[str]] = {}
        for i in range(len(query) - n_gram + 1):
            chunk = query[i : i + n_gram]
            rows = self.conn.execute(
                "SELECT content FROM memories WHERE content LIKE ?",
                (f"%{chunk}%",),
            ).fetchall()
            for r in rows:
                content = r[0]
                if content not in match_info:
                    match_info[content] = []
                if chunk not in match_info[content]:
                    match_info[content].append(chunk)
        return list(match_info.keys()), match_info

    def get_all(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, content FROM memories ORDER BY id"
        ).fetchall()
        return [{"id": r[0], "content": r[1]} for r in rows]

    def close(self):
        self.conn.close()
