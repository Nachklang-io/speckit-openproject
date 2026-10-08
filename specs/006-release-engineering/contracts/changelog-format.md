# Contract: `CHANGELOG.md`

```markdown
# Changelog

All notable changes per package. Format based on Keep a Changelog; versions follow SemVer.

## Preset

### Unreleased

### 1.0.0 - 2026-10-DD

#### Added
- ...

## Extension

### Unreleased

### 0.1.0 - 2026-10-DD

#### Added
- ...

## Bundle

### Unreleased

### 0.1.0 - 2026-10-DD

#### Added
- First bundle: preset 1.0.0 + extension 0.1.0.
```

## Rules

- There are exactly three `##` package sections, in the order Preset, Extension, Bundle.
- Each section starts with `### Unreleased`, which may be empty. After it come version entries, newest first.
- A version heading has exactly the form `### X.Y.Z - YYYY-MM-DD`. A pre-release never gets its own heading; it uses the `X.Y.Z` entry (clarification 2026-10-08).
- The allowed groups are `#### Added`, `#### Changed`, `#### Fixed`, `#### Removed`, `#### Security` and `#### Migration`.
- An entry with a list item that starts with `**Breaking**` must contain a non-empty `#### Migration` group (FR-006, constitution: breaking changes).
- Release notes are the entry body, verbatim, from the line after the heading up to the next `###` or `##` (FR-005).
- To release, the maintainer moves the items from `### Unreleased` into the new version heading (US3-3).
