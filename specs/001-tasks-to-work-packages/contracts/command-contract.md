# Contract: `speckit.taskstoissues` (preset override)

Invoked as `/speckit-taskstoissues` (skills mode) or `/speckit.taskstoissues` (command mode).

## Arguments
| Arg | Meaning |
|---|---|
| `<project>` | optional project identifier; overrides config |
| `--dry-run` | plan only; no writes to OpenProject, ledger or files |
| `--update` | propagate changed subject/description to linked WPs |

## Stop conditions (nothing written)
1. `tasks.md` missing/empty → tell user to run tasks command.
2. Config or ledger violates the rules embedded in the prompt (kept identical to `schemas/config.schema.json` / `schemas/mapping.schema.json` by `tests/test_prompt_sync.py`) → show the violations, never overwrite.
3. Required capability not available (capability table embedded in the prompt).
4. Project unknown / not writable (first preview rejected).
5. Configured type missing → list available types.

## Capabilities used (names resolved only via the capability table embedded in the prompt; source of truth `docs/mcp-tool-map.md`, kept in sync by `tests/test_prompt_sync.py`)
list projects · list types/statuses/priorities · list/search work packages · get work package · get relations · create work package · update work package · create relation.

## Confirmation protocol
1. Show plan table (key, kind, subject, parent, action, reason).
2. `--dry-run` → stop.
3. Per phase: show the phase's items → ask once → for each item run write preview, require `ready`, then `confirm=true`, then write ledger.
4. Feature work package is confirmed together with phase 1.

## Report (always last)
Counts: created, adopted, skipped, updated, blocked, stale, failed, relations created/skipped; table of key → WP id → relative link; reasons for blocked/failed/stale.

## Exit semantics
Items are independent after their parents exist; a blocked parent blocks its children (reported as "blocked: parent"). A tool failure stops the run; ledger is current to the last confirmed write.
