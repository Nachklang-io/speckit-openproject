# ADR-0001: One monorepo for preset and extension

Status: accepted (2026-10-05)

Context: The preset (overrides `speckit.taskstoissues`) and the extension (new commands) share config format, mapping ledger and test fixtures. Extensions cannot override core commands, so both artifact types are needed.

Decision: One repo with `preset/` and `extension/`, shared `schemas/`, independent tags `preset-v*` and `extension-v*`.

Consequences: Easier coordinated changes. Catalog submissions need the repo layout explained; if a catalog requires a repo root manifest, split later (history is preserved via subtree split).
