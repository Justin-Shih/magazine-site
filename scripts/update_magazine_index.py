from __future__ import annotations

import argparse
import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCS = ROOT / "docs"
MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


def title_from_slug(slug: str) -> str:
    words = [part for part in re.split(r"[-_]+", slug) if part]
    return " ".join(word.upper() if word.lower() in {"ai", "nblm"} else word.capitalize() for word in words)


def read_page_title(index_path: Path, slug: str) -> str:
    text = index_path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"<title>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return title_from_slug(slug)

    title = html.unescape(re.sub(r"\s+", " ", match.group(1))).strip()
    if not title or "\ufffd" in title or "?" in title:
        return title_from_slug(slug)
    return title


def issue_date(slug: str) -> tuple[int, int]:
    match = re.search(
        r"(january|february|march|april|may|june|july|august|september|october|november|december)-(\d{4})",
        slug,
        flags=re.IGNORECASE,
    )
    if not match:
        return (0, 0)
    return (int(match.group(2)), MONTHS[match.group(1).lower()])


def discover_issues(docs_dir: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for child in sorted(docs_dir.iterdir(), key=lambda path: path.name.lower()):
        if not child.is_dir():
            continue
        index_path = child / "index.html"
        if not index_path.exists():
            continue
        year, month = issue_date(child.name)
        issues.append(
            {
                "slug": child.name,
                "title": read_page_title(index_path, child.name),
                "path": f"{child.name}/",
                "year": year,
                "month": month,
            }
        )
    return sorted(
        issues,
        key=lambda issue: (issue["year"], issue["month"], issue["slug"]),
        reverse=True,
    )


def render_index(issues: list[dict[str, str]]) -> str:
    issue_groups: list[str] = []
    issues_by_year: dict[int, list[dict[str, str]]] = {}
    for issue in issues:
        issues_by_year.setdefault(issue["year"], []).append(issue)

    for year, year_issues in issues_by_year.items():
        issue_items = []
        for issue in year_issues:
            title = html.escape(issue["title"])
            path = html.escape(issue["path"])
            slug = html.escape(issue["slug"])
            issue_items.append(
                f"""          <li class="issue">
          <a href="{path}">{title}</a>
          <p>GitHub Pages path: <code>/{slug}/</code></p>
        </li>"""
            )
        year_label = str(year) if year else "其他"
        year_items_html = "\n".join(issue_items)
        issue_groups.append(
            f"""        <section class="year-group">
          <h2>{year_label}</h2>
          <ul class="issue-list">
{year_items_html}
          </ul>
        </section>"""
        )

    if not issue_groups:
        issue_groups.append(
            """        <section class="year-group">
          <p>尚未發布任何雜誌期別。</p>
        </section>"""
        )

    issues_html = "\n".join(issue_groups)
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Magazine Site</title>
  <style>
    :root {{
      --paper: #f7f6f2;
      --ink: #1e2732;
      --muted: #667085;
      --line: #d8ddd8;
      --accent: #0b6f78;
      --panel: #ffffff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      background: var(--paper);
      font-family: "Segoe UI", "Microsoft JhengHei", Arial, sans-serif;
      line-height: 1.7;
    }}
    header {{
      background: var(--panel);
      border-bottom: 1px solid var(--line);
    }}
    .wrap {{
      width: min(980px, calc(100% - 36px));
      margin: 0 auto;
    }}
    .masthead {{ padding: 30px 0 22px; }}
    .kicker {{
      margin: 0 0 4px;
      color: var(--accent);
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 34px;
      line-height: 1.2;
      letter-spacing: 0;
    }}
    .subtitle {{ margin: 0; color: var(--muted); }}
    main {{ padding: 28px 0 56px; }}
    .year-group + .year-group {{ margin-top: 28px; }}
    h2 {{
      margin: 0 0 12px;
      font-size: 24px;
      letter-spacing: 0;
    }}
    .issue-list {{
      display: grid;
      gap: 14px;
      padding: 0;
      margin: 0;
      list-style: none;
    }}
    .issue {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }}
    .issue a {{
      color: var(--ink);
      font-size: 20px;
      font-weight: 750;
      text-decoration: none;
    }}
    .issue a:hover {{ color: var(--accent); }}
    .issue p {{ margin: 6px 0 0; color: var(--muted); }}
  </style>
</head>
<body>
  <header>
    <div class="wrap masthead">
      <p class="kicker">Magazine Site</p>
      <h1>雜誌導出網站索引</h1>
      <p class="subtitle">每一期雜誌使用獨立目錄發布，避免後續期別覆蓋總入口。</p>
    </div>
  </header>
  <main>
    <div class="wrap">
      <div class="issue-years">
{issues_html}
      </div>
    </div>
  </main>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Regenerate the magazine-site root index from docs/*/index.html.")
    parser.add_argument("--docs", type=Path, default=DEFAULT_DOCS)
    args = parser.parse_args()

    docs_dir = args.docs if args.docs.is_absolute() else ROOT / args.docs
    docs_dir.mkdir(parents=True, exist_ok=True)
    issues = discover_issues(docs_dir)
    (docs_dir / "index.html").write_text(render_index(issues), encoding="utf-8")
    print(f"Updated magazine index: {docs_dir / 'index.html'} ({len(issues)} issue(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
