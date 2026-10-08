# Release fixtures

Inputs for `tests/test_release.py` (feature 006).

- `changelog-valid.md`: all three sections; Preset 1.0.0 and 0.9.0, Extension 0.1.0 with a `**Breaking**` item and a Migration group, Bundle 0.1.0.
- `changelog-missing-entry.md`: no Extension 0.1.0 entry.
- `changelog-empty-entry.md`: Preset 1.0.0 heading with an empty body.
- `changelog-breaking-no-migration.md`: Extension 0.1.0 has a `**Breaking**` item and an empty Migration group.
- `manifests/extension-version-mismatch.yml`: version 0.1.1 (tag 0.1.0).
- `manifests/extension-repo-mismatch.yml`: repository `example/other-repo`.
