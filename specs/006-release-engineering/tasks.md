---

description: "Task list for feature 006: release engineering"
---

# Tasks: Release Engineering

**Input**: Design documents from `specs/006-release-engineering/`

**Prerequisites**: plan.md, spec.md, research.md (R1–R10), data-model.md, contracts/, quickstart.md

**Tests**: Requested. Constitution IV: all release logic in `scripts/release.py` is covered by pytest (`tests/test_release.py`); GitHub-side paths are verified by the rc run (quickstart Q4/Q5) and labeled untested until then.

**Organization**: Grouped by user story. Tasks editing `scripts/release.py`, `tests/test_release.py` or `docs/TESTING.md` are sequential (same file) and not marked `[P]`. Tasks marked **(maintainer)** push tags or publish; they need the maintainer's explicit confirmation and are never claimed done without an executed run. Nothing here touches OpenProject (FR-013).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: different files, no dependency on an incomplete task
- **[Story]**: US1–US5 as numbered in `spec.md` (US1 release by tag, US2 install from URL, US3 changelog, US4 catalog submission, US5 bundle)

## Path Conventions

Monorepo: `scripts/`, `bundle/`, `.github/workflows/`, `docs/`, `tests/`, `preset/`, `extension/`. Contracts: `specs/006-release-engineering/contracts/`.

---

## Phase 1: Setup

- [ ] T001 Create `tests/fixtures/release/` with fixture changelogs (valid; missing entry; empty entry; breaking without Migration) and fixture manifests (version mismatch, repository mismatch)
- [ ] T002 [P] Create `CHANGELOG.md` per `contracts/changelog-format.md`: `## Preset`, `## Extension`, `## Bundle`, each with `### Unreleased`; move existing history into `### 1.0.0 - <date>` (Preset) and `### 0.1.0 - <date>` (Extension, Bundle) entries, with `#### Migration` where a breaking change is claimed

---

## Phase 2: Foundational (blocks all stories)

- [ ] T003 Create `scripts/release.py` skeleton: argparse subcommands `check`, `notes`, `build`, `verify-archive`, `bundle-catalog`; exit codes 0/1/2; messages prefixed `release: ` (contracts/release-script.md); stdlib + PyYAML only
- [ ] T004 Implement tag parsing in `scripts/release.py` with the exact grammar from data-model.md (`^(preset|extension|bundle)-v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(-[0-9A-Za-z]+(\.[0-9A-Za-z]+)*)?$`), returning kind, core version, suffix, prerelease flag, archive name `openproject-<kind>-<tagversion>.zip`
- [ ] T005 Implement the changelog parser in `scripts/release.py` per `contracts/changelog-format.md`: find section + `### X.Y.Z - YYYY-MM-DD` entry, return body verbatim up to next `###`/`##`; reject empty body; require non-empty `#### Migration` when an item starts with `**Breaking**`
- [ ] T006 Add `tests/test_release.py` tests for T004 and T005: valid, pre-release, `v1.0.0`, `extension-v1.0`, leading zero, missing/empty entry, breaking without migration (uses T001 fixtures)

**Checkpoint**: tag grammar and changelog parsing are tested.

---

## Phase 3: User Story 1 - Release one package by pushing a tag (P1) 🎯 MVP

**Goal**: A tag `preset-vX.Y.Z` / `extension-vX.Y.Z` yields a release with one clean archive; all stop rules hold; re-runs are idempotent.

**Independent Test**: quickstart Q1–Q3 locally; Q4 steps 1, 2, 4 on GitHub.

- [ ] T007 [US1] Implement `check` in `scripts/release.py`: core version vs manifest (`preset/preset.yml` `preset.version`, `extension/extension.yml` `extension.version`), changelog entry, `--repository` vs manifest `repository`; JSON line on success; messages exactly as in contracts/release-script.md
- [ ] T008 [US1] Implement `notes` in `scripts/release.py` (prints entry body, fails as `check` step 3)
- [ ] T009 [US1] Implement `build` in `scripts/release.py` per `contracts/archive-layout.md`: every regular file under the package dir except names starting with `.`, `__pycache__/`, `*.pyc`; sorted; timestamp 1980-01-01 00:00:00; 0644; ZIP_DEFLATED; manifest at archive root; prints path and sha256; writes only below `--out`
- [ ] T010 [US1] Implement `verify-archive` in `scripts/release.py`: manifest at root; forbidden path components (`.env`, `.scratch`, `tests`, `specs`, `docs`, `..`, leading `/`); content rules (token regex `OPENPROJECT_API_TOKEN\s*[=:]\s*['"]?[A-Za-z0-9_-]{16,}`; `http(s)` host allowlist `github.com`, `raw.githubusercontent.com`, `www.openproject.org`, `example.com` and subdomains); print every violation, exit 1
- [ ] T011 [US1] Extend `tests/test_release.py`: `check` (match, mismatch, pre-release core-only, repository mismatch), `notes`, `build` reproducible (same sha256 twice) and exact entry list for both packages, `verify-archive` (clean pass; `.env`, `tests/` path, token string, foreign host each fail)
- [ ] T012 [US1] Create `.github/workflows/release.yml` per `contracts/release-workflow.md`: triggers `preset-v*`, `extension-v*`, `bundle-v*`; job `verify` (`contents: read`: `uv sync`, `check`, ruff, pytest, `build`, `verify-archive`, `notes` + `<!-- release-commit: $GITHUB_SHA -->`, upload artifacts); job `publish` (`needs: verify`, `contents: write`) with the decision table (create / upload missing without `--clobber` / conflict stop); `--prerelease --latest=false` for suffix tags; no OpenProject secrets or MCP config
- [ ] T013 [US1] Add a local test for the publish decision in `tests/test_release.py` if the decision logic is factored into `scripts/release.py` (`publish-plan` pure function: inputs existing assets + marker + sha, output create/upload/noop/conflict); otherwise document it as untested-until-rc in `docs/TESTING.md` (decide while implementing T012; prefer the testable function)
- [ ] T014 [US1] Set `preset/preset.yml` version to `1.0.0` and `extension/extension.yml` version to `0.1.0` (FR-007); confirm both `repository` fields equal `https://github.com/Nachklang-io/speckit-openproject` (FR-008); run `uv run pytest tests/test_manifests.py`

