# Quickstart: validating status sync

Prerequisites: sandbox as in `docs/TESTING.md`, bot token in the MCP client config only, `scripts/dev-install.sh` run, config with `statuses` from `discover-fields`, feature `001-sandbox-demo` published with `taskstoissues` (14 work packages, ledger present). Run `--dry-run` first in every scenario; the maintainer removes test work packages by hand.

## Automated (no OpenProject)

```bash
uv run pytest tests/test_sync_decision.py tests/test_schemas.py tests/test_prompt_sync.py tests/test_manifests.py
uv run ruff check . && uv run ruff format --check .
```

Expected: all decision-table rows (including baseline, reverted, closed-not-done, conflict) pass; the second pass over the result of the first changes nothing; the checkbox edit differs from the input only in bracket characters.

## Live (installed skill, fresh session in `.scratch/proj`)

| ID | Setup | Expected |
|---|---|---|
| S14 | In OpenProject: T002 → "Closed", T003 → "In progress". In `tasks.md`: check T001 | dry run shows pull T002, in progress T003, push T001; real run: T002 checked, T001's work package "Closed", ledger holds all three statuses, assignee recorded, `tasks.md` diff = one bracket character; run again: `no changes` |
| S15 | After S14: check T004 in `tasks.md`; close T005's work package; check T006 in `tasks.md` and move its work package to "On hold"; uncheck T001 (still done) | T004 pushed, T005 pulled, T006 conflict (OpenProject wins, report names the overwritten `[x]`), T001 reverted; second run `no changes` |
| S16 | Restricted workflow for the task type (maintainer, admin UI): New may not go to Closed; check T007 | T007 `blocked`, nothing written for it, others processed, result `incomplete`; hook check: finish a `/speckit-implement` run and see the optional offer; decline reads nothing |
| S17 | Stop conditions: no `statuses.done`; ledger absent; MCP server not started; `tasks.md` edited between plan and write | each stops with a specific message and zero writes; the last case writes nothing and asks for a re-run |

Record date, OpenProject version, MCP server version, spec-kit version and result in `docs/TESTING.md`; label command mode and the transition preview (research R4) untested until run.
