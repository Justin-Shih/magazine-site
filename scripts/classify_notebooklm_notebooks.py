from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "notebooklm"
NLM = Path("C:/Users/justi/anaconda3/Scripts/nlm.exe")


CATEGORIES = [
    ("水務 / IWA / 水利", ["自來水", "water", "iwa", "水利", "水道", "管線", "seismic", "lifelines", "resilience"]),
    ("NotebookLM / Codex 學習", ["notebooklm", "codex"]),
    ("AI 通識 / AI 新知", ["ai通識", "ai新知", "ai產業", "ai 浪潮", "ai治理", "genai", "生成式ai"]),
    ("AI 專業 / LLM / RAG", ["ai專業", "llm", "rag", "fine-tune", "deepseek", "模型", "開源llm", "嵌入式ai"]),
    ("AI 硬體 / 算力", ["ai硬體", "算力", "硬體"]),
    ("數位轉型 / 自動化 / 管理", ["數位轉型", "rpa", "辦公室自動化", "企業管理", "智慧城市"]),
    ("研討會 / 活動", ["研討會", "conference", "工程參訪", "ces", "event"]),
    ("科技 / 新知 / 通訊", ["科技", "無人機", "量子", "區塊鏈", "衛星", "機器人", "自駕"]),
    ("金融", ["金融", "股市", "貨幣", "fintech"]),
    ("行銷 / 品牌 / 通路", ["行銷", "品牌", "商機", "社群", "通路", "產品介紹"]),
    ("個人健康 / 生活", ["health", "belly", "fat", "intimacy", "penhold"]),
    ("目錄 / 索引 / 其他", ["目錄", "心得", "特別要學", "prompt", "密碼"]),
]


def classify(title: str) -> str:
    normalized = title.lower()
    for category, keywords in CATEGORIES:
        if any(keyword.lower() in normalized for keyword in keywords):
            return category
    return "未分類"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [str(NLM), "notebook", "list", "--json"],
        capture_output=True,
        check=True,
    )
    notebooks = json.loads(result.stdout.decode("utf-8", errors="replace"))
    for notebook in notebooks:
        notebook["category"] = classify(notebook["title"])

    grouped: dict[str, list[dict]] = {}
    for notebook in notebooks:
        grouped.setdefault(notebook["category"], []).append(notebook)

    (OUT / "notebook-list-classified.json").write_text(
        json.dumps(notebooks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# NotebookLM 筆記本分類",
        "",
        f"- Total notebooks: {len(notebooks)}",
        "- Classification basis: notebook title keywords only.",
        "",
        "## 建議匯入本期 The Source April 2026 的候選筆記本",
        "",
    ]
    candidates = [
        n
        for n in notebooks
        if n["id"]
        in {
            "d38af9a4-0fef-4cea-bd0c-e93aa66d739f",
            "bc1e9cb6-3151-40eb-80c3-aef6b02578c0",
            "d2a5711c-cc7e-4e88-ae66-65f2079d9d7f",
            "2f3bfaab-11f1-455a-a12c-033ecdeec9c2",
            "e40ca958-cd4f-4645-ba91-1c066d6bca1e",
        }
    ]
    for notebook in candidates:
        lines.append(
            f"- **{notebook['title']}** | sources: {notebook['source_count']} | "
            f"id: `{notebook['id']}`"
        )
    lines.append("")

    for category, items in sorted(grouped.items(), key=lambda pair: pair[0]):
        lines.append(f"## {category} ({len(items)})")
        lines.append("")
        for notebook in items:
            lines.append(
                f"- {notebook['title']} | sources: {notebook['source_count']} | "
                f"id: `{notebook['id']}`"
            )
        lines.append("")

    (OUT / "notebook-classification.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT / 'notebook-classification.md'}")
    print(f"Wrote {OUT / 'notebook-list-classified.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
