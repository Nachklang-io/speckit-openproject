# Implementation Plan: Release Engineering

**Branch**: `006-release-engineering` | **Date**: 2026-10-08 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-release-engineering/spec.md`

## Summary

Release the preset, the extension and a bundle of both from this monorepo by pushing tags `preset-vX.Y.Z`, `extension-vX.Y.Z` or `bundle-vX.Y.Z`.

One script, `scripts/release.py`, holds all release logic:
- tag grammar
- version vs manifest check (core version only for pre-releases)
- changelog extraction
- reproducible ZIP build from the package directory
- archive content check
- bundle catalog generation

A GitHub Actions workflow `release.yml` runs the gates in a read-only `verify` job, then publishes idempotently in a `publish` job:
- creates the release if it is missing
- uploads only missing assets when the release's commit marker matches
- otherwise stops; it never overwrites anything

CI gets an install smoke test against pinned spec-kit tags (blocking) and spec-kit `main` (non-blocking). The smoke test serves the built archives on `127.0.0.1` and installs them with `--from`.

The bundle references both packages by pinned version. Its release ships two one-entry catalog files whose `download_url` and `sha256` point to the published package archives, because spec-kit bundles resolve components through catalogs (research R8).

The feature also delivers:
- `CHANGELOG.md`
- `docs/RELEASING.md`
- a rewritten `docs/PUBLISHING.md`
- `docs/catalog/` with the submission checklists, entries and PR text

## Technical Context

**Language/Version**: Python ≥ 3.11 (tooling only), GitHub Actions YAML, Markdown

**Primary Dependencies**:
- PyYAML (existing dev dependency) and the stdlib (`zipfile`, `hashlib`, `re`, `json`)
- `gh` CLI (preinstalled on GitHub runners)
- `specify-cli` pinned to `v1.1.0` and `v1.1.2` in CI

**Storage**: Files only: `CHANGELOG.md`, `bundle/bundle.yml`, and the release assets on GitHub

**Testing**:
- pytest (`tests/test_release.py`: tag grammar, version rule, changelog parser, archive allowlist and content scan, reproducible build, catalog JSON)
- the existing `tests/test_install.py`
- the CI smoke job; the rc run on GitHub (SC-007)

**Target Platform**: GitHub Actions `ubuntu-latest`; local macOS/Linux for maintainers

**Project Type**: Release tooling for two spec-kit packages (build scripts + CI workflows + docs)

**Performance Goals**: n/a. One release run should finish in a few minutes; there is no hard target.

**Constraints**:
- no OpenProject access (FR-013)
- no secrets in archives or notes (FR-012)
- write permission only in the publish job
- idempotent re-runs (FR-004, constitution III)
- packages keep zero runtime dependencies

**Scale/Scope**: 3 tag series, 3 archive kinds, about 2–4 releases per month

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment | Status |
|-----------|------------|--------|
| I. Spec-driven | Spec clarified (8 decisions); this plan, then tasks and analyze before code. | Pass |
| II. MCP-only OpenProject access | No release step touches OpenProject; workflows carry no MCP config or OpenProject secret (FR-013). | Pass |
| III. Idempotent, safe | The publish step is create-or-fill-missing with a commit marker; it never overwrites or deletes (R5). There is no `--dry-run` flag: the `verify` job is the plan step, and `release.py` subcommands are read-only except `build`, which writes to `dist/` only. | Pass |
| IV. Test-first | All logic sits in `scripts/release.py` with pytest coverage; release scenarios are added to `docs/TESTING.md`; untested paths (e.g. the bundle install via the catalog redirect) stay labeled until the rc run. | Pass |
| V. Compatibility | Blocking smoke test against the declared minimum `v1.1.0` and the current `v1.1.2`, plus non-blocking `main`. **Note**: "previous minor" (1.0.x) is excluded by the manifests' `>=1.1.0`; flagged to the maintainer, not changed here. Shipped config keys untouched. | Pass (with note) |
| VI. Simplicity | One script, two workflows, plain Markdown changelog; no release framework. | Pass |
| Tech constraints | Independent tags as the constitution prescribes; `bundle-v*` is an additional series (spec clarification). MIT/English. No runtime dependencies. No secrets. | Pass |
| Workflow | CI gains the install smoke test the constitution already requires. | Pass |

**Post-design re-check (after Phase 1)**: unchanged. The design adds no principle conflict. The bundle catalog files are generated release assets, not a new persistent store.

## Project Structure

### Documentation (this feature)

```text
specs/006-release-engineering/
├── plan.md              # This file
├── research.md          # Phase 0: decisions R1–R10
├── data-model.md        # Phase 1: entities and validation rules
├── quickstart.md        # Phase 1: validation scenarios
├── contracts/
│   ├── release-script.md     # scripts/release.py subcommands, exit codes, messages
│   ├── release-workflow.md   # tag triggers, jobs, gates, publish decision table
│   ├── archive-layout.md     # archive names, allowlist, forbidden content
│   ├── changelog-format.md   # CHANGELOG.md grammar
│   └── bundle-and-catalog.md # bundle.yml and generated catalog JSON
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
scripts/
├── dev-install.sh            # existing
└── release.py                # NEW: check | notes | build | verify-archive | bundle-catalog

bundle/                       # NEW: bundle definition for `specify bundle build`
├── bundle.yml
└── README.md

.github/workflows/
├── ci.yml                    # CHANGED: pinned spec-kit, install-smoke matrix, install-smoke-latest
└── release.yml               # NEW: verify → publish on preset-v*/extension-v*/bundle-v*

CHANGELOG.md                  # NEW: ## Preset / ## Extension / ## Bundle

preset/preset.yml             # CHANGED: version 1.0.0 (first final tag after merge)
extension/extension.yml       # CHANGED: version 0.1.0

docs/
├── RELEASING.md              # NEW: maintainer procedure (FR-009)
├── PUBLISHING.md             # CHANGED: public Nachklang-io flow, points to RELEASING/catalog
├── TESTING.md                # CHANGED: release scenarios
└── catalog/                  # NEW (FR-010, FR-015)
    ├── preset-checklist.md
    ├── extension-checklist.md
    ├── preset-entry.json
    ├── extension-entry.json
    └── submission.md

tests/
├── test_release.py           # NEW
└── fixtures/release/         # NEW: changelog and manifest fixtures, bad-archive cases
```

**Structure Decision**: The existing monorepo layout (ADR-0001) is extended. Release logic goes into one script next to `dev-install.sh`. The bundle definition gets its own top-level directory, because `specify bundle build --path` needs a directory with `bundle.yml` and `README.md`. Catalog submission material lives under `docs/catalog/`, since it is documentation for the maintainer and is not shipped.

## Spec adjustment from research

FR-014 and US5 scenario 1 were worded as if the bundle embedded package content. spec-kit bundles only reference components and resolve them through catalogs (R8). The spec is reworded to say that the bundle pins both versions and that its published catalog files point to the published archives with their checksums. The clarification "from the published archives, no rebuild" is kept.

## Complexity Tracking

No violations to justify.
