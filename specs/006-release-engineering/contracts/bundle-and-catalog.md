# Contract: Bundle definition and generated catalogs

## `bundle/bundle.yml` (spec-kit bundle schema 1.0)

```yaml
schema_version: "1.0"
bundle:
  id: openproject
  name: "OpenProject for spec-kit"
  version: "0.1.0"
  role: developer
  description: "Preset and extension for running a spec-kit project with OpenProject via MCP"
  author: "Daniel Ring"
  license: MIT
requires:
  speckit_version: ">=1.1.0"
presets:
  - id: openproject
    version: "1.0.0"
extensions:
  - id: openproject
    version: "0.1.0"
tags: [openproject, project-management, mcp]
```

- `bundle/README.md` is required by `specify bundle build`. It contains the install steps below.
- `specify bundle validate --path bundle` must pass in CI.
- The exact optional keys (`priority`, `strategy`, `source`, `requires.tools/mcp`) are confirmed against the pinned spec-kit at implementation time. `source` is not used for installation.

## Generated catalog files (bundle release assets)

`openproject-presets-catalog.json`:

```json
{
  "schema_version": "1.0",
  "updated_at": "<ISO-8601 at generation>",
  "presets": {
    "openproject": {
      "id": "openproject",
      "name": "<from preset.yml>",
      "version": "1.0.0",
      "description": "<from preset.yml>",
      "author": "<from preset.yml>",
      "license": "MIT",
      "repository": "https://github.com/<owner/repo>",
      "download_url": "https://github.com/<owner/repo>/releases/download/preset-v1.0.0/openproject-preset-1.0.0.zip",
      "sha256": "<hex of the published archive>",
      "requires": { "speckit_version": ">=1.1.0" }
    }
  }
}
```

`openproject-extensions-catalog.json` has the same shape with the key `extensions` and the extension's values.

`updated_at` is the only non-deterministic field.

## User install path (US5-2)

```bash
specify preset catalog add <bundle release URL>/openproject-presets-catalog.json --name openproject --install-allowed
specify extension catalog add <bundle release URL>/openproject-extensions-catalog.json --name openproject --install-allowed
curl -LO <bundle release URL>/openproject-<bundle version>.zip
specify bundle install ./openproject-<bundle version>.zip
```

spec-kit resolves each component through these catalogs, downloads the published archive, verifies the `sha256` and enforces the pinned version.

**Verify in the rc run**: the catalog fetch follows GitHub's redirect from `releases/download` to its object host, and both catalog and archive downloads succeed anonymously.
