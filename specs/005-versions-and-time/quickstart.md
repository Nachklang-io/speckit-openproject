# Quickstart: validating feature 005

Prerequisites: sandbox instance and MCP server as in `docs/TESTING.md` (server started with version write and time-entry write enabled), `scripts/dev-install.sh`, a scratch feature with a ledger from `speckit.taskstoissues` (feature, phase and task work packages).

1. `uv run pytest` and `uv run ruff check . && uv run ruff format --check .`: schemas, manifests, prompt sync, reference tables.
2. **S22 version**: run `sync-version --dry-run`, check zero changes; run it, accept; expect one version, all ledger work packages assigned, ledger `version` set. Run again: `no changes`.
3. **S22b**: put one work package into another version by hand, run again: reported `other version`, untouched.
4. **S23 time**: run `log-time` with two lines (`T001: 1h30`, `T002: 45m`), pick an activity, accept; expect two entries with PT1H30M and PT45M, today's date, the activity. Run the same input again: `unchanged`, no new entries. Run once with `--entry-key second` and identical values: one more entry.
5. **S24 interruption**: stop `sync-version` after the version was created (simulate by a ledger without `version`), run again: still one version.
6. **S25 stops**: server without version write / time-entry write, missing ledger: stop before any write, message names the fix.

Report what was executed; paths not run are labelled untested.
