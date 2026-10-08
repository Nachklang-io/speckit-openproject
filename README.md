# speckit-openproject

Run projects end to end with [spec-kit](https://github.com/github/spec-kit) and [OpenProject](https://www.openproject.org): tasks become work packages with hierarchy and dependencies, status and time flow back, specs and plans are attached, features map to versions. OpenProject is accessed through an MCP server (default: [`openproject-ce-mcp`](https://github.com/jtauschl/openproject-ce-mcp), Community Edition compatible).

| Package | Path | Version | Tag |
|---|---|---|---|
| Preset `openproject` (overrides `speckit.taskstoissues`) | [`preset/`](preset) | 1.0.0 | `preset-v*` |
| Extension `openproject` (discover-fields, sync-status, sync-docs, sync-version, log-time) | [`extension/`](extension) | 0.1.0 | `extension-v*` |
| Bundle `openproject` (preset + extension, pinned) | [`bundle/`](bundle) | 0.1.0 | `bundle-v*` |

Requires spec-kit ≥ 1.1.0 and an OpenProject MCP server configured in your agent's MCP client.

## Install

From the GitHub releases (see [releases](https://github.com/Nachklang-io/speckit-openproject/releases) for the current versions):

```bash
specify preset add --from https://github.com/Nachklang-io/speckit-openproject/releases/download/preset-v1.0.0/openproject-preset-1.0.0.zip
specify extension add openproject --from https://github.com/Nachklang-io/speckit-openproject/releases/download/extension-v0.1.0/openproject-extension-0.1.0.zip
```

`specify extension add` asks you to confirm the download source; answer `y`. To install both in one step, use the bundle: see [`bundle/README.md`](bundle/README.md). Changes per package: [`CHANGELOG.md`](CHANGELOG.md).

For development, from a clone: `scripts/dev-install.sh` (installs both packages with `--dev` into `.scratch/`).

## Docs

[architecture](docs/ARCHITECTURE.md) · [roadmap](docs/ROADMAP.md) · [first session](docs/BOOTSTRAP.md) · [testing](docs/TESTING.md) · [releasing](docs/RELEASING.md) · [publishing](docs/PUBLISHING.md).

Development is AI-assisted with Claude Code and follows spec-kit itself; see [`CLAUDE.md`](CLAUDE.md) and the [constitution](.specify/memory/constitution.md).

License: MIT
