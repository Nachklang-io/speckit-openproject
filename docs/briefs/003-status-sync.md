# Brief 003: Status sync OpenProject ↔ tasks.md (extension)

Command `speckit.openproject.sync-status` plus optional hook after `implement`. Direction: status/assignee from OpenProject → checkboxes in `tasks.md` and ledger; completed tasks in `tasks.md` → status transition in OpenProject (respecting workflow). Conflict policy and dry-run required. Acceptance: round-trip scenario with changes on both sides produces a deterministic, reported result without data loss.
