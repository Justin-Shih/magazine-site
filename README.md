# Source April 2026 Magazine Site

This repository contains a local pipeline for turning the April 2026 issue of *The Source* magazine into:

- bilingual static web pages
- one page per selected article
- cropped article images and figures
- Traditional Chinese summaries and full-text notes
- per-article PDF exports
- NotebookLM-ready Markdown sources
- a GitHub Pages-ready `docs/` folder

The website is generated locally. GitHub only serves the static files from `docs/`.

## Website

Open locally:

```text
output/site/index.html
```

GitHub Pages publishes from:

```text
docs/index.html
```

The `docs/.nojekyll` file is included so GitHub Pages serves the static files directly without Jekyll processing.

## Main Commands

Regenerate all article outputs and the local website:

```powershell
python scripts/run_mvp.py
```

Regenerate a single phase:

```powershell
python scripts/run_mvp.py --phase 5
```

Sync the generated website into `docs/` for GitHub Pages:

```powershell
python scripts/publish_site.py
```

Prepare NotebookLM-ready Markdown sources:

```powershell
python scripts/prepare_notebooklm_package.py
```

## GitHub Pages Setup

In the GitHub repository:

1. Go to `Settings`.
2. Open `Pages`.
3. Set source to `Deploy from a branch`.
4. Select branch `main`.
5. Select folder `/docs`.
6. Save.

Upload or commit these important paths:

```text
README.md
config/
scripts/
docs/
docs/.nojekyll
```

## Output Structure

```text
output/site/
  index.html
  articles/
  topics/

output/articles/
  001-.../
    summary.md
    article.pdf
    crops/
    ocr/

output/notebooklm/
  sources/
  sources-manifest.json
  index.md
  notebook-outline.md
  upload-order.md
  manual-import-guide.md
  notebooklm-prompts.md
  automated-import-plan.md
  quality-report.md

docs/
  index.html
  articles/
  article-assets/
  site-assets/
  .nojekyll
```

## Configuration

Article definitions, crop boxes, titles, summaries, and table-of-contents links are managed in:

```text
config/articles.json
```

Page crop boxes use:

```text
[left, top, right, bottom]
```

as percentages of the extracted full-page image.

## Notes

- The working PDF and OCR process are best run on a local disk, not directly inside a cloud-synced folder, to avoid file locks and slow sync behavior.
- The `docs/` folder is the deployable website package.
- NotebookLM upload is prepared but not automatically performed unless a target existing notebook is selected.
