# spec-kit-openproject Constitution

## Core Principles

### I. Spec-Driven, Always
Every feature is specified, planned and tasked with spec-kit before implementation. The repository is its own first customer. Specs describe behavior and acceptance criteria, never prompt wording.

### II. MCP-Only Access to OpenProject
All OpenProject interaction goes through an MCP server. No direct REST calls, no credentials in the repo. Tool names are resolved by capability in one mapping table so alternative MCP servers can be supported without rewriting commands.

### III. Idempotent and Safe by Default (NON-NEGOTIABLE)
Re-running any command never duplicates or destroys data. Every write command supports `--dry-run`, shows a plan first, honors the MCP server's preview-then-confirm flow, and records results in the mapping ledger immediately after each write. Deletions are never performed by this project. Exception: an attachment this project uploaded itself, identified by the ledger, may be deleted when a newer version of the same document replaces it, and only after the plan was shown and confirmed (ADR-0004).

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
This constitution supersedes other practices. Where a spec, plan, task list or prompt conflicts
with it, the constitution wins and the conflicting artifact MUST be fixed.

- **Amendments**: Proposed in a PR that changes this file and adds an ADR in `docs/adr/`. The
  maintainer approves. Principle removals or redefinitions MUST include a migration note.
- **Versioning** (semantic): MAJOR for backward-incompatible removal or redefinition of a
  principle; MINOR for a new principle or section, or materially expanded guidance; PATCH for
  clarifications and wording.
- **Compliance review**: `/speckit-analyze` treats constitution violations as CRITICAL. The
  `spec-conformance-reviewer` and `openproject-api-reviewer` subagents check every diff, and
  reviewers MUST reject PRs that violate a principle without a justified, documented exception.
- **Runtime guidance**: `CLAUDE.md` holds day-to-day instructions and MUST NOT contradict this file.

**Version**: 1.2.0 | **Ratified**: 2026-10-05 | **Last Amended**: 2026-10-06
