# Releasing

How the maintainer releases the preset, the extension and the bundle. The release workflow (`.github/workflows/release.yml`) does the building and publishing; the steps here are what a person decides and checks. Releasing never touches OpenProject (FR-013).

## Tags and versions

| Package | Tag | Manifest | Release asset |
|---------|-----|----------|---------------|
| Preset | `preset-vX.Y.Z` | `preset/preset.yml` `preset.version` | `openproject-preset-X.Y.Z.zip` |
| Extension | `extension-vX.Y.Z` | `extension/extension.yml` `extension.version` | `openproject-extension-X.Y.Z.zip` |
| Bundle | `bundle-vX.Y.Z` | `bundle/bundle.yml` `bundle.version` | `openproject-X.Y.Z.zip` plus `openproject-presets-catalog.json` and `openproject-extensions-catalog.json` |

- Each package is versioned on its own (SemVer). A tag releases exactly one package.
- A pre-release tag adds `-rc.N` (or another suffix) to the version: `preset-v1.0.0-rc.1`. The manifest keeps `1.0.0`; the workflow compares the core version only. The archive name carries the full tag version (`openproject-preset-1.0.0-rc.1.zip`); the bundle archive keeps the core version.
- Pre-releases are published as "pre-release" and never become "latest".
- Bump the bundle version whenever its pins in `bundle/bundle.yml` change.

## Changelog

`CHANGELOG.md` has three sections: `## Preset`, `## Extension`, `## Bundle` (`specs/006-release-engineering/contracts/changelog-format.md`).

- During development, add items under `### Unreleased` of the package they change.
- Allowed groups: `#### Added`, `#### Changed`, `#### Fixed`, `#### Removed`, `#### Security`, `#### Migration`.
- To release, move the items from `### Unreleased` into a new entry `### X.Y.Z - YYYY-MM-DD` directly below it. Leave `### Unreleased` in place, empty.
- Date the entry with the day the final tag is pushed. If the entry was written earlier, update the date in the release-prep commit.
- Every list item that starts with `**Breaking**` needs a non-empty `#### Migration` group in the same entry. The workflow refuses the tag otherwise. A breaking change also means a major version bump (constitution); renaming or removing a shipped config key is always breaking.
- A pre-release has no entry of its own. `preset-v1.0.0-rc.1` uses the `1.0.0` entry, so write it before the first rc.
- The entry body becomes the release notes verbatim. Once a release exists, its notes are never edited; fix mistakes in the next version.

## Release a package

1. **Prepare** on a branch (or in the feature PR):
   - Set the version in the manifest.
   - Move the changelog items into the new entry (see above).
   - Check locally:

     ```bash
     uv run python scripts/release.py check preset-v1.0.0 --repository Nachklang-io/speckit-openproject
     uv run python scripts/release.py notes preset 1.0.0
     uv run pytest && uv run ruff check . && uv run ruff format --check .
     ```

   - Merge to `main` once CI is green (`test`, `install-smoke (v1.1.0)`, `install-smoke (v1.1.2)`).
2. **Pre-release (recommended for a new major or minor version)**: push an rc tag on the commit to release and run the checks in step 4 against its URL:

   ```bash
   git tag preset-v1.0.0-rc.1 <commit>
   git push origin preset-v1.0.0-rc.1
   ```

3. **Tag** the release on `main` **(maintainer)**:

   ```bash
   git switch main && git pull
   git tag preset-v1.0.0
   git push origin preset-v1.0.0
   ```

   Push one tag at a time and wait for its run, so a failure is easy to attribute.
4. **Check the workflow run** in the Actions tab: `verify` and `publish` are green, and the run log ends with `created preset-v1.0.0`. Then check the release page:
   - exactly one asset with the expected name;
   - the notes equal the changelog entry, followed by the hidden `<!-- release-commit: <sha> -->` marker;
   - a pre-release is marked "Pre-release", a final release is "Latest" (if it is the newest).