**Checkpoint**: local scenarios Q1–Q3 pass.

---

## Phase 4: User Story 2 - Install a released package from its URL (P1)

**Goal**: CI proves archives install with `--from`; the released rc installs anonymously.

**Independent Test**: quickstart Q2, Q6; Q4 step 3.

- [ ] T015 [US2] Change `.github/workflows/ci.yml`: keep `test` job but install `specify-cli` pinned (`git+https://github.com/github/spec-kit.git@v1.1.2`, one env value); add job `install-smoke` with matrix `v1.1.0`, `v1.1.2` (blocking): install that spec-kit tag, `release.py build` both packages, `python3 -m http.server --bind 127.0.0.1` on the `dist/` dir, `specify init --non-interactive --integration claude --ignore-agent-tools`, `specify preset add --from http://127.0.0.1:<port>/…`, `specify extension add --from …`, assert `preset list` / `extension list` show `1.0.0` / `0.1.0` and the skills `speckit-taskstoissues` and `speckit-openproject-discover-fields` exist
- [ ] T016 [US2] Add job `install-smoke-latest` to `.github/workflows/ci.yml` with the same steps against spec-kit `main` and `continue-on-error: true`
- [ ] T017 [P] [US2] Add `tests/test_install_archive.py`: skip when `specify` is missing; build both archives into `tmp_path`, serve over localhost HTTP, install into a fresh `specify init` project, assert list output and skills (mirrors T015 locally)
- [ ] T018 [US2] Run quickstart Q2 locally and record the result; fix defects in T009/T010/T015

**Checkpoint**: archives install from a URL on the pinned versions.

---

## Phase 5: User Story 3 - Know what changed (P2)

**Goal**: One place for release notes; release notes equal the entry.

**Independent Test**: read `CHANGELOG.md`; compare Q4 release notes with the entry.

- [ ] T019 [US3] Add a test in `tests/test_release.py` that every released version heading in `CHANGELOG.md` parses, each package section starts with `### Unreleased`, and the current manifest versions have entries (guards SC-005 in CI)
- [ ] T020 [P] [US3] Document the changelog workflow (move Unreleased into the new entry, breaking → Migration note) in `docs/RELEASING.md` (created in T031; add the section there) — if T031 has not run, create the file with only this section

---

## Phase 6: User Story 5 - Install both packages at once (P3)

**Goal**: A bundle release pins both packages and ships catalogs pointing to the published archives.

**Independent Test**: quickstart Q4 step 5 / Q5.

- [ ] T021 [US5] Create `bundle/bundle.yml` per `contracts/bundle-and-catalog.md` (id `openproject`, version `0.1.0`, preset pin `1.0.0`, extension pin `0.1.0`, `requires.speckit_version: ">=1.1.0"`) and `bundle/README.md` with the install steps; run `specify bundle validate --path bundle` and `specify bundle build --path bundle --output dist` locally and fix keys against the pinned spec-kit
- [ ] T022 [US5] Implement `bundle-catalog` in `scripts/release.py`: resolve component tags from pins and the bundle tag suffix; read the downloaded archives; verify the archive manifest reports the pinned version; write `openproject-presets-catalog.json` and `openproject-extensions-catalog.json` (schema_version `"1.0"`, `download_url`, `sha256`, copied manifest fields; only `updated_at` varies); errors `missing release archive: <name>`, `pin mismatch`
- [ ] T023 [US5] Extend `tests/test_release.py`: bundle tag resolution (final and `-rc.1`), catalog JSON shape and sha256, pin mismatch, missing archive; validate catalog JSON loads in spec-kit's catalog parser if importable, else skip
- [ ] T024 [US5] Extend `.github/workflows/release.yml` for `bundle-v*`: resolve and verify component releases with `gh release view`, `gh release download`, `bundle-catalog`, install pinned `specify-cli`, `specify bundle build --path bundle --output dist`, `specify bundle validate`; assets = bundle ZIP + two catalog files; same publish decision table
- [ ] T025 [US5] Add a CI test (in `tests/test_release.py` or `tests/test_install_archive.py`) that installs the bundle from a local catalog served on `127.0.0.1` (preset/extension catalogs with `--install-allowed`, then `specify bundle install <zip>`); mark as the local stand-in for the GitHub path

