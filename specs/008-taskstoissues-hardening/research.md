# Research: taskstoissues Hardening

## R1. How to detect a missing write permission (issue #22)

**Finding (live, read-only, 2026-10-11, sandbox, role "Project admin")**:
- `get_my_project_access` returns `project_id`, `current_user_id` and a `membership` object with `can_update` and `can_update_immediately`. These flags describe the **membership record** (may the user change it), not work package permissions. The brief's idea to check `can_update` is **wrong** and is dropped.
- `list_capabilities` (with `project`) lists the user's action grants. A capability id has the form `<resource>/<action>/w<project_id>-<principal_id>`; for work packages `work_packages/create/w3-5` exists for project 3 and user 5. Without a suffix the id is unknown (`[not_found]`).
- `list_capabilities` with `capability_id = work_packages/create/w<project_id>-<current_user_id>` and `project` returns `total: 1` when the grant exists and the tool error `[not_found] OpenProject resource not found.` when it does not (checked with an id for a user that has no grant). The result also carries a `url` with the server host: it must never be printed or stored.

**Decision (revised after `/speckit-analyze` F1)**: do not build a capability id by hand: its format (`w<project_id>-<principal_id>`) was observed on one server and project only. Step 5 reads `current_user_id` (capability `get-my-access`), then lists the project's capabilities (capability `list-capabilities`, `select` = `id`, `action_id`; `limit` 50, all pages; `select` also keeps the `url` field with the server host out of the output). It looks for entries whose id starts with `work_packages/read/` or `work_packages/create/` and ends with `-<current_user_id>`.
- read **and** create found → continue.
- read found, create **not** found → stop "missing write permission" (positive evidence of a read-only role).
- read not found, or the list is empty or has another shape → no evidence: continue as today; step 11's preview stays the authority.
- tool error → existing rule: stop and report verbatim.

**Rationale**: a wrong id format or an unexpected list can only lead to "no evidence", never to a false stop of a working setup. Two read capabilities, no write; it runs before `list-types`, so a role that sees no types gets the right reason.

**Caveats**: the capability list is informational (server instructions). The positive case is verified (admin: read and create listed for the user); the denied case for a real read-only role is **not** verified and needs a read-only user in the sandbox (scenario S7b, maintainer action). For the sandbox admin the list has 95 entries (2 pages of 50), for the principals 4 and 5 together; a normal user sees fewer.

**Alternatives considered**:
- `can_update` of the membership: wrong meaning (see above).
- Only relying on the preview of step 11: it fires after planning and the generic error text is not interpreted (rule of step 11), which is the observed problem for the type list; kept as the final authority for everything the capability check lets through.
- Role names from `get_my_project_access`: roles are free text, no permission data.

## R2. Risk of a wrong "denied" answer

A false stop would block a working setup, which would be a regression of a path that works today. The design of R1 limits it to the case with positive evidence (read listed, create missing). The message names the project, the user id and the missing permission (`work_packages/create`), so a false denial is visible. Before the release: run S7b with a read-only user (denied case) **and** S1 or S2 with the write role through the changed prompt (allowed case). If S7b cannot be run, the release notes and `docs/TESTING.md` say that the denied case is untested.

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
