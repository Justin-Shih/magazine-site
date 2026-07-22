# GitHub Pages Publishing Status

Last updated: 2026-07-22

## Repository Status

- Canonical repository: `Justin-Shih/magazine-site`
- Default branch: `main`
- Local branch tracks `origin/main`
- GitHub Pages source: `main` branch, `/docs`
- Reachable privacy-cleaned baseline: `f0dd8d4`
- Exact repository path is trusted through the global Git `safe.directory` configuration; no per-command override is required.

The private source workspace and cloud storage location are maintained separately. Do not record workstation paths, cloud-drive paths, private account addresses, NotebookLM IDs, credentials, or tokens in this tracked status file.

## Publishing Scope

The repository contains the Git-friendly publishing package:

```text
README.md
config/
scripts/
docs/
.gitignore
```

Private or generated source material is intentionally excluded:

```text
source magazine PDFs
input/
output/
NotebookLM private routing data
local configuration and credentials
```

## Size Baseline

The original `docs/` package contained approximately 134 files and 113 MB in total. Its largest file was approximately 5.09 MB, below GitHub's individual 100 MB file limit.

Recheck file sizes before publishing each new issue rather than assuming this historical baseline is still current.

## GitHub Pages Status

Pages is configured as:

```text
Deploy from a branch -> main -> /docs
```

The public root and current issue page were verified successfully after the 2026-07-22 privacy cleanup.

## Magazine Site Structure

The GitHub repository `magazine-site` is the stable category-level home for magazine website publishing.

Each magazine issue must use its own issue-level folder under `docs/` so future issues do not overwrite the root homepage.

Current issue homepage:

```text
docs/source-april-2026-magazine-site/index.html
```

Future issue examples:

```text
docs/source-may-2026-magazine-site/index.html
docs/source-june-2026-magazine-site/index.html
docs/another-magazine-july-2026-site/index.html
```

The root index is:

```text
docs/index.html
```

Use the existing scripts for future issues:

```powershell
python scripts/publish_site.py --site-slug <issue-slug>
python scripts/update_magazine_index.py
```

Use `NEXT_ISSUE_PUBLISHING_TEMPLATE.md` as the step-by-step checklist.

## Git Privacy Cleanup — 2026-07-22

- Rewrote all reachable `main` history to remove personal Gmail values from tracked content.
- Replaced reachable commit author and committer emails with the GitHub ID-based noreply address.
- Verified the rewritten local and GitHub histories contain zero Gmail values.
- Verified GitHub Pages rebuilt successfully from the rewritten `main` branch.
- Confirmed the repository had no forks or pull requests retaining the old reachable history at cleanup time.
- Old unreachable commit objects may remain temporarily accessible through GitHub object caching. A GitHub Support purge is optional if permanent cache removal is required.
- Clones created before the cleanup must be discarded and cloned again; do not merge or push their old history.
