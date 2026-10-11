# Research: Parent Status Roll-up

All open points of the spec are resolved here (the spec has no `NEEDS CLARIFICATION` left; the two items deferred from clarify are R1 and R5).

## R1. Config key that switches the roll-up off

- **Decision**: new optional top-level boolean `rollup_parents`. Absent or `true` = roll-up on (FR-014); `false` = off. It is never written by any command (discover-fields keeps it as it is, like `create_relations` and `mark_parallel`). The template documents it as a comment only, so no existing or freshly generated config contains it unless the user adds it.
- **Rationale**: it matches the existing booleans `create_relations` and `mark_parallel` (flat, top level, default-on behaviour). `additionalProperties: false` stays; the change is additive (FR-010).
- **Alternatives considered**: `statuses.rollup` (rejected: every `statuses` value is a non-empty status name, and mixing in a boolean would break that rule); a nested `sync: {rollup: …}` section (rejected: a new section for one key; nesting is not needed); a CLI flag `--no-rollup` (rejected: FR-015 wants the hook unchanged, and a team that manages parents by hand needs a durable setting, not a per-run flag).
- **Compatibility consequence**: every prompt that embeds `config-rules` treats unknown keys as errors. The key therefore enters the config-rules block of all six prompts (preset included) in the same change, and the preset gets a patch release. A user who sets `rollup_parents` while still running preset 1.0.1 gets a config error from `speckit.taskstoissues`; the README and CHANGELOG say so, and the bundle pins matching versions.

## R2. Roll-up rule (executable mirror)

- **Decision**: a new test helper `tests/rollup_reference.py` with three pure functions and a row list that the prompt block `rollup-table` must match (as `tests/sync_reference.py` does for the task table):
  1. `task_state(…)` → `finished` / `in progress` / `open` for one task line after the task part of the run (see R3).
  2. `rollup(states)` → `done` if all are finished, `in progress` if any is finished or in progress, `open` otherwise; an empty list → `none` (left alone).
  3. `classify_parent(read, target, done, in_progress, open, closed)` → action and label (R4).
- **Rationale**: the rule is the core of the feature; making it executable keeps the prompt and the tests in step (constitution IV). It is a separate file because the task table stays untouched (spec: out of scope to change the 003 task rules).
- **Alternatives considered**: extending `sync_reference.py` (rejected: mixes two tables and makes the task-table tests harder to read).

## R3. Which state a task contributes

- **Membership** (review follow-up, 2026-10-10): a task line belongs to the ledger phase whose `id` equals the `parent_id` of its work package (read in step 6, no extra call); without a match, without a parent or without a read, to the phase of the nearest `## Phase N` heading above it (N without leading zeros); otherwise to no phase; a task whose parent phase has no heading, or whose heading phase has no ledger entry, is counted for no phase and named in the report. Reason: the preset can parent a task above the first heading under a phase the user names, and a task line can be moved after publishing; the heading alone then misses a real child.
- **Decision**: per task line of a phase:
  - `finished`: its work package status after this run is `statuses.done` or any other closed status (`closed, not done` tasks; the report names them, FR-001).
  - `in progress`: its status after this run equals `statuses.in_progress`.
  - `open`: everything else, including `unpublished`, `stale`, `blocked` and `failed` tasks and tasks whose pull or conflict was `skipped` (FR-012). A task with an unmapped open status (for example On hold) also counts as `open` for the phase.
  - "status after this run" is: for a confirmed push `statuses.done`; for a blocked or failed push the status read in step 6; for every other task the status read in step 6 (pulls and conflicts never change OpenProject).
  - `orphan` ledger entries have no task line and do not belong to any phase.
- **Dry run**: pushes are assumed confirmed (spec edge case "dry run uses the planned states"); blocked previews stay blocked.
- **Rationale**: OpenProject owns the status (feature 003), so the roll-up reads OpenProject's state, not the checkbox. A pull already makes the box follow OpenProject.
- **Alternatives considered**: deriving from the checkboxes (rejected: a conflict would then roll up the side that lost).

## R4. Decision for one parent

Inputs: `O` = status read in step 6 (the existing read of every ledger item, no extra call), `R` = rolled-up status (R2), `B` = ledger status.

Checks in this order (first match wins):

| # | Condition | Action | Label |
|---|---|---|---|
| 1 | roll-up off | not evaluated, informational line as before 007 | — |
| 2 | work package missing (step 6 existence check) | stale (reported, never recreated) | `stale` |
| 3 | `R` = none (phase without task lines; feature with every phase ignored) | left alone | `no tasks` |
| 4 | `O` = `statuses.done` | none (never leaves done, FR-013) | `stays done` if `R` ≠ done |
| 5 | `O` closed, not done | left alone (FR-005) | `closed, not done` |
| 6 | `O` not one of `statuses.open`, `statuses.in_progress` | left alone (FR-006) | `unmapped status` |
| 7 | `O` = `R` | none | — |
| 8 | otherwise | roll up: write `R` | `roll-up` |

In every row from 2 on, if the parent exists and `B` ≠ `O`, the ledger gets `status` = `O` (refresh, FR-007); a row-8 parent gets `status` = `R` after its confirmed write. Assignee keys of parent entries are never written or removed (the spec writes the status only; the task assignee rule is not extended to parents).

- Row 8 can move a parent from in progress back to open when no task has started (US2 scenario 2); only done is protected (FR-013).
- A parent that is a ledger entry without a matching `## Phase N` heading is reported as `no heading` and left alone; a heading without a ledger entry `phase-N` is reported as `unpublished phase` (spec edge case). Both are reported only and do not count for the feature.
- **Alternatives considered**: using `B` as in the task table (rejected: a parent has no local side, so there is nothing to conflict with; `O` vs `R` is enough and keeps re-runs at zero writes).

