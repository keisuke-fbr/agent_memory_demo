import os
import sys
import shutil
from dotenv import load_dotenv
from google import genai
from memory import VectorMemory

load_dotenv()
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
MODEL = "gemini-2.5-flash-lite"
LOG_PATH = "pattern3_log.txt"

SCENARIO = [
    "私の名前は健二です。よろしくお願いします",
    "趣味はラーメン巡りです",
    "東京の渋谷に住んでいます",
    "最近仕事が忙しくて少し疲れています",
    "先週末は映画を見てきました",
    "今日はいい天気ですね",
    "ところで、私の名前覚えていますか？",            # テスト → 成功
    "私がよく食べるものを教えてもらえますか？",      # テスト → 成功（"食べ物"≈"ラーメン"で意味検索）
]


class Tee:
    """標準出力とファイルの両方に同時に書き出す"""
    def __init__(self, *files):
        self.files = files

    def write(self, obj):
        for f in self.files:
            f.write(obj)

    def flush(self):
        for f in self.files:
            f.flush()


def chat(memory: VectorMemory, user_input: str) -> str:
    memories, scores = memory.search(user_input, top_k=3)

    print(f"  [検索結果: {len(memories)}件]")
    if memories:
        for mem, score in zip(memories, scores):
            print(f"    - [{score:5.1f}%] \"{mem}\"")
    else:
        print(f"    （なし）")

    memory_text = "\n".join(f"- {m}" for m in memories)

    prompt = f"""あなたは親切なアシスタントです。
以下の関連する記憶を参考に、ユーザーの発言に返答してください。

【関連する記憶】
{memory_text if memory_text else "（なし）"}

user: {user_input}
assistant:"""

    reply = client.models.generate_content(model=MODEL, contents=prompt).text.strip()

    stored = memory.maybe_store(user_input)
    if stored:
        print(f"  [LLM判断 → 保存]: \"{stored}\"")
    else:
        print(f"  [LLM判断 → 保存なし]")

    all_mems = memory.get_all()
    print(f"  [DB全件: {len(all_mems)}件]")
    for i, m in enumerate(all_mems, 1):
        print(f"    #{i:02d} \"{m}\"")

    return reply


def main():
    chroma_dir = "./chroma_db"
    if os.path.exists(chroma_dir):
        shutil.rmtree(chroma_dir)

    memory = VectorMemory(client=client, persist_dir=chroma_dir)

    with open(LOG_PATH, "w", encoding="utf-8") as log_file:
        original_stdout = sys.stdout
        sys.stdout = Tee(original_stdout, log_file)

        print("=" * 60)
        print("Pattern 3: Vector Memory（LLM選別 + ベクトル検索）")
        print("=" * 60)

        for user_input in SCENARIO:
            print(f"\nYou:   {user_input}")
            reply = chat(memory, user_input)
            print(f"Agent: {reply}")

        sys.stdout = original_stdout

    print(f"\nログを保存しました: {LOG_PATH}")


if __name__ == "__main__":
    main()
