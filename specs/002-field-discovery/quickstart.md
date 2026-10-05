# Quickstart: validating feature 002

Prerequisites: `uv sync`; the sandbox MCP server connected (start Claude Code from a shell that exported `.env`, see the sandbox memory note); nothing in this guide writes to OpenProject.

## Automated

```bash
uv run pytest tests/test_schemas.py tests/test_prompt_sync.py tests/test_manifests.py
uv run pytest && uv run ruff check . && uv run ruff format --check .
```

Expected: schema accepts `statuses`, rejects unknown keys and empty names inside it; embedded blocks in both prompts match the schema and the tool map; manifests valid.

## Install into a scratch project

```bash
scripts/dev-install.sh        # recreates .scratch/proj with preset and extension (--dev)
cd .scratch/proj && specify extension list && specify preset list
```

Expected: `openproject` listed in both.

## Manual scenarios (details and result tables in `docs/TESTING.md`)

| # | Scenario | Setup | Expected |
|---|---|---|---|
| S10 | Bootstrap | no `.specify/openproject/config.yml` in the scratch project | one run, accepted proposals, file schema-valid, `taskstoissues --dry-run` reports no configuration error; with the mandatory custom field and no value: file written, run `incomplete`, warning names the field |
| S11 | Re-run after hand edits | add a comment, change `types.phase`, add `create_relations: false` | diff shown; `none` leaves file byte-identical (compare checksum); partial approval changes only the chosen keys; comment and extra key survive; unchanged project: `no changes` |
| S12 | Dry run | any state | overview and diff shown, line `Dry run: nothing was written.`, file checksum unchanged |
| S13 | Failures | (a) project not set and no projects readable, (b) unknown project, (c) project outside the server allowlist, (d) MCP server not connected, (e) invalid existing config | (a)–(d) each stop with a specific message, no file created or changed; (e) lists all violations and offers a rebuild diff, file unchanged unless approved |

Run each through the installed skill in a fresh session, `--dry-run` first, then for real. Record what was executed; paths not executed (command mode, list-type custom field, versions with data) stay labelled untested.

## Review

Run the `spec-conformance-reviewer` and `openproject-api-reviewer` subagents on the diff before the PR.
