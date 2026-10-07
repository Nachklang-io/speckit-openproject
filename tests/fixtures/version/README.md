# Fixtures recorded for feature 005 (task T001)

Recorded 2026-10-07 against the sandbox (OpenProject 17.9.1, `jtauschl/openproject-ce-mcp` v0.4.1). Scratch work packages 115–117 (`VERIFY-005 ...`) and versions 7 (`VERIFY-005`, open) and 8 (`VERIFY-005-closed`, closed) in project `speckit-sandbox`; the maintainer removes them by hand. Secret-free: no host, no URL, no token.

| File | What it shows |
|---|---|
| `create-version-confirm.json` | `create_version(..., confirm=true)` result: `version_id` top-level; `status`/`sharing` default to `open`/`none` when omitted |
| `get-version.json` | `get_version` fields: `status` is a direct top-level string |
| `assign-version-ineffective-singular.json` | **the bug**: `update_work_package(..., version="VERIFY-005", confirm=false)` preview — `_links.targetVersions` stays `[]` despite the tool docstring claiming `version` writes the same data as `target_versions` |
| `assign-version-preview.json` | the fix: `update_work_package(..., target_versions=["VERIFY-005"], confirm=false)` preview — `_links.targetVersions` correctly shows the version |
| `assign-version-bulk-confirm.json` | `bulk_update_work_packages(items=[{work_package_id, target_versions}], confirm=true)` result shape |
| `get-work-package-version-field.json` | `get_work_package(select=["id","version","target_versions"])` after assignment: `version` reads back as the version's **name** (string), not its id |
| `assign-closed-version-rejected.json` | `target_versions` pointing at a closed version: rejected at preview time with a structured `validation_errors` entry, not a tool crash |

Not recorded: the exact per-item result shape of a *mixed* (partial-success) `bulk_update_work_packages` batch (not exercised live); a project with the version module disabled.
