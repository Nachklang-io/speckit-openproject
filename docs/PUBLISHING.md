# Publishing

The repository is public at https://github.com/Nachklang-io/speckit-openproject. The manifests point there; `scripts/release.py check` refuses a preset or extension tag whose manifest `repository` does not match the publishing repository.

## Where things are

| Topic | Document |
|-------|----------|
| Releasing a package or the bundle (versions, changelog, tags, workflow, re-runs) | `docs/RELEASING.md` |
| Catalog checklists, proposed catalog entries, submission text | `docs/catalog/` |
| Release test scenarios | `docs/TESTING.md`, "Scenarios for feature 006" |
| Release workflow | `.github/workflows/release.yml` |

## Rules that stay in force

- No secrets in the repository or its history: no tokens, no private instance URLs, no `.env` content. The only secret the release workflow uses is the built-in `GITHUB_TOKEN`.
- Every package keeps its `LICENSE` (MIT) and a complete `README.md`. `scripts/release.py verify-archive` checks each archive for a root manifest, unsafe or hidden paths, `.env` files, token patterns and URL hosts outside the allowlist.
- Tags are pushed by the maintainer. Catalog submissions to `github/spec-kit` are filed by the maintainer, after re-reading the current upstream rules (`docs/catalog/submission.md`).
- Releasing never touches OpenProject.
