# Data Model: Release Engineering (006)

No database. The entities below live in files and in GitHub releases. Validation rules reference the spec's FRs.

## Package

| Field | Source | Rule |
|-------|--------|------|
| kind | fixed | `preset` \| `extension` \| `bundle` |
| directory | fixed | `preset/`, `extension/`, `bundle/` |
| manifest | file | `preset/preset.yml` (`preset.version`), `extension/extension.yml` (`extension.version`), `bundle/bundle.yml` (`bundle.version`) |
| id | manifest | `openproject` for all three (component refs are scoped by kind) |
| version | manifest | `X.Y.Z`, no pre-release suffix (FR-003) |
| repository | manifest | Must equal `https://github.com/<owner>/<repo>` of the publishing repository (FR-008). The bundle manifest has no repository field, so this check is skipped for it |
| tag prefix | fixed | `<kind>-v` |

## Release tag

| Field | Rule |
|-------|------|
| name | `^(preset\|extension\|bundle)-v(\d+)\.(\d+)\.(\d+)(-<prerelease>)?$`, without leading zeros (contract: release-script) |
| kind | Group 1 |
| core version | `X.Y.Z`; must equal the manifest version |
| pre-release | Suffix present → GitHub pre-release, not latest |
| commit | `git rev-parse <tag>^{commit}` |

## Release (GitHub)

| Field | Rule |
|-------|------|
| tag | One release per tag (FR-004) |
| title | The tag name |
| notes | The changelog entry body for (kind, core version), followed by the marker line `<!-- release-commit: <sha> -->`. Never edited after creation |
| assets | Package release: exactly one archive (contract: archive-layout). Bundle release: the bundle ZIP + two catalog JSON files |
| prerelease | True iff the tag has a suffix |

**State transitions** (publish job; see contracts/release-workflow.md):

```text
absent ──create(notes+marker, assets)──▶ complete
partial (marker = tag commit) ──upload missing──▶ complete
complete ──re-run──▶ complete (no-op)
any (marker ≠ tag commit or missing) ──re-run──▶ STOP (conflict, nothing written)
```

## Changelog entry

| Field | Rule |
|-------|------|
| package section | `## Preset` \| `## Extension` \| `## Bundle` (FR-006) |
| heading | `### X.Y.Z - YYYY-MM-DD`, or `### Unreleased` (exactly one per section, first) |
| groups | `#### Added\|Changed\|Fixed\|Removed\|Security\|Migration` |
| breaking | Any item starting with `**Breaking**` requires a non-empty `#### Migration` group |
| body | The text between the entry heading and the next `###`/`##` heading. It must be non-empty and is used verbatim as the release notes (FR-005) |

## Archive

| Field | Rule |
|-------|------|
| name | `openproject-<kind>-<tagversion>.zip` (tag version includes the suffix) |
| root | The manifest at the archive root |
| entries | The allowlist from contracts/archive-layout.md; sorted; fixed timestamp |
| sha256 | Computed after the build; used in the bundle catalog |

## Bundle definition (`bundle/bundle.yml`)

| Field | Rule |
|-------|------|
| bundle.id / version / name / role / description / author / license | spec-kit bundle schema 1.0. The version follows the `bundle-v` tag |
| requires.speckit_version | Equals the packages' range (`>=1.1.0`) |
| presets[] | One entry `{id: openproject, version: <preset pin>}` |
| extensions[] | One entry `{id: openproject, version: <extension pin>}` |
| rule | Each pin must have a published, complete component release before the bundle publishes (FR-014, US5-3). The component tag is `<kind>-v<pin>`; for a pre-release bundle tag with suffix `-S` it is `<kind>-v<pin>-S` |

## Generated catalog file (bundle release asset)

| Field | Rule |
|-------|------|
| schema_version | `"1.0"` |
| top-level key | `presets` or `extensions` (a mapping id → entry) |
| entry.version | The bundle pin |
| entry.download_url | `https://github.com/<repo>/releases/download/<kind>-v<pin>/<archive name>` |
| entry.sha256 | The sha256 of the downloaded published archive |
| entry.name / description / author / license / repository / requires | Copied from the package manifest in the archive |

## Catalog-submission checklist item

| Field | Rule |
|-------|------|
| requirement | Quoted or paraphrased from the upstream contribution guide, with a link |
| evidence | A repo path or release URL |
| state | `met` \| `gap` \| `n/a`, with a reason. Every item has a state (SC-006); a `gap` lists its options (US4-2) |
