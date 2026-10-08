# Contract: command prompts

Both prompts follow the structure of `sync-docs.md`: numbered steps, explicit stop conditions, embedded capability rows from `docs/mcp-tool-map.md`, embedded config-rules and ledger-rules blocks (identical across prompts, checked by `test_prompt_sync.py`), plan table, `--dry-run`, one confirmation, report.

## `speckit.openproject.sync-version`

Arguments: `[--version <name>] [--dry-run] [<feature dir>]`.
Capabilities used: `list-versions`, `get-version`, `create-version`, `get-work-package`, `bulk-update-work-packages` (fallback `update-work-package`).

Steps: (1) resolve feature, read config and ledger, stop on missing/invalid; (2) check capabilities, stop if `create-version` is absent; (3) resolve the version name (R2) and look it up (R3); (4) read each ledger work package (id, version); (5) classify (R3 tables) and show the plan; (6) `--dry-run` ends with `Dry run: nothing was written.`; (7) one confirmation; (8) create the version if planned (preview, confirm), write the ledger `version` at once; (9) bulk assignment preview and confirm; (10) report.
Report: counts created, reused, assigned, unchanged, other-version, stale, failed, blocked; result `complete`, `incomplete`, `no changes`, `dry run` or `stopped`.

## `speckit.openproject.log-time`

Arguments: `[--activity <name>] [--entry-key <k>] [--dry-run] [<lines>]`; lines may be given as arguments or asked for.
Capabilities used: `list-time-activities`, `create-time-entry`, `get-work-package`.

Steps: (1) resolve feature, read config and ledger; (2) check capabilities, stop if `create-time-entry` is absent; (3) parse input lines (R5), reject invalid ones in the plan; (4) resolve activity (R7), list activities, ask if needed; (5) resolve work packages (R8); (6) compute keys, classify (create, unchanged, unknown, rejected, stale) and show the plan; (7) `--dry-run` ends with `Dry run: nothing was written.`; (8) one confirmation; (9) per create item: preview, confirm, append `TimeRecord` to the ledger at once; (10) report.
Report: counts created, unchanged, unknown, rejected, stale, failed; total hours created; result as above.

## Common rules

No write before the confirmation; no deletes; no secrets, hosts or URLs in output or files; errors redacted; works in skills mode (`/speckit-openproject-sync-version`, `/speckit-openproject-log-time`) and command mode (`/speckit.openproject.<name>`).
