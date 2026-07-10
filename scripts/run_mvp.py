from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image
from pypdf import PdfReader, PdfWriter


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "articles.json"
OUTPUT_DIR = ROOT / "output"


DEFAULT_TOC = [
    {"section_en": "Regulars", "section_zh": "固定專欄", "title_en": "The President", "title_zh": "會長專欄", "page": "5", "article_id": "future-focused-feeling"},
    {"section_en": "Regulars", "section_zh": "固定專欄", "title_en": "News", "title_zh": "新聞", "page": "6", "article_id": "news-roundup"},
    {"section_en": "Regulars", "section_zh": "固定專欄", "title_en": "Editorial", "title_zh": "編輯室", "page": "10", "article_id": "waters-role-sustaining-planet"},
    {"section_en": "Regulars", "section_zh": "固定專欄", "title_en": "IWA News", "title_zh": "IWA 新聞", "page": "12", "article_id": "iwa-news-roundup"},
    {"section_en": "Features", "section_zh": "專題", "title_en": "Resources", "title_zh": "資源管理", "page": "13", "article_id": "circular-horticultural-water-management"},
    {"section_en": "Features", "section_zh": "專題", "title_en": "IWA", "title_zh": "IWA 青年領袖", "page": "18", "article_id": "young-leaders-water-landscape"},
    {"section_en": "Features", "section_zh": "專題", "title_en": "Sanitation", "title_zh": "衛生", "page": "22", "article_id": "beyond-sewers-non-sewered-sanitation"},
    {"section_en": "Features", "section_zh": "專題", "title_en": "Europe", "title_zh": "歐洲", "page": "27"},
    {"section_en": "Features", "section_zh": "專題", "title_en": "Governing Member", "title_zh": "治理會員", "page": "31"},
    {"section_en": "Features", "section_zh": "專題", "title_en": "Development", "title_zh": "發展", "page": "37"},
    {"section_en": "Features", "section_zh": "專題", "title_en": "Event", "title_zh": "活動", "page": "41"},
    {"section_en": "Features", "section_zh": "專題", "title_en": "Viewpoint", "title_zh": "觀點", "page": "42"},
    {"section_en": "Features", "section_zh": "專題", "title_en": "Health", "title_zh": "健康", "page": "44"},
    {"section_en": "Regulars", "section_zh": "固定專欄", "title_en": "Solutions", "title_zh": "解決方案", "page": "47"},
    {"section_en": "Regulars", "section_zh": "固定專欄", "title_en": "Solutions - Digital", "title_zh": "數位解決方案", "page": "48"},
    {"section_en": "Regulars", "section_zh": "固定專欄", "title_en": "Research & Innovation", "title_zh": "研究與創新", "page": "49"},
    {"section_en": "Regulars", "section_zh": "固定專欄", "title_en": "Reading & Events", "title_zh": "閱讀與活動", "page": "50"},
]


def phase_for_magazine_page(page: str | int) -> int:
    try:
        value = int(str(page).strip())
    except ValueError:
        return 1
    if value <= 12:
        return 1
    if value <= 26:
        return 2
    if value <= 40:
        return 3
    if value <= 46:
        return 4
    return 5


def default_phases() -> list[dict]:
    return [
        {"id": 1, "title_zh": "固定專欄與前置內容", "title_en": "Regulars and front matter", "magazine_pages": "1-12"},
        {"id": 2, "title_zh": "資源、IWA 與衛生專題", "title_en": "Resources, IWA, and sanitation", "magazine_pages": "13-26"},
        {"id": 3, "title_zh": "歐洲、治理會員與發展", "title_en": "Europe, governing member, and development", "magazine_pages": "27-40"},
        {"id": 4, "title_zh": "活動、觀點與健康", "title_en": "Event, viewpoint, and health", "magazine_pages": "41-46"},
        {"id": 5, "title_zh": "解決方案、研究創新與閱讀活動", "title_en": "Solutions, research, and events", "magazine_pages": "47-50"},
    ]


