# Troubleshooting and Recovery

## 2026-09-17 — Kaggle CLI authentication required for M5 acquisition — RESOLVED

Symptom:

`.\\.venv\\Scripts\\kaggle.exe competitions files m5-forecasting-accuracy` returned `Authentication required to call the Kaggle API.`

Root cause:

The project virtual environment had no authenticated Kaggle CLI session.

Fix:

User ran `.\\.venv\\Scripts\\kaggle.exe auth login` and completed its browser-based OAuth flow outside the repository. No token, `kaggle.json`, or `.env` credential was added to the repository.

Verification:

The competition file-list command successfully returned the five official M5 files.

Files changed:

`requirements-dev.txt`, `docs/00_project_status.md`, `docs/05_experiments.md`, `docs/06_dataset.md`, `docs/04_troubleshooting.md`, `docs/CHANGELOG.md`.

Prevention:

Use a harmless metadata/file-list call before every protected Kaggle acquisition and never store credentials in repository files.

## 2026-09-17 — M5 download forbidden after successful Kaggle authentication

Symptom:

`.\\.venv\\Scripts\\kaggle.exe competitions download m5-forecasting-accuracy -p data\\raw\\m5` returned `403 Client Error: Forbidden for url: https://api.kaggle.com/v1/competitions.CompetitionApiService/DownloadDataFiles`.

Root cause:

Authentication is valid because the file listing succeeds, but the authenticated account does not currently have download access. Competition-rule acceptance or account access confirmation is required.

Fix:

While signed in to Kaggle, visit `https://www.kaggle.com/competitions/m5-forecasting-accuracy/rules` and accept/confirm the competition terms. Then rerun the download command.

Verification:

The archive downloads to `data/raw/m5/`, extracts to the official files, and remains Git-ignored.

Files changed:

`docs/00_project_status.md`, `docs/04_troubleshooting.md`, `docs/05_experiments.md`, `docs/06_dataset.md`, `docs/CHANGELOG.md`.

Prevention:

Treat a successful file list as authentication verification only; verify download authorization separately before creating an audit plan.

## Problem Record Template

## YYYY-MM-DD — Problem title

Symptom:

Root cause:

Fix:

Verification:

Files changed:

Prevention:

# Context Reset Recovery

When an AI agent loses context:

1. Read `AGENTS.md`.
2. Read `docs/00_project_status.md`.
3. Read the latest `CHANGELOG` entries.
4. Check Last Stable Checkpoint.
5. Read Next Exact Step.
6. Read Known Blockers.
7. Run verification commands.
8. Continue from repository state.
9. Do not redo tasks already marked `DONE` unless verification fails.
