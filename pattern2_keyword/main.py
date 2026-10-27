import os
import sys
from dotenv import load_dotenv
from google import genai
from memory import KeywordMemory

load_dotenv()
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
MODEL = "gemini-2.5-flash-lite"
LOG_PATH = "pattern2_log.txt"

SCENARIO = [
    "私の名前は健二です。よろしくお願いします",
    "趣味はラーメン巡りです",
    "東京の渋谷に住んでいます",
    "最近仕事が忙しくて少し疲れています",
    "先週末は映画を見てきました",
    "今日はいい天気ですね",
    "ところで、私の名前覚えていますか？",            # テスト → 成功（"名前"がn-gramでヒット）
    "私がよく食べるものを教えてもらえますか？",      # テスト → 失敗（"食べ物"≠"ラーメン"）
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


def chat(memory: KeywordMemory, user_input: str) -> str:
    memories, match_info = memory.search(user_input)

    print(f"  [検索結果: {len(memories)}件]")
    if memories:
        for mem in memories:
            chunks = match_info[mem]
            print(f"    - \"{mem}\"")
            print(f"      マッチしたn-gram: {chunks}")
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

    stored = memory.maybe_store(user_input, reply)
    if stored:
        print(f"  [LLM判断 → 保存]: \"{stored}\"")
    else:
        print(f"  [LLM判断 → 保存なし]")

    all_mems = memory.get_all()
    print(f"  [DB全件: {len(all_mems)}件]")
    for m in all_mems:
        print(f"    #{m['id']:02d} \"{m['content']}\"")

    return reply


def main():
    db_path = "pattern2.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    memory = KeywordMemory(client=client, db_path=db_path)

    with open(LOG_PATH, "w", encoding="utf-8") as log_file:
        original_stdout = sys.stdout
        sys.stdout = Tee(original_stdout, log_file)

        print("=" * 60)
        print("Pattern 2: Keyword Memory（LLM選別 + 3-gram検索）")
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
