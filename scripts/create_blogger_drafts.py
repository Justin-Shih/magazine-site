from __future__ import annotations

import argparse
import json
import re
import shutil
from dataclasses import dataclass, asdict
from html import escape
from pathlib import Path

from bs4 import BeautifulSoup


@dataclass
class Article:
    slug: str
    article_file: str
    title: str
    title_zh: str
    title_en: str
    kicker: str
    subtitle: str
    summary: str
    chinese_text: str
    original_text: str
    images: list[str]


def text_norm(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def split_bilingual_title(title: str) -> tuple[str, str]:
    title = text_norm(title)
    if " | " in title:
        zh, en = title.split(" | ", 1)
        return zh.strip(), en.strip()
    if re.search(r"[\u4e00-\u9fff]", title):
        match = re.match(r"^(.+?)\s+([A-Z][A-Za-z0-9 '&,;:()\-]+)$", title)
        if match:
            return match.group(1).strip(), match.group(2).strip()
        parts = title.split()
        if len(parts) > 1:
            for i, part in enumerate(parts):
                if re.match(r"[A-Za-z]", part) and i > 0:
                    return " ".join(parts[:i]).strip(), " ".join(parts[i:]).strip()
    return title, title


def section_text(soup: BeautifulSoup, heading: str) -> str:
    h2 = next((h for h in soup.find_all("h2") if text_norm(h.get_text()).startswith(heading)), None)
    if not h2:
        return ""
    container = h2.parent
    parts = []
    for node in container.find_all(["p", "div"], recursive=False):
        if node.name == "div":
            if "inline-figures" in (node.get("class") or []):
                continue
            parts.append(text_norm(node.get_text(" ", strip=True)))
        else:
            parts.append(text_norm(node.get_text(" ", strip=True)))
    return "\n\n".join([p for p in parts if p])


def parse_article(path: Path) -> Article:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    h1 = soup.find("h1")
    title = text_norm(h1.get_text(" ", strip=True) if h1 else path.stem)
    title_zh, title_en = split_bilingual_title(title)
    kicker = text_norm((soup.find(class_="kicker") or "").get_text(" ", strip=True))
    subtitle = text_norm((soup.find(class_="subtitle") or "").get_text(" ", strip=True))
    summary = section_text(soup, "中文完整摘要說明")
    chinese_text = section_text(soup, "中文全文")
    original_text = section_text(soup, "Original Full Text")
    images = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if src and "article-assets" in src:
            images.append(src.replace("../", ""))
    return Article(
        slug=path.stem,
        article_file=f"articles/{path.name}",
        title=title,
        title_zh=title_zh,
        title_en=title_en,
        kicker=kicker,
        subtitle=subtitle,
        summary=summary,
        chinese_text=chinese_text,
        original_text=original_text,
        images=images,
    )


def copy_asset(src_root: Path, out_assets: Path, rel: str) -> str | None:
    src = src_root / rel
    if not src.exists():
        return None
    dest = out_assets / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return str(Path("assets") / rel).replace("\\", "/")


def image_tag(local_src: str | None, alt: str) -> str:
    if not local_src:
        return ""
    return (
        f'<figure class="mag-figure">'
        f'<img src="{escape(local_src)}" alt="{escape(alt)}" style="max-width:100%;height:auto;" />'
        f'</figure>'
    )


def article_block(article: Article, local_image: str | None, base_url: str) -> str:
    link = f"{base_url.rstrip('/')}/{article.article_file}" if base_url else article.article_file
    subtitle = f"<p>{escape(article.subtitle)}</p>" if article.subtitle else ""
    summary = escape(article.summary).replace("\n\n", "</p><p>")
    return f"""
<section class="mag-article">
  <h3>{escape(article.title_zh)}<br><span>{escape(article.title_en)}</span></h3>
  {image_tag(local_image, article.title)}
  {subtitle}
  <p>{summary}</p>
  <p><a href="{escape(link)}">閱讀完整網頁整理</a></p>
</section>
""".strip()


def build_issue_html(articles: list[Article], asset_map: dict[str, str], base_url: str) -> str:
    cover = asset_map.get("site-assets/page-001-cover.jpg")
    blocks = "\n\n".join(
        article_block(a, asset_map.get(a.images[0]) if a.images else None, base_url)
        for a in articles
    )
    return f"""
<article class="source-april-2026-report">
  <p><strong>《The Source》2026年4月號</strong>聚焦國際水協會（IWA）近期議題，從水安全、衛生治理、循環用水、區域合作、數位水務到研究創新，呈現全球水領域面對氣候風險與基礎設施轉型時的多線進展。</p>
  {image_tag(cover, "The Source April 2026 cover")}

  <h2>本期重點</h2>
  <ul>
    <li>水安全與衛生治理已從單一工程問題，轉向跨部門、跨尺度、跨治理層級的系統議題。</li>
    <li>循環用水、非下水道衛生、地下水管理與區域水共享，成為韌性基礎設施的重要方向。</li>
    <li>年輕水專業人才、區域夥伴關係與國際會議平台，正在形塑後 SDG 時代的水治理議程。</li>
    <li>數位工具、感測、AI、衛星資料與決策支援系統，逐步進入水務營運與風險管理。</li>
    <li>研究創新與實務案例顯示，水、能源、糧食、健康與城市治理之間的連動愈來愈明顯。</li>
  </ul>

  <h2>文章導讀</h2>
  {blocks}

  <h2>建議閱讀路徑</h2>
  <p>若關心水治理與國際議程，可先讀會長專欄、IWA 新聞與曼谷水與發展大會報導。若關心技術實務，可從園藝循環用水、非下水道衛生、數位解決方案與研究創新切入。若關心區域案例，尼泊爾、西巴爾幹與斯里蘭卡的文章可串成一條發展與健康風險的閱讀線。</p>

  <p><em>資料來源：The Source, April 2026。本文為雜誌內容整理與繁體中文導讀草稿。</em></p>
</article>
""".strip()


def build_single_article_html(article: Article, asset_map: dict[str, str], base_url: str) -> str:
    image_html = "\n".join(image_tag(asset_map.get(img), article.title) for img in article.images[:3])
    link = f"{base_url.rstrip('/')}/{article.article_file}" if base_url else article.article_file
    summary = escape(article.summary).replace("\n\n", "</p><p>")
    chinese = escape(article.chinese_text).replace("\n\n", "</p><p>")
    return f"""
<article class="source-article-draft">
  <p><strong>{escape(article.kicker)}</strong></p>
  <p>{escape(article.subtitle)}</p>
  {image_html}
  <h2>中文導讀</h2>
  <p>{summary}</p>
  <h2>中文整理</h2>
  <p>{chinese}</p>
  <p><a href="{escape(link)}">閱讀網頁版與原文全文</a></p>
</article>
""".strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs", default="docs", help="Generated site docs directory")
    parser.add_argument("--out", default="output/blogger", help="Output draft directory")
    parser.add_argument("--base-url", default="", help="Public site base URL for article links")
    args = parser.parse_args()

    docs = Path(args.docs)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    assets = out / "assets"
    articles = [parse_article(p) for p in sorted((docs / "articles").glob("*.html"))]

    asset_map: dict[str, str] = {}
    cover_rel = "site-assets/page-001-cover.jpg"
    copied = copy_asset(docs, assets, cover_rel)
    if copied:
        asset_map[cover_rel] = copied
    for article in articles:
        for img in article.images:
            copied = copy_asset(docs, assets, img)
            if copied:
                asset_map[img] = copied

    issue_title = "《The Source》2026年4月號：水安全、韌性治理與創新實務的17篇觀察"
    issue_html = build_issue_html(articles, asset_map, args.base_url)
    (out / "source-april-2026-blogger-draft.html").write_text(issue_html, encoding="utf-8")

    md_lines = [f"# {issue_title}", "", "## 本期文章"]
    for article in articles:
        md_lines.append(f"- {article.title_zh} / {article.title_en}: {article.summary[:120]}...")
    (out / "source-april-2026-blogger-draft.md").write_text("\n".join(md_lines), encoding="utf-8")

    posts = [
        {
            "title": issue_title,
            "labels": ["The Source", "IWA", "水資源", "水安全", "雜誌導讀"],
            "status": "draft",
            "content_html": issue_html,
        }
    ]

    per_article_dir = out / "article-drafts"
    per_article_dir.mkdir(exist_ok=True)
    for article in articles:
        html = build_single_article_html(article, asset_map, args.base_url)
        post_title = f"{article.title_zh}｜{article.title_en}"
        (per_article_dir / f"{article.slug}.html").write_text(html, encoding="utf-8")
        posts.append(
            {
                "title": post_title,
                "labels": ["The Source", "IWA", "水資源", "雜誌導讀"],
                "status": "draft",
                "content_html": html,
                "source": asdict(article),
            }
        )

    (out / "blogger-drafts.json").write_text(
        json.dumps({"posts": posts, "assets": asset_map}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    guide = f"""# Blogger 草稿包

已產生：

- `source-april-2026-blogger-draft.html`：一篇總覽式網誌報導草稿。
- `source-april-2026-blogger-draft.md`：Markdown 摘要版。
- `blogger-drafts.json`：可供後續 Blogger API / Apps Script 匯入的資料。
- `article-drafts/`：17 篇單篇草稿 HTML。
- `assets/`：草稿引用的封面與文章圖片。

注意：Blogger 正式發布時，圖片需要是 Blogger/Google 相簿或公開網站 URL。若直接貼 HTML，請先在 Blogger 編輯器上傳圖片，或用 `--base-url` 指向已發布的 GitHub Pages 網站。
"""
    (out / "README.md").write_text(guide, encoding="utf-8")
    print(f"Wrote {len(posts)} draft posts to {out}")


if __name__ == "__main__":
    main()

