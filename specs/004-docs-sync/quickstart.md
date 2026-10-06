# Quickstart: validating documentation sync

Prerequisites: sandbox as in `docs/TESTING.md`; bot token in the MCP client config only; MCP server started with `OPENPROJECT_ATTACHMENT_ROOT` set to a directory that contains the scratch project's feature directory (maintainer's setting; check that `create_work_package_attachment` appears in the tool list); `scripts/dev-install.sh` run; feature published with `taskstoissues` (feature work package in the ledger). Run `--dry-run` first in every scenario; the maintainer removes test work packages and attachments by hand.

## Automated (no OpenProject)

```bash
uv run pytest tests/test_docs_decision.py tests/test_schemas.py tests/test_prompt_sync.py tests/test_manifests.py
uv run ruff check . && uv run ruff format --check .
```

Expected: every row of the decision table passes; a second pass over the result of the first changes nothing; block replacement keeps all other description text byte for byte.

## Live (installed skill, fresh session in `.scratch/proj`)

| ID | Setup | Expected |
|---|---|---|
| T002 (Task 0, done 2026-10-06) | Scratch work package 113: upload, list, replace and delete an attachment, description round trip, file outside the root | recorded in `research.md` R1/R4/R5/R9, `docs/mcp-tool-map.md` and `tests/fixtures/docs/`; repeat only if the server version changes |
| S18 | First sync with `spec.md` and `plan.md` | dry run plans two `new`; real run: two attachments, summary block in the description, ledger `documents` with both hashes; run again: `no changes` |
| S19 | Change one line of `spec.md` | one `changed`: one attachment `spec.md` with new content (old one deleted), `plan.md` untouched, summary row updated, text outside the markers identical; run again: `no changes` |
| S20 | Interruption and drift: stop after the upload of a replaced document (ledger has `pending_delete`); delete `plan.md`'s attachment in the UI | rerun: `cleaned` for the superseded one, `restored` for `plan.md`, no duplicates; a user-added attachment with a document's name → `blocked`, nothing deleted |
| S21 | Stop conditions: server without upload root (tool absent), no `spec.md`, ledger absent, markers broken in the description | each stops with a specific message and zero writes; `--dry-run` also stops for the missing tool |

Record date, OpenProject version, MCP server version, spec-kit version and result in `docs/TESTING.md`; label command mode and every path not run untested.
