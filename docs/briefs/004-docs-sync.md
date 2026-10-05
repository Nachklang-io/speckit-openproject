# Brief 004: Spec/plan documentation sync (extension)

Command `speckit.openproject.sync-docs`: attach `spec.md`, `plan.md` (and optionally `research.md`, `data-model.md`) to the feature's parent work package, replace outdated attachments by content hash, keep a generated summary with links in the description. See ADR-0003. Acceptance: changed spec.md results in one new attachment version and updated summary; unchanged files cause no writes.
