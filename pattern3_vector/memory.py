import time
import chromadb
from google import genai

MODEL = "gemini-2.5-flash-lite"
EMBED_MODEL = "gemini-embedding-001"


class VectorMemory:
    """LLMが重要情報を選別して保存し、ベクトル類似度で意味検索する"""

    def __init__(self, client: genai.Client, persist_dir: str = "./chroma_db"):
        self.client = client
        self.chroma = chromadb.PersistentClient(path=persist_dir)
        # コサイン類似度を使用（スコアが直感的に理解しやすい）
        self.collection = self.chroma.get_or_create_collection(
            "memories",
            metadata={"hnsw:space": "cosine"},
        )
        self._next_id = self.collection.count() + 1

    def _generate(self, prompt: str, max_retries: int = 5) -> str:
        for attempt in range(max_retries):
            try:
                return self.client.models.generate_content(model=MODEL, contents=prompt).text.strip()
            except Exception as e:
                if attempt < max_retries - 1 and "503" in str(e):
                    time.sleep(2 ** attempt)
                else:
                    raise

    def _embed(self, text: str) -> list[float]:
        result = self.client.models.embed_content(
            model=EMBED_MODEL,
            contents=text,
        )
        return result.embeddings[0].values

    def maybe_store(self, user_msg: str) -> str | None:
        """ユーザー発話のみを対象に、記憶する価値があるか判断して保存する"""
        prompt = f"""以下のユーザーの発言から、将来の会話で役立つユーザー自身に関する情報があれば1行で抽出してください。
名前・趣味・住所・好み・状況など、ユーザー自身に関することのみが対象です。
該当する情報がなければ「なし」とだけ答えてください。

ユーザーの発言: {user_msg}

抽出した情報:"""

        result = self._generate(prompt)
        if result and result != "なし":
            embedding = self._embed(result)
            self.collection.add(
                ids=[str(self._next_id)],
                embeddings=[embedding],
                documents=[result],
            )
            self._next_id += 1
            return result
        return None

    def get_all(self) -> list[str]:
        results = self.collection.get()
        return results["documents"]

    def search(self, query: str, top_k: int = 3) -> tuple[list[str], list[float]]:
        """クエリと意味的に近い記憶を返す。類似度スコア（0〜100%）も返す"""
        count = self.collection.count()
        if count == 0:
            return [], []

        embedding = self._embed(query)
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, count),
        )
        docs = results["documents"][0]
        # コサイン距離（0=同一, 1=無関係）→ 類似度%に変換
        similarities = [round((1 - d) * 100, 1) for d in results["distances"][0]]
        return docs, similarities
