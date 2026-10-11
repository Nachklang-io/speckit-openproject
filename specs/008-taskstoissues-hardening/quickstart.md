# Quickstart: validating feature 008

Prerequisites: `uv sync`; `scripts/dev-install.sh`; the sandbox project from `docs/TESTING.md`; skills mode.

1. **Automated**: `uv run pytest && uv run ruff check . && uv run ruff format --check .` (prompt-sync tests for the plan table rule, the step 1 handling, the step 5 permission check and the capability rows; fixtures unchanged).
2. **S-large (US1)**: `tests/fixtures/tasks/s-large-tasks.md` (120 tasks) as `tasks.md`, `/speckit-taskstoissues --dry-run`. Expect 120 task rows plus phases and the feature, hash and stored cells in every row, parts of at most 40 rows, no range, nothing written.
3. **S-plan (US3)**: delete `plan.md` from the feature directory, run the command. Expect the script's message and `Missing: plan.md. Run /speckit-plan first.`, nothing written. Repeat with `plan.md` present and `tasks.md` removed.
4. **S1/S2 regression**: the first publish and a re-run with the write role through the changed prompt. Expect the same result as before (created, then all `skip`), no extra write.
5. **S7b (US2, maintainer)**: give the sandbox user a read-only role in the project (admin action), run `--dry-run`. Expect the permission message, no types message, nothing written. Restore the role afterwards. If not run, record it as untested.
6. **Docs (US4)**: read both READMEs for the `generic` note.

Record what was actually run in the run log of `docs/TESTING.md`.
