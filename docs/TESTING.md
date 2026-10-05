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
| S1 | 3 phases / 10 tasks, no existing WPs | 3 phase WPs, 10 task WPs with parents, mapping has 13 entries | – | – |
| S2 | Re-run S1 | 0 creations, report says all skipped | – | – |
| S3 | Interrupt after 5 creations, re-run | resumes, no duplicates | – | – |
| S4 | Dependencies between tasks, `[P]` tasks | `follows` relations only for real dependencies | – | – |
| S5 | Type from config does not exist | stops, lists available types | – | – |
| S6 | Mandatory custom field in project | stops for that item, reports field | – | – |
| S7 | Project not in write allowlist | clear error, nothing written | – | – |
