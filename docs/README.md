# Long-term Memory — Human Quick Guide

This folder is the project memory for both the user and AI agents. You do **not** need to read every file every time.

## If You Only Want to Know Where the Project Is Now

Read [Project Status](00_project_status.md). It records completed work, the current task, the latest stable checkpoint, blockers, and the exact next step.

## Current Decisions

- Official forecasting dataset: M5 Forecasting - Accuracy.
- Inventory-policy evaluation: explicitly simulated inventory and replenishment state; never presented as observed Walmart operations.
- Application database: MySQL, administered/designed with MySQL Workbench and accessed by FastAPI through SQLAlchemy.
- Sales ingestion: initial historical CSV import for the thesis MVP, with a future POS/API integration boundary for ongoing sales sync.

## Status Markers

Use these human-readable markers consistently in project status: 🟢 **DONE**, 🟡 **IN_PROGRESS**, ⚪ **TODO**, 🔴 **BLOCKED**, and 🔵 **OPTIONAL**. The underlying status words remain the project’s canonical values.

## What Each File Is For

- **`00_project_status.md`** — current progress / save point of the whole project.
- **`01_architecture.md`** — how the web app, forecasting pipeline, database, ingestion, and inventory decision engine fit together.
- **`02_database_schema.md`** — planned database tables, relationships, and technology decisions.
- **`03_features/`** — detailed notes for inventory management, forecasting, decision engine, and dashboard.
- **`04_troubleshooting.md`** — errors, fixes, and context-recovery steps.
- **`05_experiments.md`** — future forecasting/inventory experiments, metrics, results, and decisions.
- **`06_dataset.md`** — dataset decision, audit evidence, limitations, and data assumptions.
- **`CHANGELOG.md`** — chronological history of notable changes/checkpoints.

## Recommended Reading Order

Most of the time, read only:

1. `00_project_status.md`
2. `06_dataset.md` for dataset work
3. `05_experiments.md` when model training starts
4. `CHANGELOG.md` to see what changed

The other files allow Codex or another AI agent to recover complete project context without relying on old chat history. After every meaningful task, update the relevant memory file, record the checkpoint/next step, then commit and push the change together with code whenever practical.
