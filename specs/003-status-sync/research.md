# Research: Status Sync

Facts marked *live* come from earlier sandbox runs recorded in `docs/mcp-tool-map.md` (OpenProject 17.9.1, project `speckit-sandbox`). Everything else is listed under "Unresolved".

## R1. Decision table (the core of the command)

**Decision**: Per task with a ledger entry, derive four values and classify with the table below.

- `C` = checkbox of the task in `tasks.md` (checked / open).
- `O` = current OpenProject status name; `Od` = `O` equals `statuses.done`.
- `B` = `status` in the ledger (last synced); `Bd` = `B` equals `statuses.done`. A missing `B` counts as not done and the item is labelled **baseline** (FR-004a).
- `tc` = `(C is checked) != Bd`: the task side changed since the last sync.
- `oc` = `O != B` (the status name differs from the ledger); for a baseline item (`B` missing) `oc` = `Od`.

| tc | oc | Condition | Action | Writes |
|---|---|---|---|---|
| no | no | | none | nothing |
| no | yes | `C checked != Od` | pull | set the box to `Od` (check if done, uncheck otherwise); ledger |
| no | yes | `C checked == Od` | refresh | ledger only (for example New → In progress, label "in progress") |
| yes | no | C checked, not Od | push | work package → `statuses.done`; ledger |
| yes | no | C open, Od (reverted) | pull | check the box; ledger; report "reverted" (FR-004b) |
| yes | yes | `C checked == Od` | refresh | ledger only (both sides moved the same way) |
| yes | yes | `C checked != Od` | conflict, OpenProject wins | box := `Od`; ledger; report names the overwritten `tasks.md` state |

A conflict can only arise when the base is not done, the box was checked and OpenProject moved the work package to another status that is not done (for example New → On hold): the checked box is overwritten and named in the report.

Overrides applied before the table is read:
1. `O` is a closed status other than done ("closed, not done", FR-003): the action is never a push and never changes the box; the ledger records `O`: the action is `refresh` if the ledger holds another status (or none) and `none` otherwise, and the label stays so that the report lists the task. A run in which only such tasks are already recorded ends `no changes`.
2. Task has no ledger entry: `unpublished`. Ledger entry whose work package is gone: `stale`. Ledger task entry without a task line: `orphan`. Items of kind `feature` and `phase`: shown only.
3. A push that the server will not accept: `blocked` (R4).

**Rationale**: The checkbox side is compared by done-ness (it has two states), the OpenProject side by status name, so that a move to "In progress" or "On hold" counts as a change (spec User Story 3). The table has seven rows. Baseline needs no special row: `Bd` is false and `oc` is `Od`, so both sides can only have changed towards done, they agree and no conflict can arise. After any completed run `status` in the ledger equals `O`, so `tc` and `oc` are false, and the second run is a no-op (SC-002). A status change that does not alter done-ness (New → In progress) only refreshes the ledger and is shown as "in progress".

**Alternatives**: a three-way merge on status names (needs a representable "in progress" in `tasks.md`, which has only two states); asking per conflict (rejected by the maintainer, spec clarification).

## R2. How progress is shown in the plan

**Decision**: One plan table, columns: key, work package id, `tasks.md` (`[ ]`/`[x]`), OpenProject status, last synced, action, reason; items sorted by task key. Intermediate statuses appear in the OpenProject column and in the reason ("in progress"). The same plan is printed with `--dry-run` and before confirmation, computed only from inputs, so dry run and real run agree (SC-003).

## R3. Reading status and assignee

**Decision**: Call `get-work-package` once per ledger task entry (id from the ledger) and read the status (name and id) and the assignee (display name) from the result. Join `list-statuses` for `is_closed`.

**Rationale** (live, confirmed 2026-10-06): `get_work_package` returns `status` (name string), `assignee` (display name or `null`), `parent_id`, `ancestors` and `lock_version`; `list_statuses` returns `id`, `name`, `is_default`, `is_closed`. `list_work_packages` supports `select` and `status` filters, but 001 found it has no parent filter and its field coverage for assignee is not verified.

**Alternatives**: one `list-work-packages` call for the whole project (fewer calls, but pagination, `select` fields and assignee are unverified; revisit as an optimisation); `get-project-work-package-context` per task (it is a schema, not the work package).

## R4. Transition check (workflow)

**Decision**: Never read the workflow administration. For a push, call `update-work-package` (work_package_id, status) **without** `confirm` first and inspect the result:
- `state: preview`, `ready: true`: show it as part of the plan, and after the one plan confirmation call again with `confirm=true`.
- `state: rejected` or non-empty `validation_errors`: `blocked`; report the errors verbatim (redacted); never call with `confirm=true`.
- The preview call raises a tool error: `blocked` for that task with the redacted text (the generic message is not diagnostic); other tasks continue.
The statuses allowed "for the task type" are listed from `get-write-context` (project, type) `available_statuses`; the message says that this is the set for the type, not necessarily for the current status, unless the preview names allowed statuses.

**Rationale** (live): a rejected preview of `update_work_package` is `state: rejected` with readable `validation_errors` and not a tool error; previews show the payload including `lockVersion`. `get_project_work_package_context` narrows `available_statuses` per type only.

