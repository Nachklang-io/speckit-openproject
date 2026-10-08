# Contract: `.github/workflows/release.yml`

## Trigger

```yaml
on:
  push:
    tags: ["preset-v*", "extension-v*", "bundle-v*"]
```

There is no `workflow_dispatch`. A re-run is a GitHub "Re-run jobs" on the same tag run, or a re-push of the same tag on the same commit. The strict grammar is enforced by `release.py check` (FR-001).

## Jobs

### `verify` (permissions: `contents: read`)

1. Check out the tagged commit; run `uv sync`.
2. Run `release.py check $TAG --repository $GITHUB_REPOSITORY` and capture its JSON.
3. Run `ruff check .`, `ruff format --check .` and `pytest`.
4. For preset or extension: run `release.py build <kind> --version <tagversion>` and then `release.py verify-archive`. Upload the archive as a workflow artifact.
5. For a bundle, also:
   1. Resolve each pin to a component release tag. A final bundle tag maps to `<kind>-v<pin>`. A pre-release bundle tag with suffix `-S` maps to `<kind>-v<pin>-S`, so `bundle-v0.1.0-rc.1` uses `preset-v1.0.0-rc.1` and `extension-v0.1.0-rc.1`. Check that `gh release view <component tag>` succeeds and lists its archive. Otherwise fail with `missing release: <component tag>`.
   2. Download both archives with `gh release download`.
   3. Run `release.py bundle-catalog`.
   4. Install the pinned `specify-cli` and run `specify bundle build --path bundle --output dist`.
   5. Upload the bundle zip and the catalog files as artifacts.
6. Run `release.py notes <kind> <core>` and append `<!-- release-commit: $GITHUB_SHA -->`. Upload the result as an artifact.

### `publish` (needs: `verify`; permissions: `contents: write`)

The publish job installs no dependencies and runs no repository code except `python3 scripts/release.py publish-plan` (stdlib only, from the tagged commit), which turns the existing release state into the action of the table below. It uses `gh` with `GITHUB_TOKEN`.

| Existing release for `$TAG` | Marker in its notes | Action | Outcome message |
|---|---|---|---|
| none | — | `gh release create $TAG <assets> --title $TAG --notes-file notes.md [--prerelease --latest=false]` | `created <tag>` |
| exists | equals `$GITHUB_SHA` | Upload each asset not in the release, with `gh release upload` (no `--clobber`) | `completed <tag>: uploaded <names>`, or `release exists, complete: <tag>` |
| exists | differs or missing | Write nothing; fail | `conflict: release <tag> was created from <sha-old>, tag now points to <sha-new>` |

Release notes and existing assets are never edited (FR-004).

## Invariants

- If any `verify` step fails, nothing is published (SC-003).
- No job has MCP configuration or OpenProject secrets (FR-013). The only secret used is `GITHUB_TOKEN`.
- Pre-release tags get `--prerelease --latest=false`.
