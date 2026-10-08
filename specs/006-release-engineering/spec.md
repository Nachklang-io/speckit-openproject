# Feature Specification: Release Engineering

**Feature Branch**: `006-release-engineering`

**Created**: 2026-10-08

**Status**: Draft

## Clarifications

### Session 2026-10-08

- Q: Which versions are tagged first? → A: preset `1.0.0`, extension `0.1.0` (roadmap M1/M2).
- Q: Catalog submission: checklists only, or also the pull requests against github/spec-kit? → A: Prepare the submissions in this repo, ready to file; the maintainer files them.
- Q: Is the bundle in scope? → A: Yes.
- Q: What does a re-run for a tag that already has a release do? → A: Complete release: nothing. Missing archive: upload it, only if the tag still points to the same commit; never overwrite.
- Q: Against which spec-kit version does the CI install smoke test run? → A: A pinned version (blocking) plus a non-blocking run against the latest spec-kit.
- Q: Is the bundle built from the published package archives or rebuilt from source at the bundle tag? → A: From the published archives of the named versions; no rebuild from source.
- Q: Does feature 006 include the first real releases? → A: Before merge, a real run with pre-release tags (for example `extension-v0.1.0-rc.1`) including the install from the URL; after merge, the maintainer sets the final tags on main and the install is verified again.
- Q: How does the tag-vs-manifest version check treat a pre-release tag? → A: Only the core `X.Y.Z` is compared with the manifest; the release notes come from the changelog entry for `X.Y.Z`.

**Input**: User description: "docs/briefs/006-release-engineering.md" — independent tags `preset-v*` / `extension-v*`, a GitHub release workflow producing archives, a changelog, catalog-submission checklists for the preset and the extension, an optional bundle via `specify bundle build`. Acceptance: a tagged release installs via `specify preset add` / `specify extension add` from the release URL.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Release one package by pushing a tag (Priority: P1)

The maintainer decides that the extension is ready for a release. They set the version in the extension manifest, add a changelog entry and push a tag `extension-vX.Y.Z`. Without further manual steps, a release appears on the repository's releases page with an installable archive of the extension only. The preset is released the same way with a `preset-vX.Y.Z` tag, independently of the extension.

**Why this priority**: Without a release artifact nobody can install the packages outside a clone of this repo; every other story depends on it.

**Independent Test**: Push a tag for one package (or run the release workflow in a test mode on a tag in a fork or a pre-release). One release exists with one archive that contains exactly that package's files (manifest, commands, README, LICENSE, templates) and nothing from the other package, the tests or the docs.

**Acceptance Scenarios**:

1. **Given** the manifest version of the extension is `X.Y.Z` and a changelog entry for `X.Y.Z` exists, **When** the tag `extension-vX.Y.Z` is pushed, **Then** a release named after the tag is created with one archive of the extension and the changelog entry as release notes.
2. **Given** a tag `preset-vA.B.C`, **When** it is pushed, **Then** only the preset is packaged and released; the extension is untouched.
3. **Given** the tag version and the manifest version differ, **When** the tag is pushed, **Then** the release fails with a message naming both versions, and no release or archive is published.
4. **Given** there is no changelog entry for the tagged version, **When** the tag is pushed, **Then** the release fails with a message naming the missing entry, and nothing is published.
5. **Given** the test suite or the lint fails on the tagged commit, **When** the tag is pushed, **Then** no release is published.
6. **Given** a release for a tag already exists, **When** the workflow runs again for the same tag, **Then** no second release and no duplicate archive is created (re-runs are idempotent); a missing archive is uploaded if the tag still points to the same commit.

---

### User Story 2 - Install a released package from its URL (Priority: P1)

A user of spec-kit, outside this repo, installs the preset and the extension from the release archives with `specify preset add --from <url>` and `specify extension add --from <url>`, and the commands are available in their project.

**Why this priority**: This is the acceptance criterion of the brief and the point of releasing at all.

**Independent Test**: In a fresh spec-kit project on a machine without a clone of this repo, install both packages from their release URLs; `specify preset list` and `specify extension list` show them with the released versions, and the commands are present in skills mode and command mode.

**Acceptance Scenarios**:

1. **Given** a published preset release, **When** a user runs `specify preset add --from <release archive URL>` in a fresh spec-kit project, **Then** the preset installs without errors and `specify preset list` shows the released version.
2. **Given** a published extension release, **When** a user runs `specify extension add --from <release archive URL>`, **Then** the extension installs without errors, `specify extension list` shows the released version, and all five commands are available.
3. **Given** the installed released packages, **When** the user runs a read-only command (for example `discover-fields --dry-run`) against a test instance, **Then** it behaves the same as the development install.

