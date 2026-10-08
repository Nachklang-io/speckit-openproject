# Contract: Package archive layout

## Name

`openproject-<kind>-<tagversion>.zip`, for example `openproject-extension-0.1.0-rc.1.zip`.

## Content

The archive contains every regular file under `<kind>/` (`preset/` or `extension/`), at the path relative to that directory. It excludes:
- names starting with `.`
- `__pycache__/` directories
- `*.pyc` files

The manifest (`preset.yml` / `extension.yml`, `bundle.yml` for the bundle archive) is at the archive root. Each package directory already contains `LICENSE`, so nothing is copied in from outside the package (FR-002, FR-012).

Expected entries today:

| Preset | Extension |
|--------|-----------|
| `preset.yml`, `README.md`, `LICENSE`, `openproject-config.template.yml`, `commands/speckit.taskstoissues.md` | `extension.yml`, `README.md`, `LICENSE`, `commands/{discover-fields,log-time,sync-docs,sync-status,sync-version}.md` |

## Reproducibility

- Entries are sorted by path.
- Each entry has the timestamp 1980-01-01 00:00:00, permissions 0644 and `ZIP_DEFLATED` compression.
- The same tree gives the same sha256.

## Forbidden (checked by `verify-archive`, SC-004)

- Paths: `.env` anywhere; a component named `.scratch`, `tests`, `specs` or `docs`; any path containing `..` or starting with `/`; any other hidden path.
- Entries outside the allowlist: root `*.yml`, root `*.md`, root `LICENSE`, `commands/*.md`. Anything else (scripts, nested directories, other file types) fails as `entry not allowed`.
- Content:
  - the regex `OPENPROJECT_API_(?:TOKEN|KEY)['"]?\s*[=:]\s*['"]?[A-Za-z0-9_-]{16,}` (env, YAML and JSON forms)
  - any `http(s)://` host outside the allowlist `github.com`, `raw.githubusercontent.com`, `www.openproject.org`, `example.com` and its subdomains

The allowlist is a constant in `scripts/release.py`. Extending it is a reviewed code change.

The release workflow also runs `verify-archive` on the bundle archive built by `specify bundle build`; there `bundle.yml` counts as the root manifest. The same content rules apply to the release notes and the two bundle catalogs through `verify-text` (FR-012).
