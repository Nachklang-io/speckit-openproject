# spec-kit ↔ OpenProject

Monorepo that delivers full spec-kit ↔ OpenProject integration:

- `preset/` – spec-kit **preset** `openproject`: overrides `speckit.taskstoissues` (tasks.md → work packages).
- `extension/` – spec-kit **extension** `openproject`: new commands for field discovery, status sync, docs sync, versions and time tracking.
- `schemas/` – shared JSON schemas (config, mapping file). Single source of truth for both packages.
- `docs/` – architecture, ADRs, roadmap, feature briefs. Read `docs/ARCHITECTURE.md` before structural work.

Goal: run a project end to end with spec-kit and OpenProject, no manual copying between the two.

## Working language
Talk to the maintainer (Daniel) in German. Everything in the repo (code, docs, commits, issues) is English.

## How we work: dogfood spec-kit
This repo is itself a spec-kit project (Claude integration, skills mode). Non-trivial work follows:
`/speckit-constitution` (once) → `/speckit-specify` → `/speckit-clarify` → `/speckit-plan` → `/speckit-tasks` → `/speckit-analyze` → `/speckit-implement`.
- Start each feature from its brief in `docs/briefs/NNN-*.md`; the brief is input, `specs/NNN-*/spec.md` is the contract.
- Do not write code for a feature before spec, plan and tasks exist and `/speckit-analyze` is clean.
- One feature = one branch (`NNN-short-name`) = one PR. Small commits, Conventional Commits.
- Ask the maintainer when a requirement is ambiguous or a decision is irreversible. Do not guess.
- Use plan mode for anything touching more than ~3 files. Use subagents (`.claude/agents/`) for review, keep the main context for implementation.

## Commands
- Install dev tools: `uv sync` (Python ≥ 3.11), `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`
- Test: `uv run pytest` · Lint/format: `uv run ruff check . && uv run ruff format --check .`
- Local install into a scratch project: `scripts/dev-install.sh` (creates `.scratch/`, installs preset and extension with `--dev`)
- Validate manifests only: `uv run pytest tests/test_manifests.py`

## Hard rules
- OpenProject is accessed **only through an MCP server** (default `jtauschl/openproject-ce-mcp`, verified v0.4.1). Never call the REST API from prompts or scripts in this repo (ADR-0002).
- Never write API tokens, URLs of private instances or `.env` content into any file, commit, work package or log. Tokens live in the MCP client config only. A hook blocks edits to secret files.
- Every write path is idempotent: re-running a command must not create duplicates. Mapping file `.specify/openproject/mapping-<feature>.json` (one per feature) is the ledger (`schemas/mapping.schema.json`).
- Prompts (command markdown) are code: keep them deterministic, numbered, with explicit stop conditions and no hidden assumptions about tool names; map capabilities → tool names in one place.
- Commands must work in skills mode (`/speckit-<name>`) and command mode (`/speckit.<name>`).
- Never rename or delete shipped config keys without a major version bump and a migration note.
- Wiki pages cannot be created via the OpenProject API v3. Docs sync uses attachments and work package descriptions (ADR-0003).

## Verification before "done"
1. `uv run pytest` and `ruff` pass.
2. `scripts/dev-install.sh` installs both packages into a fresh spec-kit project without errors and `specify preset list` / `specify extension list` show them.
3. For OpenProject-touching features: run the integration scenario in `docs/TESTING.md` against the maintainer's test instance with `--dry-run` first. Report what was actually executed; never claim an untested path works.
4. Run the `spec-conformance-reviewer` and `openproject-api-reviewer` subagents on the diff.

## Pointers
- Constitution: `.specify/memory/constitution.md`
- Domain notes (OpenProject concepts, MCP tool map): `.claude/skills/openproject-domain/SKILL.md`
- Roadmap and milestones: `docs/ROADMAP.md`
- First session guide: `docs/BOOTSTRAP.md`
