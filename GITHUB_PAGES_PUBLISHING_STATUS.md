# GitHub Pages Publishing Status

Last updated: 2026-07-10

## Current Local Publishing Copy

This C drive folder is the Git-friendly working copy for publishing the magazine site:

```text
C:\Justin\Codex\projects\雜誌分析導出網頁與NBLM筆記
```

It was created from the Google Drive source project:

```text
G:\我的雲端硬碟\@@Codex\雜誌分析導出網頁與NBLM筆記
```

Copied into this working copy:

```text
README.md
config/
scripts/
docs/
.gitignore
```

Not copied intentionally:

```text
Source April 2026.pdf
output/
input/
```

## Git Status

Git repository initialized:

```powershell
git init -b main
```

Current repository status:

```text
untracked:
  .gitignore
  README.md
  config/
  docs/
  scripts/
```

Initial commit has been created. To inspect the current commit:

```powershell
git log --oneline --decorate -1
```

2026-07-10 check:

- Repository is initialized on branch `main`.
- Initial commit exists on `main`.
- No `origin` remote is configured.
- Running Git from the Codex sandbox requires a one-off safe-directory override because the repository is owned by the Windows user and Codex runs as a sandbox user:

```powershell
git -c safe.directory='C:/Justin/Codex/projects/雜誌分析導出網頁與NBLM筆記' -C 'C:\Justin\Codex\projects\雜誌分析導出網頁與NBLM筆記' status --short --branch
```

- Local Git author is configured for this repository:

```text
user.name=Justin-Shih
user.email=<redacted-email>
```

- The GitHub connector returned no accessible repositories, so the intended GitHub repository URL still must be provided manually.

Recommended new GitHub repository name:

```text
magazine-site
```

## Size Check

The GitHub Pages `docs/` package from the Google Drive source has:

```text
134 files
about 113 MB total
largest file about 5.09 MB
```

No single file was found near GitHub's 100 MB file limit.

## Push Status

Remote repository:

```text
https://github.com/Justin-Shih/magazine-site.git
```

Push completed:

```text
main -> origin/main
```

GitHub Pages is configured:

```text
Deploy from a branch -> main -> /docs
```

Verified public URLs:

```text
https://justin-shih.github.io/magazine-site/
https://justin-shih.github.io/magazine-site/source-april-2026-magazine-site/
```

## Magazine Site Structure

The GitHub repository `magazine-site` is the stable category-level home for magazine website publishing.

Each magazine issue should be published as its own issue-level homepage under `docs/`, using a directory named for the magazine and issue date. This prevents future issues from overwriting the root homepage.

Current issue homepage:

```text
docs/source-april-2026-magazine-site/index.html
```

Future magazine issue examples:

```text
docs/source-may-2026-magazine-site/index.html
docs/source-june-2026-magazine-site/index.html
docs/another-magazine-july-2026-site/index.html
```

The root page is an index:

```text
docs/index.html
```

Use `scripts/publish_site.py --site-slug <issue-slug>` for future issue publishing.

Root index maintenance is automated:

```powershell
python scripts/update_magazine_index.py
```

`scripts/publish_site.py --site-slug <issue-slug>` also refreshes `docs/index.html` after publishing the issue folder.

## Next Commands

For the next magazine issue, publish into a new issue folder:

```powershell
python scripts/publish_site.py --site-slug source-may-2026-magazine-site
```
