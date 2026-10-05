# Testing

## Automated (CI, no OpenProject needed)
- Manifest validation for `preset/preset.yml` and `extension/extension.yml`.
- JSON schema validation of config and mapping fixtures.
- Install smoke test: scratch spec-kit project, `specify preset add --dev`, `specify extension add --dev`, check overrides.

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
