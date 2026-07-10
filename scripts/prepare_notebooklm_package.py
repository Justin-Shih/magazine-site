from __future__ import annotations

import argparse
import json
import re
import shutil
from html import unescape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "articles.json"
OUTPUT = ROOT / "output"
SITE = OUTPUT / "site"
ARTICLES = OUTPUT / "articles"
NBLM = OUTPUT / "notebooklm"


def strip_html(value: str) -> str:
    value = re.sub(r"<script\b.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = unescape(value)
    return re.sub(r"[ \t]+\n", "\n", value).strip()


def extract_original_text(html_path: Path) -> str:
    if not html_path.exists():
        return ""
    html = html_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(
        r"<h2>\s*Original Full Text\s*</h2>\s*<div class=\"body-text\">(.*?)</div>",
        html,
        flags=re.I | re.S,
    )
    return clean_notebook_source_text(strip_html(match.group(1))) if match else ""


def clean_notebook_source_text(text: str) -> str:
    patterns = [
        r"©\s*iStock\.com[^\n]*",
        r"More information:\s*.*?(?=\n\n|$)",
        r"More information\s+To watch the Africa Sanitation Dialogue recording.*?(?=\n\n|$)",
        r"IWA LeaP is supported by the EWL Endowment Fund\..*?samuela\.guida@iwahq\.org\)\.",
        r"The author:\s*.*?(?=$)",
        r"References\s+1\..*?(?=$)",
    ]
    for pattern in patterns:
        text = re.sub(pattern, "\n", text, flags=re.I | re.S)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def md_escape_path(path: Path) -> str:
    return path.as_posix()


def article_slug(index: int, article_id: str) -> str:
    return f"{index:03d}-{article_id}"


def write_article_source(out_dir: Path, index: int, article: dict) -> dict:
    slug = article_slug(index, article["id"])
    article_dir = ARTICLES / slug
    html_path = SITE / "articles" / f"{slug}.html"
    pdf_path = article_dir / f"{slug}.pdf"
    source_path = out_dir / "sources" / f"{slug}.md"

    image_items = []
    for image in article.get("display_images", []):
        label = image.get("label", "image")
        crop_path = article_dir / "crops" / f"page-{int(image['page']):03d}-{slugify(label)}.jpg"
        image_items.append({"label": label, "kind": "image", "path": crop_path})

    figure_items = []
    for crop in article.get("crops", []):
        if crop.get("kind") not in {"table", "figure"}:
            continue
        label = crop.get("label", "figure")
        crop_path = article_dir / "crops" / f"page-{int(crop['page']):03d}-{slugify(label)}.jpg"
        figure_items.append({"label": label, "kind": crop.get("kind", "figure"), "path": crop_path})

    original_text = extract_original_text(html_path)
    summary_zh = article.get("summary_zh", "").strip()
    full_text_zh = article.get("full_text_zh", "").strip()

    lines = [
        f"# {article.get('title_zh', '').strip()} / {article.get('title_en') or article.get('title')}",
        "",
        "## Metadata",
        "",
        f"- Source magazine: The Source, April 2026",
        f"- Article ID: {article['id']}",
        f"- Slug: {slug}",
        f"- Phase: {article.get('phase', '')}",
        f"- Magazine page: {article.get('magazine_page', '')}",
        f"- PDF page(s): {article.get('pages', '')}",
        f"- Tags: {', '.join(article.get('tags', []))}",
        f"- Article PDF: {md_escape_path(pdf_path.relative_to(ROOT)) if pdf_path.exists() else 'missing'}",
        "",
        "## NotebookLM Use",
        "",
        "- Use this Markdown source as the primary NotebookLM upload.",
        "- Use the article PDF as an optional companion source if layout, images, or tables need visual grounding.",
        "- Image and figure paths are listed for traceability; NotebookLM may not ingest local linked images from Markdown.",
        "",
        "## Chinese Complete Summary",
        "",
        summary_zh or "(missing)",
        "",
        "## Chinese Full Text",
        "",
        full_text_zh or "(missing)",
        "",
        "## Original Full Text",
        "",
        original_text or "(missing)",
        "",
        "## Images And Figures",
        "",
    ]
    if not image_items and not figure_items:
        lines.append("- None recorded.")
    for item in image_items + figure_items:
        path = item["path"]
        rel = path.relative_to(ROOT) if path.exists() else path
        lines.append(f"- {item['kind']}: {item['label']} - `{md_escape_path(rel)}`")
    lines.append("")

    source_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "index": index,
        "id": article["id"],
        "slug": slug,
        "phase": article.get("phase"),
        "title_zh": article.get("title_zh", ""),
        "title_en": article.get("title_en") or article.get("title", ""),
        "magazine_page": article.get("magazine_page", ""),
        "pdf_pages": article.get("pages", ""),
        "markdown_path": str(source_path.relative_to(ROOT)).replace("\\", "/"),
        "article_pdf_path": str(pdf_path.relative_to(ROOT)).replace("\\", "/") if pdf_path.exists() else "",
        "image_count": len(image_items),
        "figure_count": len(figure_items),
        "summary_chars": len(summary_zh),
        "chinese_full_chars": len(full_text_zh),
        "original_chars": len(original_text),
        "recommended_upload": "markdown",
        "optional_upload": "article_pdf",
    }


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "item"


