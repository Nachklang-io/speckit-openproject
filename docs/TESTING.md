# Testing

## Automated (CI, no OpenProject needed)
- Manifest validation for `preset/preset.yml` and `extension/extension.yml`.
- JSON schema validation of config and mapping fixtures.
- Install smoke test: scratch spec-kit project, `specify preset add --dev`, `specify extension add --dev`, check overrides.

## Test instance setup (OpenProject in a Proxmox LXC, latest release)
1. Log in as admin, create project with identifier `speckit-sandbox` (name e.g. "spec-kit Sandbox").
2. Project settings -> Modules: enable Work packages, Versions (Roadmap), Time and costs, Wiki.
3. Administration -> Types: ensure types "Phase" (or use "Milestone"), "Task", "Feature"/"Epic" exist and are enabled in the sandbox project. Note the names for `config.yml`.
4. Create a dedicated user `speckit-bot` with a role that may add/edit work packages, manage versions and log time in the sandbox project only.
5. As that user: My account -> Access tokens -> create an API token. Keep it in your shell environment only.
6. Export `OPENPROJECT_BASE_URL`, `OPENPROJECT_API_TOKEN`, `OPENPROJECT_READ_PROJECTS=speckit-sandbox`, `OPENPROJECT_WRITE_PROJECTS=speckit-sandbox` before starting Claude Code.
7. The LXC must be reachable from the machine running Claude Code (HTTPS recommended; if self-signed, set `OPENPROJECT_VERIFY_SSL` as documented by the MCP server).
Record the OpenProject version in the results table below on every run.

## Scenario checklist (manual, against the maintainer's test instance)
Use a sandbox project. Always run with `--dry-run` first. Record date, OpenProject version, MCP server version, spec-kit version and result.

| ID | Scenario | Expected | Last run | Result |
|---|---|---|---|---|
| S1 | 3 phases / 10 tasks, no existing WPs | 1 feature WP, 3 phase WPs, 10 task WPs with parents, mapping has 14 entries | 2026-10-05 | pass (manual walkthrough, see run log) |
| S2 | Re-run S1 | 0 created, 14 skipped, 0 relations created | 2026-10-05 | pass (manual walkthrough, see run log) |
| S3 | Interrupt after 5 creations (answer "stop" at the second phase confirmation), re-run | remaining items created, existing ones skipped, 0 duplicates | – | – |
| S4 | `tests/fixtures/tasks/s4-tasks.md` (dependencies, `[P]` tasks) | exactly 3 `follows` relations: T004→T002, T005→T004, T006→T001; none between `[P]` tasks | – | – |
| S5 | Type from config does not exist | stops, lists available types | – | – |
| S6 | Mandatory custom field in project | stops for that item, reports field | – | – |
| S7 | Project not in write allowlist | clear error, nothing written | – | – |
| S8 | `--dry-run` on the S1 input | plan with 14 entries; 0 work packages created; `.specify/openproject/mapping.json` absent or byte-identical | 2026-10-05 | partial: plan logic checked by hand (see run log); not run via the installed skill |
| S9 | Change one task title, run without then with `--update`; add a ledger entry pointing to a non-existent work package | without `--update`: "differs, not updated"; with `--update`: that work package updated; the bogus entry is reported as stale, not recreated | – | – |

## Notes for the scenarios
- Before S1: delete leftover `VERIFY-*` work packages from earlier checks, otherwise search hits and counts differ.
- S1 and S2 run in both modes: skills mode (`/speckit-taskstoissues`) and command mode (`/speckit.taskstoissues`). Note which one was not run.
- S6 needs a mandatory custom field on the sandbox project (create it in the admin UI, remove it afterwards).
- Large list (`tests/fixtures/tasks/s-large-tasks.md`, 120 tasks): `--dry-run` only; not run live.
- Record the S1 duration (SC-004: under 5 minutes including the dry-run review).
- Claude Code must be started with the MCP server variables exported (`set -a; source .env; set +a; claude`).

## Run log
### 2026-10-05 – S8 (dry-run), manual walkthrough, partial
- What was executed: steps 1–10 of `preset/commands/speckit.taskstoissues.md` were followed by hand in a Claude Code session against `speckit-sandbox`, using only read capabilities (`list-projects`, `list-types`, `get-write-context` for Feature/Summary task/Task, `search-work-packages` for the feature, `Phase 1:` and `T001`, `list_work_packages`). Input: `tests/fixtures/tasks/s1-tasks.md`.
- Result: sandbox empty before; no matches; plan = 4 create (feature + 3 phases), 10 blocked (type Task requires `customField1`, S6 setup), 0 relations. No write call was made and no ledger file was created.
- Not covered: the installed skill was not invoked, so frontmatter `tools:` matching, argument parsing and the confirmation dialogue are untested. S1–S7 and S9 not run.
- Environment: OpenProject version not recorded, MCP server `openproject-ce-mcp` 0.4.1 as pinned in the repo docs (not re-read at runtime), spec-kit 1.1.1.dev0.

### 2026-10-05 – S1 and S2, manual walkthrough
- What was executed: the steps of `preset/commands/speckit.taskstoissues.md` were followed by hand in a Claude Code session against `speckit-sandbox`, using the MCP tools directly (not the installed skill). Input: `tests/fixtures/tasks/s1-tasks.md` as feature `001-sandbox-demo` in the scratch project, config from the template defaults (types Feature / Summary task / Task). The mandatory test custom field had been deactivated by the maintainer. The maintainer confirmed each of the three phases, as the prompt requires.
- S1 result: 14 work packages created (ids 41–54): 1 Feature, 3 Summary tasks (children of the Feature), 10 Tasks (children of their phase). Each write was previewed (`state: preview`, `ready: true`, no validation errors) and then confirmed. The ledger `.specify/openproject/mapping.json` has 14 entries, validates against `schemas/mapping.schema.json`, ids unique, no host or URL stored. The list of work packages in the project matched the ledger (total 14, parents as expected).
- S2 result: re-planning with the ledger: each of the 14 ledger ids was found with `get-work-package`; plan = 14 skip, 0 create, 0 relations; no write call was made.
- Defects found and fixed during the run: file hints like `src/app/__init__.py` rendered as bold text in Markdown, so the prompt now writes the path in backticks (the first preview of T001 showed it before anything was written).
- Open: a `[P]`-only task gets the first line `Story: parallel`, which reads oddly; consider the label `Labels:`.
- Not covered: the installed skill was not invoked (frontmatter `tools:` matching, argument parsing untested); command mode not run; the S1 duration (SC-004) was not measured; OpenProject version not recorded; S3–S7 and S9 not run; search-and-adopt, relations, `--update` and the mandatory-field block were not exercised live in this run.
- Leftover state: the 14 work packages remain in `speckit-sandbox` (this project never deletes). Remove them before repeating S1.