DEFAULT_FULL_TEXT_ZH = """作為 IWA 會長，我深知自己處在一個非常幸運的位置，能夠協助引導這個卓越組織向前發展。最近在泰國曼谷舉辦、非常成功的 Water and Development Congress & Exhibition，讓我不只是知道自己有多幸運，也真切感受到這份幸運。

我之所以有這樣的感受，一部分來自活動議程與企圖心的深度和廣度。這場大會聚集了來自世界各地的數千名參與者，他們帶著敏銳的思考與堅定的意志，希望推動全球南方的生活轉型。

另一個原因，是我們在曼谷看見了龐大的支持。這場活動由亞洲理工學院共同主辦，並得到亞洲開發銀行、世界銀行與南非 Water Research Commission 等重要夥伴參與。這些合作凸顯了 IWA 在全球水領域中連結組織與實務社群的能力。

活動本身也非常切合區域需求。IWA 的大會雖然具有國際性，但曼谷這一屆特別呼應了區域關切。大會主題「水、衛生與創新：通往進步與韌性未來的路徑」，非常符合該區域正在面對的水與衛生挑戰。這些挑戰受到氣候變遷與天然災害加劇，但同時也促使相關社群決心創新，並與世界各地面臨類似問題的人分享知識。

在此基礎上，IWA 董事會成員與我都感受到外界對 IWA 角色、貢獻與領導力日益增強的信心。因此，我特別振奮的是，在曼谷閉幕典禮中，我們宣布 IWA 將於 2027 年初在南非舉辦專門的 Global Sanitation Summit。此外，大會期間也舉辦了一場高階峰會，其關鍵訊息被整理成「IWA Bangkok Communique on Water Security and Resilience」，作為強化水安全與韌性的共同方向與參考。

Global Sanitation Summit 與 Bangkok Communique 這兩個例子，讓我期待能再次感受到在曼谷所體驗到的幸運與動能。

我也知道，當我今年稍晚參加英國 Glasgow 的 World Water Congress & Exhibition 時，將再次感到非常幸運。明年初的 Global Sanitation Summit 會為 IWA 的全球活動計畫增加重要的衛生面向。

至於 Bangkok Communique，下一場專門的 UN Water Conference 預計於今年年底舉行。該會議的高階籌備會議已於一月在塞內加爾 Dakar 舉辦。IWA 團隊也參與其中，包括執行長 Kala Vairavamoorthy 在全體會議中發言。Dakar 是讓 Bangkok Communique 獲得曝光的理想場域，會議討論顯示該公報的行動呼籲與年底 UN Water Conference 前正在形成的動能相互呼應。

Dakar 會議也讓 IWA 有機會指出，Glasgow Congress 可以成為一個平台，讓實務工作者接觸將被帶入 UN Water Conference 的主題與選項。Glasgow 也將安排聚焦融資與水部門治理角色的高階峰會，因此 IWA 能夠提供實務視角，既相關也及時。

目前這波動能意味著 2027 年及其後有豐富的可能性。隨著節奏加快，IWA 與其網絡已準備好做出貢獻。再加上我們能夠連結抱持相同承諾的組織，我相信我們能協助影響成果。

IWA 的這種廣泛貢獻不像單一活動那樣清楚可見，但同樣重要。我相信 IWA 董事會、治理大會、管理團隊、會員與夥伴都有許多值得期待之處，我能真切感受到這一點。"""


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "item"


def parse_pages(page_spec: str, total_pages: int) -> list[int]:
    pages: list[int] = []
    for part in str(page_spec).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = [int(x) for x in part.split("-", 1)]
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))
    bad = [page for page in pages if page < 1 or page > total_pages]
    if bad:
        raise ValueError(f"Pages outside PDF range 1-{total_pages}: {bad}")
    return list(dict.fromkeys(pages))


