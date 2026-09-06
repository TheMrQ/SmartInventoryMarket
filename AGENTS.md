# Smart Inventory Market — AI Operating Manual

## Long-term Memory

The `docs/` directory is the long-term memory and repository documentation is the source of truth. Chat context is not the source of truth.

At the beginning of **every** task, read, in order:

1. `AGENTS.md`
2. `docs/00_project_status.md`
3. `docs/01_architecture.md`

Then read task-specific memory as applicable:

| Task | Required documentation |
| --- | --- |
| Dataset work | `docs/06_dataset.md` |
| ML, forecasting, or experiments | `docs/05_experiments.md`, `docs/03_features/demand_forecasting.md` |
| Inventory logic | `docs/03_features/inventory_management.md`, `docs/03_features/inventory_decision_engine.md` |
| Frontend/dashboard | `docs/03_features/dashboard.md` |
| Database | `docs/02_database_schema.md` |
| Bug, error, or recovery | `docs/04_troubleshooting.md` |

Never assume a feature exists because it appeared in a previous chat. Only repository state and documentation determine project status.

## After Every Meaningful Task

Before declaring a meaningful task complete:

1. Verify the implementation and run relevant tests/checks.
2. Update `docs/00_project_status.md` and relevant architecture/feature/dataset documentation.
3. Update `docs/05_experiments.md` after an ML experiment; update `docs/06_dataset.md` when dataset understanding changes.
4. Update `docs/04_troubleshooting.md` for a meaningful bug or recovery.
5. Update `docs/CHANGELOG.md`.
6. Create a coherent Git commit and push it.

A coding or ML task is not done until its documentation is updated.

## Status Values

Use only: `TODO`, `IN_PROGRESS`, `BLOCKED`, `DONE`, `OPTIONAL`.

## Definition of Done

Mark a task `DONE` only when implementation exists, verification and relevant tests succeed, expected outputs/artifacts exist, documentation is updated, a Git commit exists, and the push succeeds (or a push failure is explicitly documented).

# Git Commit & Push Protocol

Codex must proactively maintain Git history. This solo thesis repository may work directly on `main` unless the user requests branches.

## Rule 1 — Commit Frequently, but Meaningfully

Commit after each coherent, verified milestone (for example initialization, dataset audit, frozen subset, baseline, model, experiment, schema, inventory module, decision engine, API, dashboard, or documentation checkpoint). For long work, commit independently verified sub-steps. Do not create meaningless line-by-line commits.

## Rule 2 — Before Every Commit

Run `git status` and `git diff --check`; inspect staged files. Do not commit passwords, API keys, credentials, `.env`, personal information, M5 raw data, restricted data, huge generated files, model binaries without approval, virtual environments, `node_modules`, or temporary files.

## Rule 3 — Test Before Committing

Run applicable checks: `pytest` for backend work, `npm run build` for frontend work, import/syntax smoke checks as appropriate, and validation/evaluation for ML work. Do not knowingly commit broken code.

## Rule 4 — Commit Messages

Prefer Conventional Commits, such as `chore(init): initialize smart inventory thesis project`, `feat(forecast): add naive forecasting baseline`, `experiment(forecast): compare LightGBM and XGBoost`, or `fix(data): prevent future leakage in rolling features`.

## Rule 5 — Push After Successful Commits

After each milestone, run `git push origin HEAD`; for an initial upstream, run `git push -u origin main`. Keep GitHub synchronized with verified work.

## Rule 6 — No Destructive Git Automation

Never automatically run `git push --force`, `git push --force-with-lease`, `git reset --hard`, or `git clean -fd`. Never rewrite pushed history, delete remote branches, or amend a pushed commit without explicit user approval.

## Rule 7 — Remote Conflicts

If a push finds remote changes, fetch and inspect divergence; never force-push. For a meaningful merge/rebase conflict, stop destructive Git actions, record the blocker in project status, and explain it to the user.

## Rule 8 — Authentication or Network Failure

On GitHub authentication/network failure, preserve the local commit, avoid repeatedly changing Git configuration, record `PUSH_BLOCKED` in project status, and report the exact error.
