# Contract: `scripts/release.py`

Run as `uv run python scripts/release.py <subcommand> ...` from the repository root. The script uses only the stdlib and PyYAML. It never touches the network, except `bundle-catalog`, which reads only local files that the workflow has already downloaded. Exit code `0` means success. Exit code `1` means a gate failed; the message goes to stderr and starts with `release: `. Exit code `2` means a usage error.

## `check <tag> [--repository <owner/repo>]`

Read-only. Gates for FR-001, FR-003 and FR-008.

1. Parse the tag with the grammar in data-model.md. On a mismatch, fail with `not a release tag: <tag>`.
2. Load the manifest of the tag's kind. If the core version differs from the manifest version, fail with `version mismatch: tag <core> vs <manifest path> <version>`.
3. Find the changelog entry for (kind, core). If it is missing or empty, fail with `missing changelog entry: <Section> <core>`. If the entry has a `**Breaking**` item and no `#### Migration` group, fail with `breaking change without migration note: <Section> <core>`.
4. If `--repository` is given and the kind is preset or extension, the manifest `repository` must equal `https://github.com/<owner/repo>`. Otherwise fail with `repository mismatch: manifest <url> vs publishing repository <url>`.
5. For a bundle, every component pin must be an `X.Y.Z` version. Checking that the matching release exists belongs to the workflow, because it needs `gh`.

On success, the script prints one JSON line to stdout: `{"kind":..., "version":<core>, "tag":..., "prerelease":bool, "archive":<file name>}`.

## `notes <kind> <X.Y.Z>`

Read-only. Prints the changelog entry body (FR-005). Fails as in `check` step 3.

## `build <kind> [--out dist] [--version <tagversion>]`

Writes only below `--out` (default `dist/`). For preset and extension it builds the reproducible ZIP described in archive-layout.md and prints the path and the sha256. It is not used for bundles; those use `specify bundle build`.

## `verify-archive <zip>`

Read-only. Enforces archive-layout.md: the manifest is at the root, every entry is in the allowlist, no forbidden path exists, and no file matches the content rules. Each violation is printed. If there is at least one, the exit code is 1.

## `bundle-catalog --bundle bundle/bundle.yml --tag <bundle tag> --archives <dir> --repository <owner/repo> --out <dir>`

Resolves the component tags from the pins and the bundle tag's suffix, as described in release-workflow.md. It reads the two downloaded package archives from `<dir>`; their names must be exactly the resolved archive names. `download_url` points to the resolved component release. It writes `openproject-presets-catalog.json` and `openproject-extensions-catalog.json` as described in bundle-and-catalog.md. It fails with `missing release archive: <name>` if an archive is absent, and with `pin mismatch` if the manifest inside the archive does not report the pinned version.

## Stop conditions (all subcommands)

- No subcommand creates, edits or deletes anything outside `--out`.
- No subcommand reads `.env`, MCP configuration or any OpenProject setting.