def resolve_path(config_path: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    return path if path.is_absolute() else (config_path.parent / path).resolve()


def detect_ocr_engine() -> dict:
    found = shutil.which("tesseract")
    if found:
        return {"name": "tesseract", "path": found, "available": True}
    common = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if common.exists():
        return {"name": "tesseract", "path": str(common), "available": True}
    return {"name": "none", "path": "", "available": False}


def page_text_status(char_count: int) -> str:
    if char_count == 0:
        return "needs_ocr"
    if char_count < 250:
        return "low_text"
    return "ok"


def scan_pages(reader: PdfReader) -> list[dict]:
    rows = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        rows.append(
            {
                "page": page_number,
                "char_count": len(text),
                "status": page_text_status(len(text)),
                "image_count": len(list(page.images)),
                "preview": re.sub(r"\s+", " ", text[:120]).strip(),
            }
        )
    return rows


def write_page_reports(rows: list[dict]) -> None:
    csv_path = OUTPUT_DIR / "page-text-report.csv"
    md_path = OUTPUT_DIR / "page-text-report.md"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["page", "char_count", "status", "image_count", "preview"])
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Page Text Report",
        "",
        f"- Total pages: {len(rows)}",
        f"- Needs OCR: {sum(1 for row in rows if row['status'] == 'needs_ocr')}",
        "",
        "| Page | Characters | Images | Status |",
        "| --- | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(f"| {row['page']} | {row['char_count']} | {row['image_count']} | {row['status']} |")
    md_path.write_text("\n".join(lines), encoding="utf-8")


def write_article_pdf(reader: PdfReader, pages: list[int], out_path: Path) -> None:
    writer = PdfWriter()
    for page_number in pages:
        writer.add_page(reader.pages[page_number - 1])
    with out_path.open("wb") as handle:
        writer.write(handle)


def export_page_images(reader: PdfReader, pages: list[int], images_dir: Path) -> list[dict]:
    images_dir.mkdir(parents=True, exist_ok=True)
    exported = []
    for page_number in pages:
        page = reader.pages[page_number - 1]
        for image_index, image in enumerate(page.images, start=1):
            suffix = Path(getattr(image, "name", "") or ".jpg").suffix.lower() or ".jpg"
            image_path = images_dir / f"page-{page_number:03d}-{image_index}{suffix}"
            image_path.write_bytes(image.data)
            exported.append({"page": page_number, "path": image_path, "name": image_path.name})
    return exported


def crop_from_page_images(source_images: list[dict], crop_defs: list[dict], out_dir: Path) -> list[dict]:
    out_dir.mkdir(parents=True, exist_ok=True)
    by_page = {}
    for image in source_images:
        by_page.setdefault(int(image["page"]), image)
    exported = []
    for index, crop in enumerate(crop_defs, start=1):
        page_number = int(crop["page"])
        source = by_page.get(page_number)
        if not source:
            continue
        bbox = crop["bbox_percent"]
        with Image.open(source["path"]) as img:
            width, height = img.size
            box = (
                round(width * float(bbox[0]) / 100),
                round(height * float(bbox[1]) / 100),
                round(width * float(bbox[2]) / 100),
                round(height * float(bbox[3]) / 100),
            )
            cropped = img.crop(box)
            label = slugify(crop.get("label", f"crop-{index}"))
            path = out_dir / f"page-{page_number:03d}-{label}.jpg"
            cropped.save(path, quality=92)
        exported.append(
            {
                "page": page_number,
                "label": crop.get("label", f"crop-{index}"),
                "kind": crop.get("kind", "text"),
                "path": path,
                "name": path.name,
                "bbox_percent": bbox,
            }
        )
    return exported


