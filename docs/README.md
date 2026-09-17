# Documentation Guide

The `docs/` directory is the permanent, human-readable memory for Smart Inventory Market. Start with [Project Status](00_project_status.md), then read the architecture and the task-specific document listed in `AGENTS.md`.

## Current Decisions

- Official forecasting dataset: M5 Forecasting - Accuracy.
- Inventory-policy evaluation: explicitly simulated inventory and replenishment state; never presented as observed Walmart operations.
- Application database: MySQL, administered/designed with MySQL Workbench and accessed by FastAPI through SQLAlchemy.
- Sales ingestion: initial historical CSV import for the thesis MVP, with a future POS/API integration boundary for ongoing sales sync.

## Main Documents

- `00_project_status.md` — roadmap, stable checkpoint, and exact next step.
- `01_architecture.md` — system and ingestion architecture.
- `02_database_schema.md` — planned, unfrozen schema and database technology decisions.
- `03_features/` — feature scope and definitions of done.
- `05_experiments.md` — required reproducibility records for future experiments.
- `06_dataset.md` — dataset decision, evidence, limitations, and audit state.
- `04_troubleshooting.md` and `CHANGELOG.md` — recovery record and project history.
