# Roadmap

Each item has a brief in `docs/briefs/` that is the input for `/speckit-specify`.

| # | Feature | Package | Outcome | Depends on |
|---|---|---|---|---|
| 001 | Tasks → work packages (hardening of existing preset) | preset | Phase/task hierarchy, relations, idempotent re-run, `--dry-run`, shared config/mapping schemas, tested on test instance | – |
| 002 | Field discovery and config bootstrap | extension | `discover-fields` writes config.yml (types, statuses, custom fields) | 001 |
| 003 | Status sync (OpenProject ↔ tasks.md) | extension | `sync-status`, hook after `implement`, conflict policy | 001, 002 |
| 004 | Spec/plan documentation sync | extension | spec.md/plan.md as attachments + summary in parent work package | 001 |
| 005 | Versions/milestones and time tracking | extension | feature → version, `log-time` | 001, 002 |
| 006 | Release engineering | both | tags `preset-v*`/`extension-v*`, catalog submissions, bundle | 001–005 |

Milestones: M1 = 001 released as preset v1.0.0. M2 = 002+003 as extension v0.1. M3 = 004+005. M4 = catalog submissions.
