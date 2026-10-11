# Contract: `speckit.openproject.sync-status` (extension 0.2.0)

Changes against the contract of feature 003 (`specs/003-status-sync/contracts/command-contract.md`). Everything not listed there stays as it is.

## Invocation

Unchanged: `[feature] [--dry-run]`; skills `/speckit-openproject-sync-status`, command `/speckit.openproject.sync-status`. No new flag (FR-015); the switch is the config key `rollup_parents`.

## Capabilities used

Unchanged set: `list-statuses`, `get-write-context`, `get-work-package`, `search-work-packages`, `update-work-package`. New uses only: `get-write-context` also for the parent types (hint for blocked parents), `update-work-package` also for phase and feature work packages (`status` only).

## Steps (16, every run from scratch)

1–6 as in 003 (step 6 additionally reads `parent_id` of every task work package for the phase membership, FR-002 (report lines `T### counted for phase-M (parent in OpenProject), …` and `T### not counted: …`, no action and no count change); step 5 additionally requires `statuses.open` and `statuses.in_progress` while the roll-up is on; step 5 reads the write context for the phase and feature types too).

7. **Roll-up plan** (new): planned task states (pushes assumed confirmed), `R` and action of each phase, then of the feature.
8. **Preview the writes**: task pushes, then each parent with action `roll-up` (phases in key order, feature last), `status` = `R`, no `confirm`. An invalid preview or a tool error makes the parent `blocked`.
9. Plan: task table, Parents section, both counts lines. 10. Dry run / nothing to write. 11. One confirmation for the whole plan.
12. Task push. 13. Pull and conflicts. (003 steps 11 and 12.)
14. **Parent writes** (new): skipped if step 12 or 13 stopped the run. Recompute `R` from actual outcomes; a differing target is not written (`plan changed`, `skipped`). Recheck `O`, confirm, ledger write before the next call. Then the feature from actual phase outcomes.
15. Ledger. 16. Report.

## Output contract

- Task table and task counts line unchanged (SC-006).
- New Parents section: `Key | WP | OpenProject | Rolled up | Action | Reason`.
- New counts line: `parents: rolled up N, unchanged N, left alone N, blocked N, failed N, stale N, skipped N`.
- Result values unchanged. A blocked, failed or skipped parent makes the result `incomplete`; left-alone and stale parents are reported only.
- Notes in the report: percent complete 100 on every closed parent (FR-011); tasks counted as finished through a closed status other than done, per phase.
- With `rollup_parents: false`: no Parents section, informational lines as in 003.

## Hard limits (replace the 003 limits on parents)

- Parents are written only by the roll-up, only `status`, only after preview and the single confirmation.
- A parent in done, another closed status or a status outside the three configured ones is never written.
- No create, delete, re-parent or reopen; no change of subject, description, type, assignee or time.
- No token, host or URL of an instance in any file or output.

## Hook

Unchanged (`after_implement`, optional): the hook runs the sync including the roll-up.