---

### User Story 3 - Know what changed (Priority: P2)

A user who upgrades wants to know what changed between versions, and the maintainer wants the release notes to come from one place.

**Why this priority**: Required for honest releases (constitution VI) and for migration notes on breaking changes (constitution V), but a release can exist without it for a first version.

**Independent Test**: Read the changelog: each released version of each package has an entry with date and the changes grouped by kind; the release notes on the releases page equal the entry.

**Acceptance Scenarios**:

1. **Given** the changelog, **When** a version of either package is released, **Then** it has its own entry for that package, separate from the other package's entries.
2. **Given** a version contains a breaking change, **When** its entry is written, **Then** the entry contains a migration note (constitution: breaking changes need a major bump and migration notes).
3. **Given** unreleased changes exist, **When** the maintainer prepares a release, **Then** they move the "Unreleased" items of that package into the new version entry.

---

### User Story 4 - Submit to the spec-kit catalogs (Priority: P3)

The maintainer wants the preset and the extension listed in the community catalogs of spec-kit so users can install them by id.

**Why this priority**: Milestone M4; valuable for discovery, but it depends on public releases and on the catalog maintainers' process, which this repo does not control.

**Independent Test**: For each package, a checklist exists that lists every requirement of the current spec-kit contribution guide for that catalog type, each item ticked or explained, and the submission text is ready to file.

**Acceptance Scenarios**:

1. **Given** a released package, **When** the maintainer opens its catalog-submission checklist, **Then** every item names the requirement, where it is met in this repo (file or release URL), and its state.
2. **Given** the catalog requires a field this repo cannot meet in its monorepo layout (for example a manifest at the repository root), **When** the checklist is prepared, **Then** the gap is listed with the options (explain the layout, or split per ADR-0001) instead of being hidden.
3. **Given** the checklist for a package is complete, **When** the maintainer wants to submit, **Then** the submission (catalog entry and pull request text for github/spec-kit) is prepared in this repo, ready to file; filing it is the maintainer's step and not part of this feature.

---

### User Story 5 - Install both packages at once (Priority: P3)

A user wants to install preset and extension together in one step.

**Why this priority**: Convenience; both packages already install separately.

**Independent Test**: Build the bundle, install it into a fresh project; both packages are listed.

**Acceptance Scenarios**:

1. **Given** released versions of the preset and the extension, **When** the tag `bundle-vX.Y.Z` is pushed, **Then** a release with one bundle archive (built with `specify bundle build`) is published that references exactly those package versions, and its package content equals the content of their published release archives.
2. **Given** the bundle archive, **When** a user installs it into a fresh spec-kit project, **Then** `specify preset list` and `specify extension list` show both packages with the versions the bundle names.
3. **Given** the bundle names a package version that has no release, **When** the bundle tag is pushed, **Then** nothing is published and the message names the missing release.

---

### Edge Cases