def run_ocr(crop_path: Path, out_dir: Path, engine: dict) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    txt_path = out_dir / f"{crop_path.stem}.txt"
    json_path = out_dir / f"{crop_path.stem}.json"
    if not engine.get("available"):
        txt_path.write_text("", encoding="utf-8")
        status = {"status": "pending", "engine": "none", "text_path": str(txt_path), "char_count": 0}
        json_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        return status
    command = [engine["path"], str(crop_path), str(txt_path.with_suffix("")), "-l", "eng"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    text = txt_path.read_text(encoding="utf-8", errors="replace") if txt_path.exists() else ""
    status = {
        "status": "done" if result.returncode == 0 else "failed",
        "engine": engine["name"],
        "text_path": str(txt_path),
        "char_count": len(text.strip()),
        "stderr": result.stderr.strip(),
    }
    json_path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    return status


def collect_ocr_text(crops: list[dict]) -> str:
    chunks = []
    for crop in crops:
        status = crop.get("ocr", {})
        path_text = status.get("text_path")
        if not path_text:
            continue
        path = Path(path_text)
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace").strip()
            if text:
                chunks.append(text)
    return "\n\n".join(chunks)


def clean_ocr_text(text: str, article: dict) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    for pattern in article.get("remove_ocr_patterns", []):
        text = re.sub(pattern, "\n", text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)

    paragraphs = []
    for block in re.split(r"\n\s*\n+", text):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        rebuilt = ""
        for line in lines:
            if not rebuilt:
                rebuilt = line
            elif rebuilt.endswith("-"):
                rebuilt = rebuilt[:-1] + line
            elif re.match(r"^(\d+\.|[A-Z][A-Za-z ]{0,45}:?$)", line):
                rebuilt += "\n" + line
            else:
                rebuilt += " " + line
        paragraphs.append(rebuilt)
    text = "\n\n".join(paragraphs).strip()
    for pattern in article.get("remove_ocr_patterns", []):
        text = re.sub(pattern, "\n", text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def rel_from_site(path: Path) -> str:
    return Path("..", path.relative_to(OUTPUT_DIR)).as_posix()


def rel_from_site_subdir(path: Path) -> str:
    return Path("..", "..", path.relative_to(OUTPUT_DIR)).as_posix()


def site_css() -> str:
    return """
:root {
  --paper: #fbfaf7;
  --ink: #18212f;
  --muted: #647084;
  --line: #d7dddf;
  --accent: #0b6f78;
  --accent-2: #8f3f2b;
  --panel: #ffffff;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--paper);
  color: var(--ink);
  font-family: "Segoe UI", "Microsoft JhengHei", Arial, sans-serif;
  line-height: 1.7;
}
header {
  border-bottom: 1px solid var(--line);
  background: var(--panel);
}
.wrap {
  width: min(1180px, calc(100% - 36px));
  margin: 0 auto;
}
.masthead {
  padding: 26px 0 18px;
}
.kicker {
  color: var(--accent);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0;
  margin: 0 0 4px;
  text-transform: uppercase;
}
h1, h2, h3 { line-height: 1.25; letter-spacing: 0; }
h1 { font-size: 32px; margin: 0 0 8px; }
h2 { font-size: 23px; margin: 0 0 10px; }
h3 { font-size: 17px; margin: 24px 0 8px; }
.subtitle { color: var(--muted); margin: 0; }
main { padding: 24px 0 54px; }
.grid {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(360px, 1.1fr);
  gap: 24px;
  align-items: start;
}
.cover img, figure img {
  width: 100%;
  height: auto;
  display: block;
}
.cover, .toc-card, .article-section, figure {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 8px;
}
.cover { overflow: hidden; }
.toc-card, .article-section { padding: 18px; }
.toc-section + .toc-section { border-top: 1px solid var(--line); margin-top: 16px; padding-top: 16px; }
.toc-list { display: grid; gap: 10px; margin: 0; padding: 0; list-style: none; }
.toc-item a {
  color: var(--ink);
  text-decoration: none;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid #edf0f1;
}
.title-en { font-weight: 750; }
.title-zh { color: var(--accent); font-weight: 700; margin-top: 2px; }
.page-num { color: var(--muted); white-space: nowrap; }
.article-layout {
  display: grid;
  grid-template-columns: minmax(280px, 380px) minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}
.media-stack, .inline-figures { display: grid; gap: 14px; }
.inline-figures {
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
}
figure { margin: 0; overflow: hidden; }
figcaption { padding: 8px 10px; color: var(--muted); font-size: 13px; }
.article-section + .article-section { margin-top: 16px; }
.body-text { white-space: pre-wrap; }
.summary { font-size: 16px; }
.meta-row { color: var(--muted); font-size: 14px; margin-top: 8px; }
.nav { margin-bottom: 14px; }
.nav a { color: var(--accent); font-weight: 700; text-decoration: none; }
@media (max-width: 860px) {
  .grid, .article-layout { grid-template-columns: 1fr; }
  h1 { font-size: 27px; }
}
"""


def write_article_page(site_root: Path, article: dict, article_data: dict) -> str:
    title_en = article.get("title_en") or article.get("title") or article_data["title"]
    title_zh = article.get("title_zh") or "面向未來的感受"
    summary_zh = article.get("summary_zh") or ""
    full_zh = article.get("full_text_zh") or DEFAULT_FULL_TEXT_ZH
    full_en = article_data.get("clean_ocr_text", article_data.get("ocr_text", "")).strip()
    if not full_en:
        full_en = "OCR text is not available yet."
    display_images = [crop for crop in article_data["crops"] if crop.get("kind") == "image"]
    table_images = [crop for crop in article_data["crops"] if crop.get("kind") == "table"]
    figures = []
    for image in display_images:
        figures.append(
            f"""<figure>
  <img src="{html.escape(rel_from_site_subdir(image['path']))}" alt="{html.escape(title_en)} image">
  <figcaption>{html.escape(image.get('label', 'Original image'))}</figcaption>
</figure>"""
        )
    if not figures:
        figures.append("""<div class="article-section"><p class="subtitle">No non-text original image crop has been configured.</p></div>""")
    inline_figures = []
    for image in table_images:
        inline_figures.append(
            f"""<figure>
  <img src="{html.escape(rel_from_site_subdir(image['path']))}" alt="{html.escape(title_en)} figure or table">
  <figcaption>{html.escape(image.get('label', 'Original figure or table'))}</figcaption>
</figure>"""
        )
    inline_figure_section = ""
    if inline_figures:
        inline_figure_section = f"""
        <div class="article-section">
          <h2>圖表與原文表格 / Figures and Tables</h2>
          <div class="inline-figures">{''.join(inline_figures)}</div>
        </div>"""

    page_path = site_root / "articles" / f"{article_data['slug']}.html"
    page_path.parent.mkdir(parents=True, exist_ok=True)
    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title_zh)} | {html.escape(title_en)}</title>
  <style>{site_css()}</style>
