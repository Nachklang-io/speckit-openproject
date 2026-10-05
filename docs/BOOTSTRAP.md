# First Claude Code session

Prerequisites on the maintainer machine: Python ≥ 3.11, `uv`, `git`, Claude Code, `gh` (for publishing).

1. `cd` into the repo root, `uv sync`, install the CLI: `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`.
2. Copy `.env.example` to `.env`, fill in the **test** instance URL and a least-privilege token; export the variables in the shell that starts Claude Code (`.mcp.json` expands them). Create a sandbox project in OpenProject and set it as the only write project.
3. Start `claude` in the repo root. Approve the project MCP server `openproject` when asked.
4. Run `/speckit-constitution` and let it confirm/refine `.specify/memory/constitution.md` (already filled in v1.0.0).
5. Pick the first feature: `/speckit-specify` with the content of `docs/briefs/001-tasks-to-work-packages.md`. Then `/speckit-clarify`, `/speckit-plan`, `/speckit-tasks`, `/speckit-analyze`, `/speckit-implement`.
6. Before every PR: run the checks in `CLAUDE.md` ("Verification before done") and both review subagents.

Suggested opening prompt:
> Read CLAUDE.md, docs/ARCHITECTURE.md and docs/briefs/001-tasks-to-work-packages.md. Start with /speckit-specify for feature 001. Ask me when something is ambiguous.

Publishing: see `docs/PUBLISHING.md`.
