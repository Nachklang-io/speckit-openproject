# Research: Release Engineering (006)

Findings come from reading the installed `specify-cli` 1.1.1.dev0 source (`specify_cli/presets/_catalog.py`, `extensions/__init__.py`, `bundles/*`) and the upstream tag list (latest stable `v1.1.2` on 2026-10-08). Items marked **verify in rc run** are inferred from source and are confirmed only by the pre-release run (SC-007).

## R1 Archive format and layout

- **Decision**: One ZIP per package, named `openproject-preset-<tagversion>.zip` / `openproject-extension-<tagversion>.zip`. The manifest (`preset.yml` / `extension.yml`) sits at the archive root, next to the package's own files (commands, README, LICENSE, template). Built from an allowlist: every regular file under the package directory, excluding dotfiles, `__pycache__/` and `*.pyc`. Entries are sorted and carry a fixed timestamp, so the same tree gives the same bytes.
- **Rationale**: `specify preset add --from` and `specify extension add --from` accept `.zip`/`.tar.gz`/`.tgz` and look for the manifest at the archive root or in exactly one top-level directory. The root is the simplest valid layout. Both package directories already contain their own `LICENSE`, so no shared file must be copied in (FR-012). Reproducible bytes allow the CI test to compare a rebuild with a checksum and make the bundle checksum (R8) meaningful.
- **Alternatives**: a top-level directory per archive (valid, but adds a naming rule for nothing); `tar.gz` (also accepted, but ZIP is what the spec assumes and what `specify bundle build` produces); `git archive` with export-ignore (ties the layout to `.gitattributes`, harder to test).

## R2 Tooling shape

- **Decision**: One stdlib-plus-PyYAML script `scripts/release.py` with subcommands `check`, `notes`, `build`, `verify-archive`, `bundle-catalog`. It is used by CI, by the release workflow and locally. Pure functions are tested with pytest (`tests/test_release.py`); the workflow only wires the subcommands together with `gh`.
- **Rationale**: Constitution VI prefers small scripts. PyYAML is already a dev dependency, and the release runner installs it through `uv sync`. Nothing is added to the shipped packages, so they still have no runtime dependencies. With one entry point, the tag regex, the version rule and the changelog parser exist once.
- **Alternatives**: inline shell in the workflow (untestable, duplicated between CI and release); a release action from the marketplace such as release-please or semantic-release (needs conventions the repo does not follow and would own the changelog); a Makefile (no gain over subcommands).

## R3 Tag grammar and pre-releases

- **Decision**: The workflow triggers on `preset-v*`, `extension-v*` and `bundle-v*`. `release.py check` then applies the strict pattern `^(preset|extension|bundle)-v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[0-9A-Za-z]+(\.[0-9A-Za-z]+)*)?$`. Anything else ends the run with "not a release tag" and publishes nothing. A suffix makes the release a GitHub pre-release that is not marked latest. Only the core `X.Y.Z` is compared with the manifest and used to find the changelog entry (clarification 2026-10-08).
- **Rationale**: GitHub tag filters are globs and cannot express semver, so the script enforces it, and that enforcement is testable. This covers the edge cases `v1.0.0` (no trigger) and `extension-v1.0` (trigger, but rejected before any write).
- **Alternatives**: allowing build metadata `+meta` (no use case, so rejected); requiring the full pre-release version in the manifest (rejected by the maintainer).

## R4 Changelog layout

- **Decision**: One `CHANGELOG.md` at the repo root with three level-2 sections `## Preset`, `## Extension` and `## Bundle`. Each section holds `### Unreleased` first, then `### X.Y.Z - YYYY-MM-DD` entries, newest first. Inside an entry, `#### Added|Changed|Fixed|Removed|Security|Migration` groups follow Keep a Changelog. `#### Migration` is required when the entry has a `**Breaking**` item. `release.py notes <kind> <X.Y.Z>` prints the entry body and fails if the entry is missing or empty.
- **Rationale**: Users find everything in one file, and per-package sections satisfy FR-006. The heading grammar is strict enough to parse without a Markdown library.
- **Alternatives**: one changelog per package directory (would ship inside the archive; harmless, but the bundle has no directory of its own); generating the changelog from Conventional Commits (commit scopes do not map cleanly to packages, and FR-005 wants curated notes).

