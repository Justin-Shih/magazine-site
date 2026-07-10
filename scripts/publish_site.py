from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "output" / "site"
DEFAULT_DEST = ROOT / "docs"
ARTICLE_OUTPUT = ROOT / "output" / "articles"
SITE_ASSETS_OUTPUT = ROOT / "output" / "site-assets"


def copy_site(source: Path, dest: Path) -> None:
    if not (source / "index.html").exists():
        raise FileNotFoundError(f"Missing site entry: {source / 'index.html'}")
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest)
    (dest / ".nojekyll").write_text("", encoding="utf-8")


def linked_article_pages(dest: Path) -> set[str]:
    index_path = dest / "index.html"
    text = index_path.read_text(encoding="utf-8")
    return set(re.findall(r'href="articles/([^"]+\.html)"', text))


def copy_publish_assets(dest: Path) -> None:
    if SITE_ASSETS_OUTPUT.exists():
        shutil.copytree(SITE_ASSETS_OUTPUT, dest / "site-assets")

    linked_pages = linked_article_pages(dest)
    linked_slugs = {Path(page).stem for page in linked_pages}

    articles_dir = dest / "articles"
    for html_path in articles_dir.glob("*.html"):
        if html_path.name not in linked_pages:
            html_path.unlink()

    asset_dest = dest / "article-assets"
    asset_dest.mkdir(parents=True, exist_ok=True)
    for slug in sorted(linked_slugs):
        source_dir = ARTICLE_OUTPUT / slug
        crops_dir = source_dir / "crops"
        if crops_dir.exists():
            shutil.copytree(crops_dir, asset_dest / slug / "crops")


def rewrite_paths(dest: Path) -> None:
    for html_path in dest.rglob("*.html"):
        text = html_path.read_text(encoding="utf-8")
        text = text.replace("../site-assets/", "site-assets/")
        text = text.replace("../../articles/", "../article-assets/")
        html_path.write_text(text, encoding="utf-8")


def git_available() -> bool:
    return shutil.which("git") is not None


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def maybe_git_publish(commit_message: str, push: bool) -> None:
    if not git_available():
        print("Git is not available in PATH; skipped git commit/push.")
        return

    status = run_git(["status", "--short"])
    if status.returncode != 0:
        print(status.stderr.strip() or status.stdout.strip())
        print("Skipped git commit/push because this folder is not a ready git repo.")
        return

    run_git(["add", "docs", "scripts/publish_site.py", "README.md"])
    status_after_add = run_git(["status", "--short"])
    if not status_after_add.stdout.strip():
        print("No git changes to commit.")
        return

    commit = run_git(["commit", "-m", commit_message])
    if commit.returncode != 0:
        print(commit.stderr.strip() or commit.stdout.strip())
        print("Git commit did not complete.")
        return
    print(commit.stdout.strip())

    if push:
        pushed = run_git(["push"])
        if pushed.returncode != 0:
            print(pushed.stderr.strip() or pushed.stdout.strip())
            print("Git push did not complete.")
            return
        print(pushed.stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish generated static site to docs/ for GitHub Pages.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--commit", action="store_true", help="Commit docs/ changes when git is available.")
    parser.add_argument("--push", action="store_true", help="Push after committing. Implies --commit.")
    parser.add_argument("--message", default="Publish generated site")
    args = parser.parse_args()

    source = args.source if args.source.is_absolute() else (ROOT / args.source)
    dest = args.dest if args.dest.is_absolute() else (ROOT / args.dest)

    copy_site(source.resolve(), dest.resolve())
    copy_publish_assets(dest.resolve())
    rewrite_paths(dest.resolve())
    print(f"Copied site: {source.resolve()} -> {dest.resolve()}")
    print(f"GitHub Pages folder: {dest.resolve()}")

    if args.commit or args.push:
        maybe_git_publish(args.message, args.push)
    return 0


if __name__ == "__main__":
    sys.exit(main())