</head>
<body>
  <header>
    <div class="wrap masthead">
      <p class="kicker">The Source · April 2026 · p.{html.escape(article.get('magazine_page', '5'))}</p>
      <h1>{html.escape(title_zh)}<br><span class="title-en">{html.escape(title_en)}</span></h1>
      <p class="subtitle">{html.escape(article.get('why_selected', ''))}</p>
    </div>
  </header>
  <main class="wrap">
    <div class="nav"><a href="../index.html">← 返回目錄 / Back to contents</a></div>
    <div class="article-layout">
      <aside class="media-stack">
        {''.join(figures)}
      </aside>
      <section>
        <div class="article-section">
          <h2>中文完整摘要說明</h2>
          <p class="summary">{html.escape(summary_zh)}</p>
        </div>
        <div class="article-section">
          <h2>中文全文</h2>
          <div class="body-text">{html.escape(full_zh)}</div>
        </div>
        {inline_figure_section}
        <div class="article-section">
          <h2>Original Full Text</h2>
          <div class="body-text">{html.escape(full_en)}</div>
        </div>
      </section>
    </div>
  </main>
</body>
</html>"""
    page_path.write_text(doc, encoding="utf-8")
    return Path("articles", page_path.name).as_posix()


def write_topic_pages(site_root: Path, toc_entries: list[dict], article_links: dict[str, str]) -> None:
    topic_root = site_root / "topics"
    topic_root.mkdir(parents=True, exist_ok=True)
    for entry in toc_entries:
        slug = entry.get("slug") or slugify(entry["title_en"])
        target = article_links.get(entry.get("article_id", ""))
        link_text = "閱讀文章 / Read article" if target else "待建立文章頁 / Pending article page"
        href = f"../{target}" if target else "../index.html"
        doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(entry['title_zh'])} | {html.escape(entry['title_en'])}</title>
  <style>{site_css()}</style>
</head>
<body>
  <header><div class="wrap masthead">
    <p class="kicker">{html.escape(entry['section_zh'])} / {html.escape(entry['section_en'])} · p.{html.escape(str(entry['page']))}</p>
    <h1>{html.escape(entry['title_zh'])}<br><span class="title-en">{html.escape(entry['title_en'])}</span></h1>
  </div></header>
  <main class="wrap">
    <div class="nav"><a href="../index.html">← 返回目錄 / Back to contents</a></div>
    <section class="article-section"><p><a href="{html.escape(href)}">{html.escape(link_text)}</a></p></section>
  </main>
</body>
</html>"""
        (topic_root / f"{slug}.html").write_text(doc, encoding="utf-8")


