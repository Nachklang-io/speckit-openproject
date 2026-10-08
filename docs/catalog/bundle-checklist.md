# Catalog checklist: bundle `openproject`

Upstream rules read on 2026-10-08 (research R9, T027):

- [T] https://github.com/github/spec-kit/blob/main/.github/ISSUE_TEMPLATE/bundle_submission.yml
- Community catalog: https://github.com/github/spec-kit/blob/main/bundles/catalog.community.json (no separate publishing guide)

Every item has a state: `met`, `gap` (with options) or `n/a` (with reason). `tests/test_release.py` checks this (SC-006). File the bundle only after the preset and the extension are accepted, because its components must resolve.

## Requirements

| # | Requirement (source) | Evidence | State | Reason / options |
|---|----------------------|----------|-------|------------------|
| 1 | Valid `bundle.yml` manifest included [T] | `bundle/bundle.yml`; CI step `specify bundle validate --offline --path bundle` | met | |
| 2 | Bundle id matches the manifest and follows naming conventions [T] | `bundle.id: openproject`, archive `openproject-0.1.0.zip` | met | |
| 3 | Every extension and preset reference is pinned [T] | preset `1.0.0`, extension `0.1.0` in `bundle/bundle.yml` | met | |
| 4 | README explains role, installed components and installation steps [T] | `bundle/README.md` | met | |
| 5 | LICENSE file included [T] | `preset/LICENSE`, `extension/LICENSE` inside the component archives | gap | The bundle directory has no LICENSE of its own. Options: (a) add `bundle/LICENSE` (MIT, same text) before filing (recommended); (b) point to the repository license in the submission |
| 6 | Validation succeeds with `specify bundle validate --path <dir>` [T] | CI `install-smoke`; release workflow step | met | Run with `--offline`; the online check needs the components in a catalog |
| 7 | Build succeeds with `specify bundle build` and produces the submitted artifact [T] | S28; release workflow builds the asset that is published | met | |
| 8 | Bundle installs from the built artifact [T] | S28 (`tests/test_install_archive.py::test_bundle_installs_from_catalogs`) | met | Local, against catalogs served on `127.0.0.1` |
| 9 | The submitted distribution path was tested end to end, including install by bundle id from an install-allowed catalog when an entry is proposed [T] | — | gap | Only the install from the ZIP was tested. Options: (a) after T038 and acceptance of preset and extension, test `specify bundle install openproject` from a catalog that holds `bundle-entry` (to be written then), and record it in `docs/TESTING.md` (chosen); (b) submit without a catalog entry, artifact only |
| 10 | Installation tested in a clean spec-kit project [T] | S28 uses a fresh `specify init` project | met | |
| 11 | Required component catalogs are documented and included in testing, or none are needed [T] | `bundle/README.md` (two one-entry catalogs from the bundle release); S28 adds both | met | Once preset and extension are in the community catalogs, these extra catalogs become unnecessary; update `bundle/README.md` then |
| 12 | GitHub release created with a version tag [T] | Release `bundle-v0.1.0` | gap | Not published yet. Options: (a) the maintainer pushes `bundle-v0.1.0` after the component tags (T038) (chosen) |
| 13 | Documentation is complete and accurate [T] | `bundle/README.md` | met | |
