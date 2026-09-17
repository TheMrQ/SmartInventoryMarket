# Troubleshooting and Recovery

## 2026-09-17 — Kaggle CLI authentication required for M5 acquisition

Symptom:

`.\\.venv\\Scripts\\kaggle.exe competitions files m5-forecasting-accuracy` returned `Authentication required to call the Kaggle API.`

Root cause:

The project virtual environment had no authenticated Kaggle CLI session.

Fix:

User must run `.\\.venv\\Scripts\\kaggle.exe auth login` and complete its browser-based OAuth flow outside the repository. Accept M5 competition rules if prompted. Do not add a token, `kaggle.json`, or `.env` credential to the repository.

Verification:

Rerun the competition file-list command successfully before starting the download.

Files changed:

`requirements-dev.txt`, `docs/00_project_status.md`, `docs/05_experiments.md`, `docs/06_dataset.md`, `docs/04_troubleshooting.md`, `docs/CHANGELOG.md`.

Prevention:

Use a harmless metadata/file-list call before every protected Kaggle acquisition and never store credentials in repository files.

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
