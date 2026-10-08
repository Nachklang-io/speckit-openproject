# Catalog submission

Prepared text for submitting the packages to the spec-kit community catalogs. The maintainer files them (FR-015); nothing here is sent automatically.

Upstream rules as read on 2026-10-08 (research R9): extensions are submitted **only** through the "Extension Submission" issue form, not as a PR. Presets have an issue form and a PR path described in `presets/PUBLISHING.md`. Bundles have their own issue form.

## Status

| Package | Issue | Filed |
|---------|-------|-------|
| Preset `openproject` 1.0.0 | https://github.com/github/spec-kit/issues/4886 | 2026-10-08 |
| Extension `openproject` 0.1.0 | https://github.com/github/spec-kit/issues/4887 | 2026-10-08 |
| Bundle `openproject` 0.1.0 | not filed; waits until both are listed | |

The forms read on 2026-10-08 at filing time also ask for key features, a testing checklist, testing details and example usage; the filed issues answer them. The preset form has no catalog-entry field, so the preset issue links `preset-entry.json` instead.

## Before filing

1. The final tags are published (T038): `preset-v1.0.0`, `extension-v0.1.0`, then `bundle-v0.1.0`.
2. Download each asset anonymously and compute its checksum:

   ```bash
   curl -fsSLO https://github.com/Nachklang-io/speckit-openproject/releases/download/preset-v1.0.0/openproject-preset-1.0.0.zip
   curl -fsSLO https://github.com/Nachklang-io/speckit-openproject/releases/download/extension-v0.1.0/openproject-extension-0.1.0.zip
   sha256sum openproject-preset-1.0.0.zip openproject-extension-0.1.0.zip
   ```

3. Replace `"sha256": "PENDING"` in `preset-entry.json` and `extension-entry.json` with these values and commit.
4. Re-read the upstream sources linked in the checklists. If they changed, update the checklists first.
5. Every `gap` in `preset-checklist.md` and `extension-checklist.md` is closed or accepted.

Order: preset and extension first. The bundle follows after both are listed, because its components must resolve from the catalogs.

## Preset

### Issue form "Preset Submission" (preferred)

| Field | Answer |
|-------|--------|
| Preset ID | `openproject` |
| Preset name | OpenProject Work Packages |
| Version | 1.0.0 |
| Description | Overrides speckit.taskstoissues to create OpenProject work packages (phases, tasks, sub-tasks, relations) via an OpenProject MCP server instead of GitHub Issues |
| Author | Daniel Ring |
| Repository URL | https://github.com/Nachklang-io/speckit-openproject |
| Download URL | https://github.com/Nachklang-io/speckit-openproject/releases/download/preset-v1.0.0/openproject-preset-1.0.0.zip |
| Documentation URL | https://github.com/Nachklang-io/speckit-openproject/blob/preset-v1.0.0/preset/README.md |
| License | MIT |
| Required spec-kit version | >=1.1.0 |
| Templates provided | none |
| Commands provided | `speckit.taskstoissues` (replaces the core command) |
| Tags | openproject, issue-tracking, project-management, mcp, preset |
| Catalog entry | contents of `docs/catalog/preset-entry.json` |

Additional context:

> The preset lives in the `preset/` directory of a monorepo that also holds the `openproject` extension. The release asset is a self-contained archive with `preset.yml` at its root; the documentation link points to `preset/README.md`, as PUBLISHING.md asks for monorepos. The preset talks to OpenProject only through an MCP server (default `jtauschl/openproject-ce-mcp` ≥ 0.4.1) and never calls the REST API. Tested against a self-hosted OpenProject Community Edition instance.

### PR fallback (if the maintainers ask for a PR)

- Branch: `add-openproject-preset`
- Files: add the entry from `preset-entry.json` to `presets/catalog.community.json` (alphabetical), and a row to `docs/community/presets.md`.
- Title: `Add openproject preset to community catalog`
- Body:

  > Adds the `openproject` preset (v1.0.0). It overrides `speckit.taskstoissues` to create OpenProject work packages via an OpenProject MCP server.
  >
  > - Repository: https://github.com/Nachklang-io/speckit-openproject (monorepo; preset in `preset/`)
  > - Documentation: https://github.com/Nachklang-io/speckit-openproject/blob/preset-v1.0.0/preset/README.md
  > - Install: `specify preset add --from https://github.com/Nachklang-io/speckit-openproject/releases/download/preset-v1.0.0/openproject-preset-1.0.0.zip`
  >
  > Checklist: https://github.com/Nachklang-io/speckit-openproject/blob/main/docs/catalog/preset-checklist.md

## Extension

### Issue form "Extension Submission"

| Field | Answer |
|-------|--------|
| Extension ID | `openproject` |
| Extension name | OpenProject Integration |
| Version | 0.1.0 |
| Description | Sync fields, status, docs, versions and time between spec-kit and OpenProject via MCP |
| Author | Daniel Ring |
| Repository URL | https://github.com/Nachklang-io/speckit-openproject |
| Download URL | https://github.com/Nachklang-io/speckit-openproject/releases/download/extension-v0.1.0/openproject-extension-0.1.0.zip |
| Documentation URL | https://github.com/Nachklang-io/speckit-openproject/blob/extension-v0.1.0/extension/README.md |
| Changelog URL | https://github.com/Nachklang-io/speckit-openproject/blob/main/CHANGELOG.md |
| License | MIT |
| Required spec-kit version | >=1.1.0 |
| Required tools | `openproject-ce-mcp` >=0.4.1 (an MCP server configured in the AI agent's MCP client, not a CLI) |
| Number of commands | 5 |
| Number of hooks | 1 (`after_implement`, optional) |
| Tags | openproject, project-management, mcp |
| Catalog entry | contents of `docs/catalog/extension-entry.json` |

Commands:

- `speckit.openproject.discover-fields`: read types, statuses and mandatory custom fields, write `.specify/openproject/config.yml`
- `speckit.openproject.sync-status`: sync task progress between work packages and `tasks.md`
- `speckit.openproject.sync-docs`: attach the design documents to the feature work package
- `speckit.openproject.sync-version`: create or reuse the feature's OpenProject version and assign it
- `speckit.openproject.log-time`: log time entries against the feature's work packages

Additional context:

> The extension lives in the `extension/` directory of a monorepo that also holds the `openproject` preset (which overrides `speckit.taskstoissues`). The release asset is a self-contained archive with `extension.yml` at its root. All OpenProject access goes through an MCP server; the extension never calls the REST API and never stores tokens. Every write command supports `--dry-run` and is idempotent through a per-feature mapping file. Tested against a self-hosted OpenProject Community Edition instance.
>
> Checklist: https://github.com/Nachklang-io/speckit-openproject/blob/main/docs/catalog/extension-checklist.md

## Bundle

File only after the preset and the extension are listed, and after closing the gaps in `bundle-checklist.md`.

### Issue form "Bundle Submission"

| Field | Answer |
|-------|--------|
| Bundle ID | `openproject` |
| Version | 0.1.0 |
| Role | developer |
| Description | Preset and extension for running a spec-kit project with OpenProject via MCP |
| Repository URL | https://github.com/Nachklang-io/speckit-openproject |
| Artifact URL | https://github.com/Nachklang-io/speckit-openproject/releases/download/bundle-v0.1.0/openproject-0.1.0.zip |
| Documentation URL | https://github.com/Nachklang-io/speckit-openproject/blob/bundle-v0.1.0/bundle/README.md |
| License | MIT |
| Components | preset `openproject` 1.0.0, extension `openproject` 0.1.0 |
| Required catalogs | none once both components are in the community catalogs |