def write_index(site_root: Path, config: dict, toc_entries: list[dict], cover_path: Path, article_links: dict[str, str]) -> None:
    phases = {int(phase["id"]): phase for phase in config.get("phases", default_phases())}
    grouped: dict[int, list[dict]] = {}
    for entry in toc_entries:
        phase_id = int(entry.get("phase") or phase_for_magazine_page(entry.get("page", 1)))
        grouped.setdefault(phase_id, []).append(entry)

    sections = []
    for phase_id in sorted(grouped):
        phase = phases.get(phase_id, {"title_zh": f"階段 {phase_id}", "title_en": f"Phase {phase_id}", "magazine_pages": ""})
        entries = grouped[phase_id]
        items = []
        for entry in entries:
            slug = entry.get("slug") or slugify(entry["title_en"])
            topic_href = article_links.get(entry.get("article_id", ""), f"topics/{slug}.html")
            items.append(
                f"""<li class="toc-item"><a href="{html.escape(topic_href)}">
  <span><span class="title-zh">{html.escape(entry['title_zh'])}</span><br><span class="title-en">{html.escape(entry['title_en'])}</span><br><span class="subtitle">{html.escape(entry['section_zh'])} / {html.escape(entry['section_en'])}</span></span>
  <span class="page-num">p.{html.escape(str(entry['page']))}</span>
</a></li>"""
            )
        sections.append(
            f"""<section class="toc-section">
  <h2>{html.escape(phase['title_zh'])}<br><span class="title-en">{html.escape(phase['title_en'])}</span></h2>
  <p class="subtitle">Magazine pages: {html.escape(str(phase.get('magazine_pages', '')))}</p>
  <ul class="toc-list">{''.join(items)}</ul>
</section>"""
        )

    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(config.get('site_title', 'Magazine Article Digest'))}</title>
  <style>{site_css()}</style>
</head>
<body>
  <header>
    <div class="wrap masthead">
      <p class="kicker">{html.escape(config.get('magazine', 'Source'))} · {html.escape(config.get('issue', 'April 2026'))}</p>
      <h1>雜誌目錄<br><span class="title-en">Magazine Contents</span></h1>
      <p class="subtitle">目錄內容以中英文併列，連結至各主題頁與已完成文章頁。</p>
    </div>
  </header>
  <main class="wrap">
    <div class="grid">
      <aside class="cover">
        <img src="{html.escape(rel_from_site(cover_path))}" alt="Magazine cover image">
      </aside>
      <section class="toc-card">
        {''.join(sections)}
      </section>
    </div>
  </main>
</body>
</html>"""
    (site_root / "index.html").write_text(doc, encoding="utf-8")


def write_markdown(article: dict, data: dict) -> None:
    body = f"""# {article.get('title_zh', '')} / {article.get('title_en') or article.get('title')}