## R5 Idempotent publish (FR-004)

- **Decision**: The publish step reads the state with `gh release view <tag> --json assets,body,isPrerelease`:
  - No release: create it with the notes plus a trailing marker line `<!-- release-commit: <sha> -->`, the `--prerelease` / `--latest=false` flags when needed, and the archive.
  - Release exists and its marker equals the tag's commit: upload only the assets that are missing, with `gh release upload` without `--clobber`. If none are missing, report "release exists, complete" and exit 0.
  - Release exists but the marker differs or is missing: stop and name both commits. This covers a tag re-pushed on another commit.
  - Notes and existing assets are never edited.
- **Rationale**: The marker records the source commit inside the release itself, with no external ledger, in the same spirit as the mapping ledger. `targetCommitish` is not reliable for tag-triggered releases, because it can hold a branch name.
- **Alternatives**: `--clobber` re-upload (overwrites, violates FR-004); deleting and recreating (destructive); storing state in a repo file (needs a push from CI).

## R6 Release gates (FR-003, FR-008, FR-012, FR-013)

- **Decision**: The `verify` job runs on the tagged commit and has read-only permissions:
  1. `release.py check <tag>`: tag grammar; core version equals the manifest version; changelog entry present; the manifest `repository` equals `https://github.com/$GITHUB_REPOSITORY`.
  2. `ruff check`, `ruff format --check` and `pytest`.
  3. `release.py build` followed by `release.py verify-archive`. The archive check fails on an entry outside the allowlist, on `.env`, `.scratch/`, `tests/`, `specs/` or `docs/` paths, and on any content that matches the secret patterns used by CI (token assignment) or an `http(s)://` host other than the allowed public hosts (github.com and the spec-kit and OpenProject docs).

  The `publish` job runs only after `verify` succeeds and is the only job with `contents: write`. No step has MCP configuration or OpenProject credentials.
- **Rationale**: Separating permissions keeps the write token away from test code. Gates before any write make SC-003 hold by construction.
- **Alternatives**: a single job (simpler, but the write permission covers the test run).

## R7 CI install smoke test and spec-kit pin (FR-011, constitution V)

- **Decision**: CI gets a new job `install-smoke` with a blocking matrix over the spec-kit tags `v1.1.0` (the declared minimum in both manifests) and `v1.1.2` (the current release, the pin). The pin lives in one place, a workflow `env`/matrix value, and the maintainer raises it deliberately. Each matrix leg:
  1. installs `specify-cli` from `git+https://github.com/github/spec-kit.git@<tag>`
  2. builds both archives with `release.py build`
  3. serves them with `python -m http.server --bind 127.0.0.1`
  4. creates a fresh project with `specify init --non-interactive --integration claude --ignore-agent-tools`
  5. runs `specify preset add --from http://127.0.0.1:<port>/...zip` and `specify extension add openproject --from ...` (answers the source confirmation with `y`)
  6. asserts that `specify preset list` and `specify extension list` show the versions, and that the skills exist.

  A second job `install-smoke-latest` does the same against the `main` branch with `continue-on-error: true`. `tests/test_install.py` keeps covering the `--dev` path.
