# Brief 001: Tasks → work packages (preset hardening)

Input for `/speckit-specify`. Existing draft: `preset/`.

Problem: Teams using spec-kit want `tasks.md` turned into trackable OpenProject work packages without duplicates, with hierarchy and dependencies.

Wanted behavior: resolve config; verify MCP tools, project, types; parse phases/tasks/`[P]`/dependencies; skip already created items via mapping ledger and search; create phase and task work packages with parents; create `follows` relations; summary report; `--dry-run`; `--update`.

Open points to settle in clarify: feature → parent work package vs. version; how labels/tags are represented; behavior for 100+ tasks and preview-confirm friction; unification of config/mapping paths under `.specify/openproject/`; JSON schemas for config and mapping.

Acceptance: scenarios S1–S7 in `docs/TESTING.md` pass on the test instance; CI smoke test installs the preset.
