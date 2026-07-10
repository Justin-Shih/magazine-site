# Next Issue Publishing Template

Use this checklist when publishing a new magazine issue into `magazine-site`.

## Naming

Use one stable issue slug per magazine issue:

```text
<magazine-name>-<month>-<year>-magazine-site
```

Examples:

```text
source-april-2026-magazine-site
source-may-2026-magazine-site
source-june-2026-magazine-site
```

If the magazine name is not Source, replace the first word:

```text
another-magazine-july-2026-site
```

## Publish Flow

1. Place the new PDF and update `config/articles.json` for the new issue.
2. Generate local article outputs:

```powershell
python scripts/run_mvp.py
```

3. Publish into a new issue folder:

```powershell
python scripts/publish_site.py --site-slug source-may-2026-magazine-site
```

4. Confirm the generated issue folder exists:

```text
docs/source-may-2026-magazine-site/index.html
```

5. Confirm `docs/index.html` includes the new issue. It is refreshed automatically by `publish_site.py`.
6. Check the website locally from the `docs/` folder before committing.
7. Commit and push:

```powershell
git status
git add README.md config scripts docs NEXT_ISSUE_PUBLISHING_TEMPLATE.md
git commit -m "Publish Source May 2026 magazine site"
git push origin main
```

8. Verify the public URLs after GitHub Pages deploys:

```text
https://justin-shih.github.io/magazine-site/
https://justin-shih.github.io/magazine-site/source-may-2026-magazine-site/
```

## Rules

- Do not publish a new issue directly into `docs/`.
- Do not replace `docs/index.html` by hand unless `scripts/update_magazine_index.py` cannot run.
- Keep each issue self-contained under `docs/<issue-slug>/`.
- Keep `magazine-site` as the category-level entrance.