## 中文完整摘要說明

{article.get('summary_zh', '')}

## 中文全文

{article.get('full_text_zh') or DEFAULT_FULL_TEXT_ZH}

## Original Full Text

{data.get('clean_ocr_text', data.get('ocr_text', ''))}
"""
    data["summary_path"].write_text(body, encoding="utf-8")


def write_notebooklm_docs(config: dict, article_data: list[dict]) -> None:
    lines = [f"# NotebookLM Import Plan: {config.get('notebook_title', '')}", ""]
    lines.append("```powershell")
    lines.append(f"nlm notebook create \"{config.get('notebook_title', 'Selected Articles')}\"")
    for data in article_data:
        lines.append(f"nlm source add <notebook-id> --file \"{data['pdf_path']}\"")
        lines.append(f"nlm source add <notebook-id> --file \"{data['summary_path']}\"")
    lines.append("```")
    (OUTPUT_DIR / "notebooklm-import-plan.md").write_text("\n".join(lines), encoding="utf-8")

    toc = ["# NotebookLM 建議目錄", ""]
    for data in article_data:
        article = data["article"]
        toc.append(f"- {article.get('title_zh', '')} / {article.get('title_en') or article.get('title')}")
    (OUTPUT_DIR / "notebooklm-suggested-toc.md").write_text("\n".join(toc), encoding="utf-8")


def write_phase_plan(config: dict, toc_entries: list[dict], selected_phase: int | None) -> None:
    phases = config.get("phases", default_phases())
    article_phase_counts: dict[int, int] = {}
    for article in config.get("articles", []):
        phase_id = int(article.get("phase") or 1)
        article_phase_counts[phase_id] = article_phase_counts.get(phase_id, 0) + 1

    lines = ["# 五階段雜誌處理計畫", ""]
    if selected_phase:
        lines.append(f"目前執行：Phase {selected_phase}")
        lines.append("")
    for phase in phases:
        phase_id = int(phase["id"])
        entries = [entry for entry in toc_entries if int(entry.get("phase") or phase_for_magazine_page(entry.get("page", 1))) == phase_id]
        lines.extend(
            [
                f"## {phase['title_zh']} / {phase['title_en']}",
                "",
                f"- 雜誌頁碼：{phase.get('magazine_pages', '')}",
                f"- 已設定文章數：{article_phase_counts.get(phase_id, 0)}",
                "- 目錄項目：",
            ]
        )
        for entry in entries:
            lines.append(f"  - {entry['title_zh']} / {entry['title_en']}（p.{entry['page']}）")
        lines.append("")
    (OUTPUT_DIR / "processing-phases.md").write_text("\n".join(lines), encoding="utf-8")


def run(config_path: Path, selected_phase: int | None = None) -> None:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    source_pdf = resolve_path(config_path, config["source_pdf"])
    reader = PdfReader(str(source_pdf))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    site_root = OUTPUT_DIR / "site"
    article_root = OUTPUT_DIR / "articles"
    asset_root = OUTPUT_DIR / "site-assets"
    site_root.mkdir(parents=True, exist_ok=True)
    article_root.mkdir(parents=True, exist_ok=True)
    asset_root.mkdir(parents=True, exist_ok=True)

    write_page_reports(scan_pages(reader))
    engine = detect_ocr_engine()

    # Cover image is the cover side of the first scanned spread.
    cover_source = export_page_images(reader, [1], asset_root / "source-pages")[0]
    cover_crop = crop_from_page_images([cover_source], [{"page": 1, "label": "cover", "kind": "image", "bbox_percent": [50, 0, 100, 100]}], asset_root)[0]

    article_data = []
    total_pages = len(reader.pages)
    configured_articles = list(enumerate(config.get("articles", []), start=1))
    if selected_phase is not None:
        configured_articles = [
            (index, article)
            for index, article in configured_articles
            if int(article.get("phase") or 1) == selected_phase
        ]

    for index, article in configured_articles:
        article.setdefault("title_en", article.get("title", "Untitled"))
        article.setdefault("title_zh", "面向未來的感受")
        article.setdefault("full_text_zh", DEFAULT_FULL_TEXT_ZH)
        article.setdefault("magazine_page", "5")
        pages = parse_pages(article["pages"], total_pages)
        slug = f"{index:03d}-{slugify(article.get('id') or article['title_en'])}"
        out_dir = article_root / slug
        image_dir = out_dir / "images"
        crop_dir = out_dir / "crops"
        ocr_dir = out_dir / "ocr"
        out_dir.mkdir(parents=True, exist_ok=True)

        pdf_path = out_dir / f"{slug}.pdf"
        summary_path = out_dir / "summary.md"
        write_article_pdf(reader, pages, pdf_path)
        page_images = export_page_images(reader, pages, image_dir)

        crop_defs = article.get("crops", [])
        crop_defs = crop_defs + article.get("display_images", []) + article.get("table_images", [])
        crops = crop_from_page_images(page_images, crop_defs, crop_dir)
        for crop in crops:
            if crop.get("kind") == "text":
                crop["ocr"] = run_ocr(crop["path"], ocr_dir, engine)
        ocr_text = collect_ocr_text([crop for crop in crops if crop.get("kind") == "text"])
        clean_text = clean_ocr_text(ocr_text, article)

        data = {
            "article": article,
            "slug": slug,
            "pdf_path": pdf_path,
            "summary_path": summary_path,
            "crops": crops,
            "ocr_text": ocr_text,
            "clean_ocr_text": clean_text,
        }
        write_markdown(article, data)
        article_data.append(data)

    article_links = {}
    for index, article in enumerate(config.get("articles", []), start=1):
        article_id = article.get("id")
        slug = f"{index:03d}-{slugify(article.get('id') or article.get('title_en') or article.get('title', 'article'))}"
        article_page = site_root / "articles" / f"{slug}.html"
        if article_id and article_page.exists():
            article_links[article_id] = Path("articles", article_page.name).as_posix()
        if article_id:
            article_slug = slugify(article_id)
            matching_pages = [
                page for page in (site_root / "articles").glob(f"*-{article_slug}.html")
                if re.match(rf"^\d{{3}}-{re.escape(article_slug)}\.html$", page.name)
            ]
            if matching_pages:
                newest_page = matching_pages[-1]
                article_links[article_id] = Path("articles", newest_page.name).as_posix()
    for data in article_data:
        href = write_article_page(site_root, data["article"], data)
        article_links[data["article"].get("id", data["slug"])] = href

    toc_entries = config.get("toc_entries") or DEFAULT_TOC
    write_topic_pages(site_root, toc_entries, article_links)
    write_index(site_root, config, toc_entries, cover_crop["path"], article_links)
    write_notebooklm_docs(config, article_data)
    write_phase_plan(config, toc_entries, selected_phase)

    manifest = {
        "source_pdf": str(source_pdf),
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "ocr_engine": engine["name"] if engine.get("available") else "none",
        "articles": [
            {
                "id": data["article"].get("id"),
                "title_en": data["article"].get("title_en"),
                "title_zh": data["article"].get("title_zh"),
                "pdf": str(data["pdf_path"]),
                "summary": str(data["summary_path"]),
            }
            for data in article_data
        ],
    }
    (OUTPUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Processed {len(article_data)} article(s)")
    if selected_phase is not None:
        print(f"Phase: {selected_phase}")
    print(f"Site: {site_root / 'index.html'}")
    print(f"OCR engine: {engine['name'] if engine.get('available') else 'none'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the magazine PDF MVP pipeline.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to articles.json")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3, 4, 5], help="Only process articles assigned to this phase")
    args = parser.parse_args()
    run(Path(args.config).resolve(), selected_phase=args.phase)


if __name__ == "__main__":
    main()