5. **Verify the install from the URL** in a fresh project, without a GitHub login:

   ```bash
   specify init release-check --ai claude --script sh && cd release-check
   specify preset add --from https://github.com/Nachklang-io/speckit-openproject/releases/download/preset-v1.0.0/openproject-preset-1.0.0.zip
   specify extension add openproject --from https://github.com/Nachklang-io/speckit-openproject/releases/download/extension-v0.1.0/openproject-extension-0.1.0.zip   # answer y
   specify preset list && specify extension list
   ```

   Expected: both lists show the released versions; `speckit-taskstoissues` carries `preset:openproject`; the five `speckit-openproject-*` skills exist.
6. **Run the scenarios** in `docs/TESTING.md` against the test instance before announcing the release: the scenarios of every command whose prompt changed in this release, `--dry-run` first, and the parity scenario S27 (installed from the release URL vs `--dev`). Record what was actually run in the run log.
7. **Announce** and, for a first release or a changed catalog entry, file the catalog submission (below).

## Release the bundle

The bundle pins exact package versions and references their published archives; it never rebuilds them.

1. Release the pinned preset and extension versions first (above). The workflow fails with `missing release: <tag>` otherwise.
2. Set `bundle.version` and the pins in `bundle/bundle.yml`, write the `## Bundle` changelog entry, merge.
3. Push `bundle-vX.Y.Z` **(maintainer)**. A pre-release bundle tag `bundle-vX.Y.Z-rc.N` resolves its pins to the component tags with the same suffix (`preset-v1.0.0-rc.1`, `extension-v0.1.0-rc.1`); those must exist.
4. Check the release: the bundle ZIP and the two catalog files.
5. Verify the install path in a fresh project (`bundle/README.md`):

   ```bash
   BASE=https://github.com/Nachklang-io/speckit-openproject/releases/download/bundle-v0.1.0
   specify preset catalog add $BASE/openproject-presets-catalog.json --name openproject --install-allowed
   specify extension catalog add $BASE/openproject-extensions-catalog.json --name openproject --install-allowed
   curl -LO $BASE/openproject-0.1.0.zip
   specify bundle install ./openproject-0.1.0.zip
   specify preset list && specify extension list
   ```

   Expected: both packages with the pinned versions; spec-kit verified the `sha256` of each archive.

## Re-runs and failures

The workflow is safe to re-run. It decides from the existing release and the commit marker in its notes:

| Situation | Outcome |
|-----------|---------|
| No release for the tag | `created <tag>` |
| Release exists from the same commit, assets missing (an earlier run failed mid-upload) | `completed <tag>: uploaded <names>`; nothing else changes |
| Release exists from the same commit, complete | `release exists, complete: <tag>`; nothing changes |
| Release exists, but the tag now points to another commit (or the notes have no marker) | `conflict: release <tag> was created from <old>, tag now points to <new>`; nothing is written |
| A gate fails in `verify` (tag grammar, version mismatch, missing changelog entry, breaking change without migration, repository mismatch, tests, archive check, missing component release) | nothing is published; the message names the gate |

- To retry, use "Re-run jobs" on the failed run, or delete the local and remote tag and push it again **on the same commit**.
- A gate failure: fix it on `main`, delete the tag (`git push origin :refs/tags/<tag>`, `git tag -d <tag>`) and tag the fixed commit. This is only possible while no release exists for the tag.
- A conflict: a published version is never moved to another commit. Release the fix as the next version (`1.0.1`). Deleting a published release and its tag is a last resort for a release nobody can have installed yet; decide that by hand.

## Catalog submission

The checklists, proposed catalog entries and the prepared submission text live in `docs/catalog/`. After a final release:

1. Fill the `sha256` of each published archive into `docs/catalog/*-entry.json` (`docs/catalog/submission.md`, "Before filing").
2. Re-read the upstream rules linked in the checklists and update the checklists if they changed.
3. File the submissions in `github/spec-kit` **(maintainer)**: preset and extension first, the bundle after both are listed.
4. For later versions, update the catalog entry in the same way.
