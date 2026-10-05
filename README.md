# speckit-openproject

Run projects end to end with [spec-kit](https://github.com/github/spec-kit) and [OpenProject](https://www.openproject.org): tasks become work packages with hierarchy and dependencies, status and time flow back, specs and plans are attached, features map to versions. OpenProject is accessed through an MCP server (default: [`openproject-ce-mcp`](https://github.com/jtauschl/openproject-ce-mcp), Community Edition compatible).

| Package | Path | Status |
|---|---|---|
| Preset `openproject` (overrides `speckit.taskstoissues`) | [`preset/`](preset) | draft, installs on spec-kit 1.1.1 |
| Extension `openproject` (discover-fields, sync-status, sync-docs, log-time) | [`extension/`](extension) | skeleton |

Docs: [architecture](docs/ARCHITECTURE.md) · [roadmap](docs/ROADMAP.md) · [first session](docs/BOOTSTRAP.md) · [testing](docs/TESTING.md) · [publishing](docs/PUBLISHING.md).

Development is AI-assisted with Claude Code and follows spec-kit itself; see [`CLAUDE.md`](CLAUDE.md) and the [constitution](.specify/memory/constitution.md).

Quick try: `scripts/dev-install.sh`.

License: MIT
