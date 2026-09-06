# Long-term Memory — Human Quick Guide

This folder is the project memory for both the user and AI agents. You do **not** need to read every file every time.

## If you only want to know where the project is now

Read **`00_project_status.md`**.

It tells you:
- what has already been completed,
- what is currently being worked on,
- the latest stable checkpoint,
- any blockers,
- and the exact next step.

## What each file is for

- **`00_project_status.md`** — current progress / save point of the whole project.
- **`01_architecture.md`** — how the web app, forecasting pipeline, database, and inventory decision engine fit together.
- **`02_database_schema.md`** — planned database tables and relationships.
- **`03_features/`** — detailed notes for each major feature such as inventory management, forecasting, decision engine, and dashboard.
- **`04_troubleshooting.md`** — errors we encountered, why they happened, how they were fixed, and how to recover after a reset.
- **`05_experiments.md`** — forecasting and inventory experiments, models tested, metrics, results, and decisions.
- **`06_dataset.md`** — dataset candidates, the chosen dataset/subset once frozen, schema, time split, limitations, and data assumptions.
- **`CHANGELOG.md`** — chronological history of notable changes/checkpoints.

## Recommended reading order for you

Most of the time, read only:

1. `00_project_status.md`
2. `06_dataset.md` when we are working with data
3. `05_experiments.md` when model training starts
4. `CHANGELOG.md` if you want to see what changed recently

The other files are mainly there so Codex or another AI agent can recover the full project context without relying on old chat history.

## Current memory rule

After every meaningful task, the AI agent should update the relevant memory file, record the new checkpoint/next step, then commit and push the change together with the code whenever practical.