---

## Phase 7: User Story 4 - Submit to the spec-kit catalogs (P3)

**Goal**: Complete checklists and ready-to-file submission material; filing is the maintainer's step.

**Independent Test**: every checklist item has a state (SC-006).

- [ ] T026 [US4] Re-read the current spec-kit contribution guide for the preset catalog and the extension catalog (and whether community bundles are accepted); note the date and source URLs
- [ ] T027 [P] [US4] Write `docs/catalog/preset-checklist.md`: each upstream requirement, evidence (repo path or release URL), state `met`/`gap`/`n/a` with reason; list the monorepo-layout gap with options (explain layout, or split per ADR-0001)
- [ ] T028 [P] [US4] Write `docs/catalog/extension-checklist.md` in the same form
- [ ] T029 [P] [US4] Write `docs/catalog/preset-entry.json` and `docs/catalog/extension-entry.json` (proposed catalog entries; `download_url`/`sha256` filled after the final tags) and `docs/catalog/submission.md` (PR titles and bodies per package; bundle if accepted)
- [ ] T030 [US4] Add a test in `tests/test_release.py` that every checklist item line carries a state (zero items without state, SC-006)

---

## Phase 8: Polish & Cross-Cutting

- [ ] T031 [P] Write `docs/RELEASING.md` (FR-009): bump version, move changelog, push tag **(maintainer)**, check workflow, verify install from URL, run `docs/TESTING.md` scenarios; include rc procedure and bundle procedure
- [ ] T032 [P] Rewrite `docs/PUBLISHING.md` for the public `Nachklang-io/speckit-openproject` repo (remove `ringind` private-repo steps); point to RELEASING.md and `docs/catalog/`
- [ ] T033 Add release scenarios to `docs/TESTING.md` (local build + localhost install, rc run, final-tag check, bundle install); mark GitHub-side paths untested until T034/T037
- [ ] T034 **(maintainer)** Q4: after explicit confirmation push `preset-v1.0.0-rc.1` and `extension-v0.1.0-rc.1` on the branch head; verify pre-release flag, not-latest, archive, notes + marker; anonymous install from the URL; re-run for idempotency; push `bundle-v0.1.0-rc.1` and run the bundle install path; record executed results in `docs/TESTING.md`
- [ ] T035 Run `uv run pytest`, `uv run ruff check . && uv run ruff format --check .`, `scripts/dev-install.sh` with `specify preset list` / `specify extension list`; run the `spec-conformance-reviewer` subagent on the diff (the `openproject-api-reviewer` is not applicable: no OpenProject interaction changed, say so in the PR)
- [ ] T036 Update README links/status and the roadmap (`docs/ROADMAP.md`: M1/M2 release state, M4 prepared); open the PR (Conventional Commits, one feature = one PR)
- [ ] T037 **(maintainer)** Q5: after merge, push `preset-v1.0.0`, `extension-v0.1.0`, `bundle-v0.1.0` on main; repeat the anonymous installs and bundle install; record the outcome in `docs/TESTING.md` (SC-007)

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → US1 (Phase 3) → US2 (Phase 4); US3 (Phase 5) can start after Phase 2 and runs alongside US1; US5 (Phase 6) needs `build` (T009) and the release workflow (T012); US4 (Phase 7) is independent and can run in parallel with Phases 3–6 (documentation only), but its entries need final tags for `sha256`.
- Phase 8: T031–T033 after the stories; T034 needs T012, T015, T024; T035 before the PR (T036); T037 only after merge.
- Same-file tasks (`scripts/release.py`, `tests/test_release.py`, `docs/TESTING.md`, `release.yml`, `ci.yml`) are sequential in listed order.

## Parallel Examples

- T002 with T001.
- After Phase 2: T015–T017 (ci/test files) with T019 and with T026–T029 (docs).
- T027, T028, T029 together; T031 and T032 together.

## Implementation Strategy

- **MVP**: Phases 1–4 (US1 + US2): tag → clean archive → installs from a URL, with CI smoke tests.
- Then US3 (changelog guard), US5 (bundle), US4 (submission material), polish.
- No code before `/speckit-analyze` is clean. Outward-facing steps (T034, T037) happen only on the maintainer's explicit confirmation.