def write_index(out_dir: Path, cfg: dict, manifest: list[dict]) -> None:
    title = cfg.get("notebook_title") or f"{cfg.get('magazine', 'Magazine')} {cfg.get('issue', '')}"
    lines = [
        f"# {title}",
        "",
        "## Import Summary",
        "",
        f"- Source PDF: `{cfg.get('source_pdf', '')}`",
        f"- Source count: {len(manifest)} Markdown article sources",
        "- Recommended import: upload Markdown sources first; add article PDFs only when visual layout is needed.",
        "",
        "## Article Sources",
        "",
    ]
    for item in manifest:
        lines.append(
            f"- [{item['index']:03d}. {item['title_zh']} / {item['title_en']}]"
            f"({Path(item['markdown_path']).name}) - p.{item['magazine_page']}"
        )
    (out_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")


def write_outline(out_dir: Path, manifest: list[dict]) -> None:
    groups = [
        ("雜誌總覽 / Issue Overview", [1, 2, 3, 4, 5]),
        ("固定專欄 / Regulars", [1]),
        ("專題文章 / Features", [2, 3, 4]),
        ("解決方案 / Solutions", [5]),
        ("研究與創新 / Research & Innovation", [5]),
        ("閱讀與活動 / Reading & Events", [5]),
    ]
    lines = [
        "# NotebookLM 建議目錄 / Suggested Outline",
        "",
        "全部來源匯入同一個既有 NotebookLM 筆記本，不建立多個筆記本。",
        "",
    ]
    for heading, phases in groups:
        lines.append(f"## {heading}")
        lines.append("")
        for item in manifest:
            if item["phase"] in phases:
                lines.append(f"- {item['title_zh']} / {item['title_en']} (p.{item['magazine_page']})")
        lines.append("")
    (out_dir / "notebook-outline.md").write_text("\n".join(lines), encoding="utf-8")


def write_upload_order(out_dir: Path, manifest: list[dict]) -> None:
    lines = [
        "# NotebookLM Upload Order",
        "",
        "Upload these Markdown files into the existing NotebookLM notebook in this order.",
        "",
    ]
    for item in manifest:
        lines.append(f"{item['index']}. `{item['markdown_path']}`")
    lines.extend(
        [
            "",
            "Optional companion PDF uploads:",
            "",
        ]
    )
    for item in manifest:
        if item["article_pdf_path"]:
            lines.append(f"- `{item['article_pdf_path']}`")
    (out_dir / "upload-order.md").write_text("\n".join(lines), encoding="utf-8")


def write_manual_guide(out_dir: Path, manifest: list[dict]) -> None:
    lines = [
        "# Manual Import Guide",
        "",
        "Use this when importing into an existing NotebookLM notebook manually.",
        "",
        "1. Open the existing NotebookLM notebook.",
        "2. Add sources using the files listed in `upload-order.md`.",
        "3. Prefer Markdown files first. They contain Chinese summaries, Chinese full text, and original text.",
        "4. Add article PDFs only when visual context is needed.",
        "5. After upload, ask NotebookLM to create an issue overview using `notebooklm-prompts.md`.",
        "",
        "Expected source count:",
        "",
        f"- Markdown article sources: {len(manifest)}",
        f"- Optional article PDFs: {sum(1 for item in manifest if item['article_pdf_path'])}",
        "",
    ]
    (out_dir / "manual-import-guide.md").write_text("\n".join(lines), encoding="utf-8")


def write_prompts(out_dir: Path) -> None:
    lines = [
        "# NotebookLM Prompts",
        "",
        "## 本期總覽",
        "",
        "請根據所有來源，以繁體中文整理本期雜誌總覽。請分成：主要主題、關鍵文章、重要案例、技術趨勢、政策與治理議題、值得追蹤的問題。",
        "",
        "## 文章索引",
        "",
        "請建立本期文章索引，依雜誌頁碼排序。每篇列出中文標題、英文標題、3 句摘要、關鍵詞。",
        "",
        "## 核心水務議題",
        "",
        "請歸納本期水務相關的 5-8 個核心議題，並指出每個議題對應到哪些文章來源。",
        "",
        "## 圖片與表格索引",
        "",
        "請根據來源中的 Images And Figures 區段，整理所有圖片、圖表與表格，說明它們應支援哪個文章重點。",
        "",
        "## 延伸研究問題",
        "",
        "請提出 10 個適合後續研究或簡報討論的問題，每題附上可參考的來源文章。",
        "",
    ]
    (out_dir / "notebooklm-prompts.md").write_text("\n".join(lines), encoding="utf-8")


def write_automation_plan(out_dir: Path, manifest: list[dict]) -> None:
    lines = [
        "# Automated Import Plan",
        "",
        "Use this only after choosing the existing NotebookLM notebook.",
        "",
        "## Required User Choice",
        "",
        "- Existing notebook ID or exact title: `<EXISTING_NOTEBOOK>`",
        "- Automation route: `MCP` or `CLI`",
        "",
        "## CLI Import Commands",
        "",
        "Markdown sources are the primary upload set:",
        "",
        "```powershell",
    ]
    for item in manifest:
        lines.append(f"& 'C:/Users/justi/anaconda3/Scripts/nlm.exe' source add '<EXISTING_NOTEBOOK>' --file '{ROOT / item['markdown_path']}'")
    lines.extend(
        [
            "```",
            "",
            "Optional PDF companion uploads:",
            "",
            "```powershell",
        ]
    )
    for item in manifest:
        if item["article_pdf_path"]:
            lines.append(f"& 'C:/Users/justi/anaconda3/Scripts/nlm.exe' source add '<EXISTING_NOTEBOOK>' --file '{ROOT / item['article_pdf_path']}'")
    lines.extend(
        [
            "```",
            "",
            "## MCP Import Approach",
            "",
            "Call `source_add` once per Markdown file with:",
            "",
            "- `source_type`: `file`",
            "- `notebook_id`: existing notebook UUID",
            "- `file_path`: absolute path to each Markdown file",
            "",
            "## After Import",
            "",
            "1. List sources and verify source count.",
            "2. Create one note named `本期總覽與導讀` using `notebooklm-prompts.md` as the prompt basis.",
            "3. Do not create a new notebook unless the user explicitly changes the plan.",
            "",
        ]
    )
    (out_dir / "automated-import-plan.md").write_text("\n".join(lines), encoding="utf-8")


def write_quality_report(out_dir: Path, manifest: list[dict]) -> None:
    residue_patterns = [
        "iStock",
        "Credit:",
        "More information",
        "The author:",
        "References",
        "ISBN:",
        "eISBN:",
        "doi:",
    ]
    lines = [
        "# NotebookLM Package Quality Report",
        "",
        "| Source | Summary | Chinese Full | Original | Flags |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for item in manifest:
        text = (ROOT / item["markdown_path"]).read_text(encoding="utf-8", errors="replace")
        flags = [pattern for pattern in residue_patterns if pattern.lower() in text.lower()]
        if item["summary_chars"] < 80:
            flags.append("short-summary")
        if item["chinese_full_chars"] < 200:
            flags.append("short-chinese-full")
        if item["original_chars"] < 300:
            flags.append("short-original")
        lines.append(
            f"| {item['slug']} | {item['summary_chars']} | {item['chinese_full_chars']} | "
            f"{item['original_chars']} | {', '.join(flags) if flags else 'OK'} |"
        )
    (out_dir / "quality-report.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare NotebookLM-ready Markdown sources from generated magazine outputs.")
    parser.add_argument("--out", type=Path, default=NBLM)
    args = parser.parse_args()

    out_dir = args.out if args.out.is_absolute() else (ROOT / args.out)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    (out_dir / "sources").mkdir(parents=True, exist_ok=True)

    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    manifest = [write_article_source(out_dir, index, article) for index, article in enumerate(cfg["articles"], start=1)]

    (out_dir / "sources-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_index(out_dir, cfg, manifest)
    write_outline(out_dir, manifest)
    write_upload_order(out_dir, manifest)
    write_manual_guide(out_dir, manifest)
    write_prompts(out_dir)
    write_automation_plan(out_dir, manifest)
    write_quality_report(out_dir, manifest)

    print(f"Prepared NotebookLM package: {out_dir}")
    print(f"Sources: {len(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
