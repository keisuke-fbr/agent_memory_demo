import base64

def make_url(s):
    return "https://mermaid.ink/img/" + base64.urlsafe_b64encode(s.encode("utf-8")).decode("ascii")

p1 = """flowchart TD
  A[ユーザー発話] --> B[直近N件を取得]
  C[(SQLite)] -->|読み込み| B
  B --> D[プロンプト生成]
  D --> E[LLM応答生成]
  E --> F[全会話を保存]
  F -->|書き込み| C
  style A fill:#f5f5f5,stroke:#666666
  style B fill:#dae8fc,stroke:#6c8ebf
  style C fill:#f5f5f5,stroke:#666666
  style D fill:#dae8fc,stroke:#6c8ebf
  style E fill:#ffe6cc,stroke:#d79b00
  style F fill:#d5e8d4,stroke:#82b366"""

p2 = """flowchart TD
  A[ユーザー発話] --> B[3-gram検索]
  C[(SQLite)] -->|読み込み| B
  B --> D[プロンプト生成]
  D --> E[LLM応答生成]
  E --> F{保存すべきか}
  F -->|はい| G[(SQLite保存)]
  F -->|いいえ| H[破棄]
  style A fill:#f5f5f5,stroke:#666666
  style B fill:#dae8fc,stroke:#6c8ebf
  style C fill:#f5f5f5,stroke:#666666
  style D fill:#dae8fc,stroke:#6c8ebf
  style E fill:#ffe6cc,stroke:#d79b00
  style F fill:#fff2cc,stroke:#d6b656
  style G fill:#d5e8d4,stroke:#82b366
  style H fill:#f8cecc,stroke:#b85450"""

p3 = """flowchart TD
  A[ユーザー発話] --> B[ベクトル検索]
  C[(ChromaDB)] -->|読み込み| B
  B --> D[プロンプト生成]
  D --> E[LLM応答生成]
  E --> F{保存すべきか}
  F -->|はい| G[(ChromaDB保存)]
  F -->|いいえ| H[破棄]
  style A fill:#f5f5f5,stroke:#666666
  style B fill:#dae8fc,stroke:#6c8ebf
  style C fill:#e1d5e7,stroke:#9673a6
  style D fill:#dae8fc,stroke:#6c8ebf
  style E fill:#ffe6cc,stroke:#d79b00
  style F fill:#fff2cc,stroke:#d6b656
  style G fill:#d5e8d4,stroke:#82b366
  style H fill:#f8cecc,stroke:#b85450"""

print("P1:", make_url(p1))
print("P2:", make_url(p2))
print("P3:", make_url(p3))
