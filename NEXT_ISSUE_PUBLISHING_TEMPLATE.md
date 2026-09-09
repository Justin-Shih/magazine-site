# Next Issue Publishing Template

Use this checklist only after a new issue has been built and validated in:

`C:\Justin\Codex\magazine-july-2026-work`

This is the existing `Justin-Shih/magazine-site` GitHub Pages publishing procedure, not a separate workflow.

## Naming

Use the canonical issue ID plus `-magazine-site`:

```text
Canonical issue ID: source-december-2025
Pages site slug:   source-december-2025-magazine-site
```

The public URL is:

```text
https://justin-shih.github.io/magazine-site/<issue-id>-magazine-site/
```

## Publish

1. In the canonical project, confirm the issue site and cross-issue index pass their validators.
2. Confirm `docs/issues/<issue-id>/index.html` exists.
3. Run the established safe publishing entry:

```powershell
python scripts\publish_site.py --issue-id <issue-id>
```

4. In this Pages repository, confirm these outputs:

```text
docs/<issue-id>-magazine-site/index.html
docs/<issue-id>-magazine-site/articles/
docs/index.html
docs/.nojekyll
```

5. Verify the root index is grouped by year newest to oldest, with issues newest to oldest inside each year.
6. Open the root and issue pages locally. Verify every article link, image, title, and mobile/desktop layout.
7. Check total and largest file sizes. Do not publish a file at or above GitHub's 100 MB hard limit.
8. Review and commit only the intended public files:

```powershell
git status
git diff --check
git add docs/index.html docs/<issue-id>-magazine-site
git commit -m "Publish <issue name> magazine site"
git push origin main
```

9. Verify both public URLs return HTTP 200 and contain the expected issue link and article count:

```text
https://justin-shih.github.io/magazine-site/
https://justin-shih.github.io/magazine-site/<issue-id>-magazine-site/
```

## Rules

- Do not publish a new issue directly into the `docs/` root.
- Do not create another GitHub Pages workflow or repository.
- Do not bypass the canonical issue-site and index validators.
- Do not commit source PDFs, OCR working files, NotebookLM private routing data, credentials, tokens, or private workflow state.
- Do not commit or push without explicit publication authorization.
- Keep each issue self-contained under `docs/<issue-id>-magazine-site/`.
