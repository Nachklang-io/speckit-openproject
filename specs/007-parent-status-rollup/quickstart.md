# Quickstart: validating the parent status roll-up

Prerequisites: sandbox as in `docs/TESTING.md`, bot token in the MCP client config only, `scripts/dev-install.sh` run, config with `statuses` from `discover-fields`, a published sandbox feature (ledger present, phases and feature work packages in "New"). Run `--dry-run` first in every scenario; the maintainer removes test work packages by hand.

## Automated (no OpenProject)

```bash
uv run pytest tests/test_rollup.py tests/test_schemas.py tests/test_prompt_sync.py tests/test_manifests.py
uv run ruff check . && uv run ruff format --check .
```

Expected: every rule and guard case passes; the second pass over the result of the first writes nothing; the `rollup-table` block and the config-rules of all six prompts match the reference and the schema.

## Live (installed skill, fresh session in `.scratch/proj`)

Contracts: [command-contract.md](contracts/command-contract.md), data: [data-model.md](data-model.md).

| ID | Setup | Expected |
|---|---|---|
| S34 | All tasks done in `tasks.md` and OpenProject; phases and feature "New" | dry run lists every parent with `roll-up`; real run: all phases and the feature done, ledger holds it, percent-complete note in the report; run again: 0 writes |
| S35 | Three phases: all done / one task open, rest done / nothing started | phases done, in progress, open; feature in progress |
| S36 | One phase hand-set to "Rejected", one to "On hold" | both reported (`closed, not done`, `unmapped status`), never written; Rejected counts as finished, On hold as in progress for the feature |
| S37 | `rollup_parents: false`; all tasks done | no parent read for the roll-up or written; report as in 003 |
| S38 | Workflow of the phase type forbids the transition | that parent `blocked` with the server reason, other parents continue, result `incomplete` |

Record date, OpenProject version, MCP server version, spec-kit version and result in `docs/TESTING.md`; label command mode, the hook offer and every path not run untested.