- **Rationale**: spec-kit allows plain HTTP only for localhost, which makes a local server a faithful stand-in for the release URL, without publishing anything. Testing the declared minimum and the current release is what "constraints are verified in CI" means.
- **Open point for the maintainer**: constitution V says "current and previous minor". The manifests declare `>=1.1.0`, so 1.0.x is unsupported by declaration. The plan tests what is declared and does not lower the bound. Supporting 1.0.x would be a separate decision.
- **Alternatives**: an unpinned install only (today's CI; breaks PRs on upstream changes, rejected in clarify); a `file://` install (not accepted by `--from`).

## R8 Bundle: reference, not embed (FR-014, US5)

- **Finding**: A spec-kit bundle (`bundle.yml` schema 1.0, built by `specify bundle build --path <dir> --output <dir>` into `<id>-<version>.zip`) contains only `bundle.yml`, its `README.md` and optional files. It **references** presets and extensions by `id` and `version`. `specify bundle install` resolves each component through the project's preset and extension **catalog stacks** (`PresetCatalog.get_pack_info` / `download_pack`, `ExtensionCatalog.get_extension_info` / `download_extension`) and enforces the pinned version. The `source` field is not used for installation. A catalog entry may carry `sha256`, which spec-kit verifies on download.
- **Decision**:
  - A bundle definition lives in `bundle/bundle.yml` + `bundle/README.md`, with id `openproject` and components preset `openproject` and extension `openproject` at pinned versions.
  - On a `bundle-vX.Y.Z` tag, the workflow first checks the bundle gates: version vs `bundle.yml`, the `## Bundle` changelog entry, tests, and the repository field. It then checks that the releases `preset-v<pin>` and `extension-v<pin>` exist and have their archive, and downloads both archives.
  - `release.py bundle-catalog` writes `openproject-presets-catalog.json` and `openproject-extensions-catalog.json` (schema_version `1.0`). Each holds exactly one entry with the pinned version, a `download_url` pointing to the published release asset, and the `sha256` of the downloaded archive.
  - The workflow runs `specify bundle build` and publishes the bundle ZIP plus the two catalog files as assets of the bundle release.
  - Users add both catalogs with `catalog add <asset-url> --name openproject --install-allowed`, download the bundle ZIP and run `specify bundle install <zip>`.
- **Rationale**: This is how spec-kit bundles work, so "content taken from the published archives" (clarification A) is realised by `download_url` plus `sha256`, which pins the exact published bytes. Release asset URLs are immutable per tag and served over HTTPS. Catalog URL validation only requires HTTPS, and the redirect to GitHub's object host stays on HTTPS (**verify in rc run**).
- **Spec consequence**: The wording of FR-014 and US5-1 ("bundle content … taken from that package's published release archive" / "package content equals …") implies embedding. It is reworded to: the bundle pins both versions, and its catalog files point to the published archives with their checksums. The intent of the clarification is kept; nothing is rebuilt from source.
- **Alternatives**: catalog files committed in the repo and served from `raw.githubusercontent.com/.../main` (mutable and changes per release, so rejected); waiting for the community catalog listing (US4, outside this repo's control); embedding packages in the bundle (not supported by spec-kit).

## R9 Catalog submissions (FR-010, FR-015)

- **Decision**: `docs/catalog/` holds the following:
  - `preset-checklist.md` and `extension-checklist.md`: each requirement of the then-current upstream contribution guide, with evidence (file or release URL) and state (met / gap / n.a. with reason).
  - `preset-entry.json` and `extension-entry.json`: the proposed catalog entries.
  - `submission.md`: PR titles and bodies per package.
  - The bundle catalog is checked for whether it accepts community submissions; the result is recorded in the checklist.
  - The monorepo layout question (manifest not at the repository root) is listed as a gap with its options, per US4-2.
- **Rationale**: The guide changes (PUBLISHING.md), so the checklist is written at implementation time by re-reading upstream; the plan fixes only the shape. Filing is the maintainer's step.
- **Alternatives**: GitHub issue templates (not ours to define).

## R10 Documentation

- **Decision**: New `docs/RELEASING.md` (procedure for FR-009). `docs/PUBLISHING.md` is rewritten for the public `Nachklang-io` repo and points to RELEASING.md and `docs/catalog/`. `docs/TESTING.md` gets release scenarios: a local build plus localhost install, the rc run, the final-tag check and the bundle install.
- **Rationale**: PUBLISHING.md still describes the old private `ringind` setup.