- A tag that does not match `preset-vX.Y.Z` or `extension-vX.Y.Z` (for example `v1.0.0` or `extension-v1.0`) does not trigger a release.
- A pre-release version (for example `extension-v0.2.0-rc.1`) is published as a pre-release, not as the latest release; the manifest carries the core version (`0.2.0`), so an installed pre-release reports the core version.
- Both tags are pushed on the same commit: two independent releases, each with only its own package.
- A tag is deleted and re-pushed on a different commit: the existing release is not silently overwritten; the run stops and names the conflict.
- The archive must not contain secrets, `.env`, `.scratch/`, private instance URLs, tests, specs or docs outside the package directory.
- The extension requires a spec-kit version range; installing into an unsupported spec-kit version gives spec-kit's own error, not a broken install.
- A manifest's repository field points to a different repository than the one the release is published from (the repository moved from `ringind` to `Nachklang-io` on 2026-10-08); the release stops and names both.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST release the preset and the extension independently, triggered only by tags of the form `preset-vX.Y.Z` and `extension-vX.Y.Z` (semantic versions, optional pre-release suffix).
- **FR-002**: Each release MUST contain one archive per package in a format accepted by `specify preset add --from` / `specify extension add --from`, built only from that package's directory.
- **FR-003**: The release MUST stop without publishing anything when the tag version differs from the version in the package manifest, when the changelog has no entry for that package and version, or when tests or lint fail on the tagged commit. For a pre-release tag (`X.Y.Z-<suffix>`), only the core version `X.Y.Z` is compared with the manifest, and the changelog entry for `X.Y.Z` is required and used as release notes.
- **FR-004**: Re-running the release for an existing tag MUST NOT create a second release or a duplicate archive. If the existing release is complete, the run changes nothing and reports that the release exists. If its archive is missing, the run uploads it only when the tag still points to the commit the release was created from. Existing archives and release notes are never overwritten.
- **FR-005**: The release notes MUST be the changelog entry for that package and version.
- **FR-006**: The repository MUST have a changelog with separate entries per package and version, an "Unreleased" section per package, and a migration note for every breaking change.
- **FR-007**: The first released versions MUST be preset `1.0.0` and extension `0.1.0` (roadmap milestones M1 and M2); the manifests are set to these versions before the first tags. Final release tags are set on main after the feature is merged, never on the feature branch.
- **FR-014**: The repository MUST release a bundle of both packages (`specify bundle build`) triggered by tags `bundle-vX.Y.Z`, with the same stop rules as FR-003 (version, changelog entry, tests) plus a check that every package version the bundle names has a release. The bundle content for each package MUST be taken from that package's published release archive, not rebuilt from the source tree at the bundle tag.
- **FR-015**: For each package (and the bundle, if the catalog accepts bundles), the catalog submission for github/spec-kit MUST be prepared in this repo (catalog entry and pull request text); the feature does not file it.
- **FR-008**: The `repository` field of both manifests MUST point to the repository the releases are published from.
- **FR-009**: A documented release procedure MUST list the maintainer's steps (bump version, write changelog, tag, verify install from URL) and the verification to run before announcing a release, including the scenarios in `docs/TESTING.md` against the test instance.
- **FR-010**: For each package, a catalog-submission checklist MUST map the current spec-kit contribution requirements to this repo, with state and evidence per item.
- **FR-011**: CI MUST verify on every pull request that each package can be built into an archive and that the archive installs into a fresh spec-kit project (install smoke test, constitution development workflow). The test that blocks a pull request runs against a pinned spec-kit version, which the maintainer raises deliberately; a second, non-blocking run against the latest spec-kit reports breaking changes early.
- **FR-012**: Archives and release notes MUST NOT contain secrets, `.env` content, private instance URLs or files outside the package directory except shared files the package needs (for example the LICENSE).
- **FR-013**: No release step MUST access OpenProject; releasing is independent of any OpenProject instance.

### Key Entities

- **Package**: preset or extension; has a manifest with id and version, a directory, and its own tag prefix.
- **Release**: one tag of one package; has a version, an archive and release notes.
- **Changelog entry**: one package, one version, date, grouped changes, optional migration note.
- **Catalog-submission checklist**: one per package; items with requirement, evidence and state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: From pushing a tag to a downloadable archive takes no manual step besides the tag push.
- **SC-002**: A user installs each released package from its URL into a fresh spec-kit project with one command each, without errors, on the first attempt.
- **SC-003**: 100% of release attempts with a version mismatch, a missing changelog entry or failing tests publish nothing.
- **SC-004**: Each released archive contains only files of its package; a check of the archive contents finds zero files from tests, specs, docs or `.scratch/`.
- **SC-005**: Every released version of each package has a changelog entry, and the release notes match it.
- **SC-006**: Each catalog-submission checklist has zero items without a state.
- **SC-007**: Before the pull request is merged, one pre-release per package (tag with a pre-release suffix, pushed after the maintainer's confirmation) has been published by the workflow and installed anonymously from its URL into a fresh spec-kit project. After the merge, the final tags `preset-v1.0.0` and `extension-v0.1.0` are set on main by the maintainer and the same install check passes.

## Assumptions

- Releases are published on the public GitHub repository `Nachklang-io/speckit-openproject` (the monorepo, ADR-0001); no split into per-package repositories in this feature. Both manifests already point there (changed 2026-10-08).
- The release archives are ZIP files, which both `specify preset add --from` and `specify extension add --from` accept.
- The changelog lives in one file at the repository root with per-package sections (or one file per package); the plan decides, the requirement is per-package entries.
- The existing CI workflow is extended; releasing runs on GitHub Actions in this repository.
- The spec-kit contribution guide for catalogs is re-read at implementation time because the process changes (`docs/PUBLISHING.md`).
- The repository is public, so the install from the release URL (User Story 2) is verified anonymously, without GitHub authentication.
- The bundle has its own tag series `bundle-vX.Y.Z`, independent of the package tags, because one bundle version pins one version of each package.
- Tagging, publishing a release and filing catalog submissions are outward-facing and done by the maintainer or only after the maintainer's explicit confirmation.