## R5. Feature roll-up and the order of writes

- **Decision**: each phase contributes to the feature with its status *after* its own handling:
  - row 8 confirmed: `R`; row 8 blocked: `O`; row 8 failed: a fresh `get-work-package` read, `O` if that read fails;
  - rows 4–7: `O` (closed → finished, `statuses.in_progress` or unmapped open → in progress, `statuses.open` → open);
  - row 3 (`no tasks`) and the `no heading` case: ignored;
  - stale: its `R` capped at in progress (a missing phase never counts as finished; it still shows that work has started).
  Then the feature `R` = R2's `rollup` over these states. Phases are written before the feature (FR-003).
- **Rationale**: matches clarification 7 (a blocked or failed phase counts with its actual status) and is safe (never closes a feature over a phase that is not closed).
- **Alternatives considered**: counting a stale phase as finished when its tasks are (rejected: a missing work package is an anomaly; closing the feature over it hides it).

## R6. Where the roll-up sits in the steps

- **Decision**: renumber the prompt to 16 steps; steps 1–6 keep their numbers and meaning. New and moved steps:
  - 5: also calls `get-write-context` for `types.phase` and `types.feature` when the roll-up is on (hint for blocked parents only; a tool error only drops the hint, as for tasks). The `statuses.open` and `statuses.in_progress` names become required when the roll-up is on (FR edge case "missing statuses: stop"); the step-3 message is extended accordingly.
  - 7 (new) **Roll-up plan**: compute the planned task states (R3, pushes assumed confirmed), each phase's `R` and action (R4), then the feature's planned `R` from the planned phase states (R5).
  - 8 (was 7) **Preview the writes**: task pushes, then every row-8 parent (phases in key order, then the feature) with `status` = `R`, no `confirm`. An invalid preview or a tool error makes the parent `blocked`; the three-consecutive-tool-errors stop counts across tasks and parents.
  - 9–11 (were 8–10): plan with a parents section and a second counts line; dry run; one confirmation for the whole plan (FR-004). The "more than 10 pushes" notice also counts parent writes.
  - 12–13 (were 11–12): task push and pull, unchanged.
  - 14 (new) **Parent writes**: skipped entirely if step 12 or 13 stopped the run (FR-012). Recompute each phase's `R` from the actual task outcomes; if it differs from the planned `R`, do not write: label `plan changed`, count as `skipped`. Otherwise recheck with `get-work-package` (status must still be `O`, else `failed`, `changed meanwhile`), confirm, write the ledger before the next write. Then recompute the feature from the actual phase outcomes (R5) and handle it the same way.
  - 15 (was 13) Ledger; 16 (was 14) Report.
- **Rationale**: previews must happen before the single question (consent covers what was shown), and a confirm call must repeat the previewed call exactly; a recomputed target that differs is therefore skipped, never written. Renumbering is cleaner than sub-steps; no test or doc refers to the step numbers of `sync-status.md` (checked: `grep` over `tests/`, `docs/`, READMEs).
- **Alternatives considered**: a second question for parents after the task writes (rejected by clarification 6); previewing parents after the task writes (rejected: the user would confirm a plan whose parent part was never previewed).

## R7. Ledger write for parents

- **Decision**: the same atomic write as for a task push (complete ledger through `mapping-<FEATURE>.json.tmp`, read back, validate, move), after each confirmed parent write and before the next call. Refreshes of parent statuses are batched in step 15 with the task refreshes. Only `status` of `phase` and `feature` items changes; no schema change for the ledger (the item key `status` exists).
- **Rationale**: FR-007; the interruption analysis of feature 003 (risk 4) applies unchanged.

## R8. Report and result

- **Decision**: the plan and the report get a `Parents` section: `Key | WP | OpenProject | Rolled up | Action | Reason`, and a second counts line `parents: rolled up N, unchanged N, left alone N, blocked N, failed N, stale N, skipped N`. The task counts line keeps its exact format (SC-006). Result: a blocked, failed or skipped parent makes it `incomplete`; left-alone and stale parents do not change the result on their own (they are reported). With the roll-up off, the parents section is replaced by the informational lines of 003. If any parent was closed: the percent-complete note (FR-011). Tasks counted as finished through a closed status other than done are named per phase.
- Override 3 of the task table ("feature and phase entries are read for the report only and never written") and the rule "Never write phase or feature work packages" are rewritten to "only through the roll-up (steps 7, 8 and 14), only `status`".

## R9. Version bumps and catalogs

- **Decision**: extension 0.1.0 → 0.2.0 (new default behaviour of an existing command); preset 1.0.1 → 1.0.2 (shipped prompt's config-rules block changes, behaviour otherwise unchanged); bundle 0.1.1 → 0.2.0 pinning both. Releases and catalog updates are done by the maintainer after merge (`docs/RELEASING.md`), not in this feature's tasks.
- **Rationale**: no shipped key is renamed or removed, so no major bump and no migration note (CLAUDE.md hard rule); the behaviour change of sync-status is visible in the CHANGELOG.

## Unresolved (to verify live, labelled untested until then)

- Whether the sandbox workflow for the phase type ("Summary task") and the feature type allows New → Closed and In progress → New directly; if not, those parents are `blocked` by design (spec assumption), and the scenario records it.
- Whether the server's percent-complete derivation on a closed parent changes anything else visible (expected: only percent complete).
