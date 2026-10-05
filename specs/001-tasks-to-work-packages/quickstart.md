# Quickstart: validating feature 001

## Automated (no OpenProject)
```
uv sync
uv run pytest tests/test_schemas.py tests/test_manifests.py
uv run ruff check . && uv run ruff format --check .
scripts/dev-install.sh && (cd .scratch/* && specify preset list)
```
Expect: schema fixtures pass/fail as listed in `contracts/schema-changes.md`; preset `openproject` listed.

## Manual (maintainer's test instance, see `docs/TESTING.md` setup)
Prereq: sandbox project `speckit-sandbox`, MCP server connected, config at `.specify/openproject/config.yml` with types Feature/Phase/Task.
1. In a scratch project use a `tasks.md` with 3 phases / 10 tasks (fixture `tests/fixtures/tasks/s1-tasks.md`).
2. `/speckit-taskstoissues --dry-run` → plan of 14 creates; verify OpenProject and ledger untouched (SC-005).
3. `/speckit-taskstoissues` → confirm per phase; verify S1: 14 WPs, parents, 14 ledger entries.
4. Re-run → S2 (0 creations). Interrupt after ~5 creations, re-run → S3.
5. `s4-tasks.md` → S4 relations. S5/S6/S7 per `docs/TESTING.md`.
6. Record date, OpenProject, MCP server, spec-kit versions and results in `docs/TESTING.md`; fill "Verified params" in `docs/mcp-tool-map.md` (research "Unresolved" items 1–2).

Untested paths must be labelled as such in the README.
