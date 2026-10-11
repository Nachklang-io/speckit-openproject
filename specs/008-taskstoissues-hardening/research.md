# Research: taskstoissues Hardening

## R1. How to detect a missing write permission (issue #22)

**Finding (live, read-only, 2026-10-11, sandbox, role "Project admin")**:
- `get_my_project_access` returns `project_id`, `current_user_id` and a `membership` object with `can_update` and `can_update_immediately`. These flags describe the **membership record** (may the user change it), not work package permissions. The brief's idea to check `can_update` is **wrong** and is dropped.
- `list_capabilities` (with `project`) lists the user's action grants. A capability id has the form `<resource>/<action>/w<project_id>-<principal_id>`; for work packages `work_packages/create/w3-5` exists for project 3 and user 5. Without a suffix the id is unknown (`[not_found]`).
- `list_capabilities` with `capability_id = work_packages/create/w<project_id>-<current_user_id>` and `project` returns `total: 1` when the grant exists and the tool error `[not_found] OpenProject resource not found.` when it does not (checked with an id for a user that has no grant). The result also carries a `url` with the server host: it must never be printed or stored.

**Decision**: step 5 reads `project_id` and `current_user_id` (capability `get-my-access`), then asks for the exact capability id (capability `get-capability`). `total` 1 → allowed. `[not_found]` → stop "missing write permission". Any other error or shape → tool error (existing rule: stop and report verbatim, never guess).

**Rationale**: two read-only calls, no write, exact answer for the project. It runs before `list-types`, so a role that sees no types is reported with the right reason.

**Caveats (untested, listed as such until run)**: the server's instructions say capabilities are informational, not the authority. The positive case is verified (admin); the negative case is verified only for a non-existing principal. Whether a real read-only role gets `[not_found]` for `work_packages/create` is **not verified**: it needs a read-only user in the sandbox (maintainer action) and is scenario S7b. Until then the check is labelled untested (R2).

**Alternatives considered**:
- `can_update` of the membership: wrong meaning (see above).
- Only relying on the preview of step 11: it fires after planning and the generic error text is not interpreted (rule of step 11), which is the observed problem for the type list; kept as the final authority for everything the capability check lets through.
- Role names from `get_my_project_access`: roles are free text, no permission data.

## R2. Risk of a wrong "denied" answer

If the capability lookup answered `[not_found]` for a user who may in fact create work packages, the command would block a working setup. That would be a regression of a path that works today.

**Decision**: the stop happens only on `[not_found]` for the exact capability id; any other error or shape is a tool error and stops with the server's text, as today. The message names the project, the user id and the capability id, so a false denial is visible and diagnosable. Before the release: run S7b with a read-only user (denied case) **and** S1 or S2 with the write role through the changed prompt (allowed case). If S7b cannot be run, the release notes and `docs/TESTING.md` say that the denied case is untested.

## R3. Plan rows without ranges and with hashes (issue #23)

The plan table of step 9 lists key, kind, subject, parent key, action, reason; the hash is mentioned only in the "differs, not updated" rule. In a 120-task dry run the model condensed rows.

**Decision**: add two columns, `hash` (current hash, first 12 hex characters) and `stored` (ledger hash, first 12, or `—` without a ledger entry), and a rule: one row per ledger key, never ranges, never "…", never "and N more"; if the table is long, print it in consecutive parts of at most 40 rows, each with the header, and say `part i of n`. The counts line stays. The full hashes stay in the ledger; the table shows prefixes.

**Alternatives**: full 64-character hashes (unreadable, 120 rows × 2); no hash column (the issue asks for them); a separate file with the plan (writes a file in a dry run, forbidden).

## R4. Missing plan.md (issue #21)

**Finding**: `check-prerequisites.sh` already prints `ERROR: plan.md not found in <dir>` and `Run /speckit-plan first to create the implementation plan.` on stderr and exits 1, and tests `plan.md` **before** `tasks.md`. The prompt's step 1 mentions only a missing `tasks.md` and does not say what to do with the script's exit. The skills-mode wording in the script (`/speckit-plan`) is wrong in command mode.

**Decision**: step 1 handles a non-zero exit explicitly: print the script's message verbatim, then name the missing file and the command that creates it for the current mode (`/speckit-plan` or `/speckit.plan`; `/speckit-tasks` or `/speckit.tasks`), and stop. Which file is named follows the script's order (`plan.md` first). The spec's precedence rule was corrected accordingly (the draft said `tasks.md` first, which was never true).

**Alternatives**: testing both files in the prompt before running the script (duplicates the script, changes the order); patching the script (not part of this repo, overwritten by spec-kit updates).

## R5. generic integration (issue #20)

spec-kit registers preset command overrides per integration; the `generic` integration gets none (observed in the T045 command-mode runs, run log 2026-10-09). Documentation only: both READMEs get the same note and the alternative (use a Claude/other integration with preset support, or run the extension commands, which do not need an override).

**Open**: which integrations register overrides is spec-kit's behavior and can change; the note names `generic`, the version it was observed with, and says "check `specify preset list` and the command output".
