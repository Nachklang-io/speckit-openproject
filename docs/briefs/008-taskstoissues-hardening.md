# Brief 008: Hardening of `taskstoissues` after the command-mode runs (preset)

Four small defects in `speckit.taskstoissues` found during the T045 command-mode runs (run log 2026-10-09, PR #19). The preset is the only package that changes; no new config keys, no change to the ledger or schemas. Each item has a GitHub issue.

1. **#23 Large plans are condensed.** A 120-task dry run listed tasks as ranges (`T001–T020`) and skipped hashes. The prompt requires one row per item and forbids ranges and omitted hash columns in the plan and in the report.
2. **#22 Read-only role.** `list-types` returns an empty list for a role without write permission, so the stop reason says "types are missing". The prompt checks the write permission first (`can_update` in the project context, to be verified against the tool map before use) and stops with "missing write permission" and the role, not with a types message.
3. **#21 Missing `plan.md`.** Step 1 names only a missing `tasks.md`; a missing `plan.md` stops in `check-prerequisites.sh` without a hint. The prompt names `plan.md` and the command that creates it (`/speckit-plan`).
4. **#20 `generic` integration (documentation only).** spec-kit registers no preset command overrides for the `generic` integration, so `/speckit.taskstoissues` stays the core GitHub-issues command there. Add a note to `preset/README.md` and the main README; no prompt change. Can be done in the same PR or on its own.

Out of scope: #24 (file hints in backticks) is already shipped since preset 1.0.0 (`a54012d`); it was closed with a pointer to that commit.

Constraints: preset 1.0.3 (patch, wording and checks only), prompts stay deterministic and numbered with explicit stop conditions; every changed stop path gets a prompt-sync test and a scenario in `docs/TESTING.md` (S7 for the read-only role, a large-plan dry run for the ranges, a missing `plan.md` case). Run the scenarios live against the sandbox with `--dry-run` first and record what was actually executed.

Acceptance: a 120-task dry run lists 120 task rows with hashes; the read-only role stops with the permission message; a missing `plan.md` stops with the specific message; the README names the `generic` limitation.