**Live 2026-10-06**: an unknown status name makes the preview call fail with the generic tool error (no `validation_errors`), which the rule above treats as `blocked`; an allowed transition previews as `state: preview`, `ready: true` (fixture `tests/fixtures/sync/preview-allowed.json`); setting a closed status also sets `percentageDone: 100` in the payload.

**Unresolved**: that OpenProject rejects a forbidden transition in the **preview** (and not only on confirm) has not been observed. T-task: with a restricted workflow in the sandbox, run the preview and record the result as a fixture; if the preview accepts a transition that confirm then refuses, the prompt must treat a failed confirm of a single task as `failed` (FR-014), and S14 documents it. No code path depends on guessing: both outcomes end in a named state.

**Alternatives**: read `/workflows` (no such capability; admin-only); try intermediate statuses (forbidden by the clarification).

## R5. Checkbox edits in tasks.md

**Decision**: A task line is a line that matches `^(\s*)- \[( |x|X)\] (T\d{3,})\b`. An edit replaces only the character inside the brackets of the line whose key matches (` ` ↔ `x`; an existing `X` is kept when the box stays checked, otherwise written as ` `). Before writing: re-read the file and compare it with the content read at the start (FR-015); on a difference, no write. Write the whole text to `tasks.md.tmp` in the same directory, read it back, verify that the only differences to the original are the planned bracket characters, then move it over `tasks.md`.

**Rationale**: SC-005 demands a diff with only checkbox characters; the keys come from the ledger (`T###`), which also appear in subjects created by 001. The same rule is implemented in `tests/sync_reference.py` so that fixtures can assert it.

**Alternatives**: rewriting the file from a parsed model (loses formatting); editing lines through an agent's edit tool one by one (not atomic: the file could be left half-edited).

## R6. Ledger changes

**Decision**: Add the optional string `assignee` (display name only, no URL, no host, no id of a user) to the ledger item schema, additive, schema version stays `1.0`. `status` already exists (last synced status). The command writes the ledger through a temporary file and a move after each successful push, and once at the end for pulls and refreshes; the ledger is the only place the assignee is kept (clarification). Existing ledgers stay valid.

**Rationale**: the clarification fixes the place of the assignee; additive keys need no major bump (CLAUDE.md).

**Alternatives**: store the assignee id (not useful without another call, and ids of users are PII-adjacent); a separate file (violates one ledger per feature).

## R7. Hook after implement

**Decision**: In `extension/extension.yml` add `hooks.after_implement` with `command: speckit.openproject.sync-status`, `optional: true`, `description` and `prompt`. Key names follow the bundled spec-kit extensions (`agent-context`, `git` in `specify_cli/core_pack/extensions/*/extension.yml`: `hooks.<event>.command`, `optional`, `description`; `prompt` is documented for optional hooks in the spec-kit hook text).

**Rationale**: constitution III (an automatic write to a shared system must be the user's decision); `optional: true` makes the host ask.

**Verified 2026-10-06**: `specify extension add --dev` accepts the `prompt` key and writes `hooks.after_implement` (`optional: true`, `prompt`, `description`) into `.specify/extensions.yml`.

**Unresolved**: whether the `implement` skill of the installed spec-kit actually prints the hook (it reads `.specify/extensions.yml`, which `specify extension add` writes). S16 checks it in a scratch project after `scripts/dev-install.sh`; until then the hook is labelled untested. The 002 prompt states that hook keys were not verified; this feature verifies the manifest side only.

**Alternatives**: mandatory hook (rejected); hook in the preset (the preset has no sync command).

## R8. Capability rows

**Decision**: The prompt embeds `list-statuses`, `get-work-package`, `get-write-context`, `update-work-package` from `docs/mcp-tool-map.md`. The `update-work-package` row's parameter cell is extended with `status` (verified parameters table already lists it; the live check of 2026-10-05 changed only subject/description, so `status` in a preview is marked verified only after the T-task of R4). The 001 prompt embeds the same row; its prompt-sync test requires identity, so the preset prompt is re-embedded with the new parameter cell (a documentation-level change, no behaviour change).

**Alternatives**: a separate capability id `set-status` (more rows, same tool; rejected for simplicity).

## R9. Report and results

**Decision**: Result values as in FR-013: `complete`, `incomplete` (any failed, blocked or skipped), `no changes`, `dry run`, `stopped`. Counts: pulled, pushed, unchanged, refreshed (ledger-only update: status name or assignee differs but done-ness is the same, or "closed, not done" recorded), conflicts, blocked, stale, orphan, unpublished, failed, skipped (a pull or conflict not written because `tasks.md` changed during the run); baseline, reverted and "closed, not done" are labels on items, not counts. `complete` requires at least one applied write (including a ledger-only refresh) and no failed, blocked or skipped item; `no changes` means that nothing was written anywhere. A ledger-only refresh is part of the plan, is shown with the action `refresh` and is written after the single confirmation (in `--dry-run` it is shown, not written).

## Unresolved (to verify live, labelled untested until then)

1. A forbidden transition is rejected in the update **preview** (R4).
2. The exact `get_work_package` fields for status and assignee (R3); assignee is absent or null for an unassigned work package.
3. Hook output by `/speckit-implement` after `specify extension add --dev` (R7).
4. Command mode (`/speckit.openproject.sync-status`) end to end.
5. A work package with a stale `lockVersion` between preview and confirm (concurrent edit): expected to fail the confirm and be reported `failed`.
