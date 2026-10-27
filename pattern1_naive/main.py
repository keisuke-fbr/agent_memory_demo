import os
import sys
import time
from dotenv import load_dotenv
from google import genai
from memory import NaiveMemory

load_dotenv()
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
MODEL = "gemini-2.5-flash-lite"
LOG_PATH = "pattern1_log.txt"

SCENARIO = [
    "私の名前は健二です。よろしくお願いします",     # 事実: 名前
    "趣味はラーメン巡りです",                       # 事実: 趣味
    "東京の渋谷に住んでいます",                     # 事実: 住所
    "最近仕事が忙しくて少し疲れています",           # フィラー
    "先週末は映画を見てきました",                   # フィラー
    "今日はいい天気ですね",                         # フィラー
    "ところで、私の名前覚えていますか？",            # テスト → 失敗（直近6件の外）
    "私がよく食べるものを教えてもらえますか？",     # テスト → 失敗（関連情報なし）
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


def generate(prompt: str, max_retries: int = 5) -> str:
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model=MODEL, contents=prompt).text.strip()
        except Exception as e:
            if attempt < max_retries - 1 and "503" in str(e):
                wait = 2 ** attempt
                print(f"  [503エラー: {wait}秒後にリトライ...]")
                time.sleep(wait)
            else:
                raise


def chat(memory: NaiveMemory, user_input: str) -> str:
    history = memory.get_recent()

    print(f"  [コンテキスト: 直近{memory.n_recent}件中 {len(history)}件を参照]")
    if history:
        for m in history:
            preview = m["content"][:40] + "..." if len(m["content"]) > 40 else m["content"]
            print(f"    {m['role']:9s}: {preview}")
    else:
        print(f"    （なし）")

    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in history)

    prompt = f"""あなたは親切なアシスタントです。
以下の会話履歴を参考に、ユーザーの発言に返答してください。

【会話履歴】
{history_text if history_text else "（なし）"}

user: {user_input}
assistant:"""

    reply = generate(prompt)

    memory.add("user", user_input)
    memory.add("assistant", reply)

    all_msgs = memory.get_all()
    print(f"  [DB全件: {len(all_msgs)}件]")
    for m in all_msgs:
        preview = m["content"][:40] + "..." if len(m["content"]) > 40 else m["content"]
        print(f"    #{m['id']:02d} {m['role']:9s}: {preview}")

    return reply


def main():
    db_path = "pattern1.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    memory = NaiveMemory(db_path=db_path, n_recent=6)

    with open(LOG_PATH, "w", encoding="utf-8") as log_file:
        original_stdout = sys.stdout
        sys.stdout = Tee(original_stdout, log_file)

        print("=" * 60)
        print(f"Pattern 1: Naive Memory（直近{memory.n_recent}件のみ参照）")
        print("=" * 60)

        for user_input in SCENARIO:
            print(f"\nYou:   {user_input}")
            reply = chat(memory, user_input)
            print(f"Agent: {reply}")

        sys.stdout = original_stdout

    memory.close()
    print(f"\nログを保存しました: {LOG_PATH}")


if __name__ == "__main__":
    main()
