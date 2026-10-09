# Implementation Plan: Parent Status Roll-up

**Branch**: `007-parent-status-rollup` | **Date**: 2026-10-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/007-parent-status-rollup/spec.md`

## Summary

Extend the extension command `speckit.openproject.sync-status` (`extension/commands/sync-status.md`) so that, after the task pushes and pulls, it rolls the status of the phase work packages up from their tasks and the status of the feature work package up from its phases. The roll-up is a fixed rule (all finished → done, any started → in progress, else open), protected by guards: a parent in done, in another closed status or in a status outside the three configured ones is never written. Parent writes are part of the one plan and the one confirmation of the run, use the same preview-then-confirm flow and failure classes as task pushes, and are recorded in the ledger after each write. A new optional config key `rollup_parents: false` switches the roll-up off (default on). As in 001–006 no runtime code is shipped: correctness rests on the prompt, the schema, a fixture-driven reference implementation of the roll-up in the tests, prompt-sync tests and manual scenarios S34–S38 run through the installed skill.

## Technical Context

**Language/Version**: Markdown prompts + YAML/JSON; Python ≥ 3.11 for dev tooling and tests only

**Primary Dependencies**: shipped: none. Dev: pytest, pyyaml, jsonschema, ruff (already in `pyproject.toml`). Runtime: spec-kit ≥ 1.1, MCP server `jtauschl/openproject-ce-mcp` ≥ 0.4.1

**Storage**: reads `.specify/openproject/config.yml` (new optional key `rollup_parents`); reads and writes `.specify/openproject/mapping-<feature>.json` (only `status` of `phase` and `feature` items is new as a write); `tasks.md` handling unchanged

**Testing**: pytest (schema, prompt sync incl. the new `rollup-table` block and the extended config-rules line in all six prompts, roll-up rule against fixtures); manual scenarios S34–S38 in `docs/TESTING.md`

**Target Platform**: any agent supporting spec-kit skills/command mode; OpenProject Community Edition

**Project Type**: spec-kit extension (prompt package) in a monorepo, plus one additive config schema change that touches the preset prompt's config-rules block

**Performance Goals**: no extra reads per parent (step 6 already reads every ledger item); one preview and one confirm per parent write, plus one recheck read; the dogfood case (53 parents) stays one confirmation

**Constraints**: MCP-only (ADR-0002); no secrets, hosts or URLs in files or output; writes only through preview-then-confirm and only `status`; ledger updated right after each write; never move a parent out of done; no deletes, creates or re-parenting; shipped keys stable (`rollup_parents` is additive)

**Scale/Scope**: one feature per run: one feature work package, up to ~10 phases, tens of tasks

## Constitution Check

| Principle | Status | Evidence |
|---|---|---|
| I Spec-driven | Pass | specify → clarify (7 answers) → plan; tasks and analyze follow |
| II MCP-only | Pass | no new capability; `get-work-package`, `get-write-context` and `update-work-package` (status only) are already in the sync-status map |
| III Idempotent/safe (NON-NEGOTIABLE) | Pass | parents in the dry-run plan, one confirmation, preview/confirm per parent, recheck before confirm, a recomputed target that differs from the previewed one is skipped (R6), ledger written after each write, `O` = `R` → no write so a second run is a no-op (SC-003), done/closed/unmapped parents never written |
| IV Test-first incl. prompts | Pass, with caveat | the roll-up rule has a reference implementation (`tests/rollup_reference.py`) and fixtures; the prompt block is checked against it; S34–S38 manual; the workflow behaviour of parent types is unverified until S38 (research "Unresolved") and stays labelled |
| V Compatibility | Pass | skills + command mode unchanged; config key additive, absent = on (FR-014); with `rollup_parents: false` the run is identical to 0.1.0 (SC-006); hook unchanged (FR-015); preset patch release because its embedded config-rules line changes (R1) |
| VI Simplicity/transparency | Pass | one rule, one table, no scripts; every left-alone parent is reported with a reason |

Post-design re-check: Pass. The default-on behaviour change is not a violation: it is the requested feature, versioned as extension 0.2.0 and documented in the CHANGELOG; the switch-off path keeps the old behaviour.

## Project Structure

### Documentation (this feature)

```text
specs/007-parent-status-rollup/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── command-contract.md
│   └── schema-changes.md
├── checklists/requirements.md
└── tasks.md             # created by /speckit-tasks
```

### Source Code (repository root)

```text
extension/
├── extension.yml                          # version 0.2.0; command and hook unchanged
├── README.md                              # roll-up rules, switch, untested paths
└── commands/
    ├── sync-status.md                     # roll-up steps 7, 8, 14; rollup-table block; overrides and rules rewritten; config-rules
    ├── discover-fields.md                 # config-rules block only (keeps rollup_parents as it is)
    ├── sync-docs.md                       # config-rules block only
    ├── sync-version.md                    # config-rules block only
    └── log-time.md                        # config-rules block only
preset/
├── preset.yml                             # version 1.0.2
├── openproject-config.template.yml        # commented-out rollup_parents with explanation
└── commands/speckit.taskstoissues.md      # config-rules block only
bundle/
└── bundle.yml                             # version 0.2.0, pins preset 1.0.2 and extension 0.2.0
schemas/
└── config.schema.json                     # + optional boolean rollup_parents
tests/
├── fixtures/
│   ├── sync/rollup-*.json                 # secret-free roll-up cases
│   └── config/{valid-rollup-off,invalid-rollup-type}.yml
├── rollup_reference.py                    # reference implementation of the roll-up (test helper only)
├── test_rollup.py                         # rule cases, guards, feature order, idempotence
├── test_schemas.py                        # extend
└── test_prompt_sync.py                    # rollup-table block; config-rules line from schema (already generic)
docs/
├── ARCHITECTURE.md                        # sync policy: parents rolled up
├── TESTING.md                             # S34–S38 and run results
└── ROADMAP.md                             # row 007
CHANGELOG.md                               # extension 0.2.0, preset 1.0.2, bundle 0.2.0
```

**Structure Decision**: Existing monorepo layout. The behaviour change lives in one prompt (`sync-status.md`); the other five prompts change only their embedded config-rules block, which the existing prompt-sync test derives from the schema.
## Complexity Tracking

No constitution violations.

## Risks

1. **Parent workflows.** The phase type ("Summary task") or the feature type may forbid New → Closed or In progress → New. Mitigation: a rejected preview or a tool error on the preview makes the parent `blocked` (same as tasks), the plan shows it before the question, the feature counts with the phase's real status (R5). S38 records the live behaviour.
2. **Plan drift between preview and write.** A task push can fail after its parent was previewed with "done". Mitigation: step 14 recomputes from actual outcomes and never writes a target that differs from the previewed one (`skipped`, `plan changed`); a re-run applies it with a fresh preview.
3. **Config compatibility across packages.** All prompts reject unknown keys; a user who sets `rollup_parents` with preset 1.0.1 gets a config error in `speckit.taskstoissues`. Mitigation: config-rules of all six prompts change in one PR (prompt-sync test enforces it), preset 1.0.2 and bundle 0.2.0, the template only shows the key commented out, README and CHANGELOG say which versions are needed.
4. **Default-on surprises teams with hand-managed parents.** Mitigation: done/closed/unmapped parents are never touched, every parent write is in the plan before the one question, `--dry-run` shows it, the switch is documented in the extension README and the CHANGELOG.
5. **Longer prompt, more agent drift.** sync-status grows by three steps. Mitigation: the rule is a single embedded table mirrored in the tests; verification runs the installed skill in a fresh session (S34–S38), not a manual walkthrough.
