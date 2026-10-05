# spec-kit-openproject Constitution

## Core Principles

### I. Spec-Driven, Always
Every feature is specified, planned and tasked with spec-kit before implementation. The repository is its own first customer. Specs describe behavior and acceptance criteria, never prompt wording.

### II. MCP-Only Access to OpenProject
All OpenProject interaction goes through an MCP server. No direct REST calls, no credentials in the repo. Tool names are resolved by capability in one mapping table so alternative MCP servers can be supported without rewriting commands.

### III. Idempotent and Safe by Default (NON-NEGOTIABLE)
Re-running any command never duplicates or destroys data. Every write command supports `--dry-run`, shows a plan first, honors the MCP server's preview-then-confirm flow, and records results in the mapping ledger immediately after each write. Deletions are never performed by this project.

### IV. Test-First, Including the Prompts
Schemas, manifests and helper scripts are covered by automated tests. Command prompts have scenario checklists in `docs/TESTING.md` that are executed against a real test instance before each release. Untested paths are labeled as such in docs.

### V. Compatibility Is a Feature
Support the current and previous minor spec-kit release; support skills and command mode; support OpenProject Community Edition. Version constraints live in `preset.yml` / `extension.yml` and are verified in CI. Shipped config keys are stable API.

### VI. Simplicity and Transparency
Prefer plain Markdown, YAML and small scripts over frameworks. Anything the LLM must decide (type mapping, ambiguous dependencies) is surfaced to the user, not guessed. Document limitations honestly.

## Technical Constraints
- Packages: `preset/` (`preset.yml`) and `extension/` (`extension.yml`) released from one repo with independent tags (`preset-vX.Y.Z`, `extension-vX.Y.Z`).
- Language: English in repo artifacts. License: MIT.
- Python ≥ 3.11 for tooling and tests; no runtime dependencies in the shipped packages.
- No secrets in git, ever. Tokens only in MCP client configuration.

## Development Workflow
- Spec → clarify → plan → tasks → analyze → implement, one feature per branch and PR.
- Conventional Commits; CI (lint, manifest validation, tests, install smoke test) must pass before merge.
- AI-assisted changes are reviewed by the review subagents and a human before merge.
- Breaking changes need an ADR, a major version bump and migration notes.

## Governance
This constitution supersedes other practices. Amendments need an ADR in `docs/adr/` and a version bump below.

**Version**: 1.0.0 | **Ratified**: 2026-10-05 | **Last Amended**: 2026-10-05
