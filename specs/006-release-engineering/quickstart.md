# Quickstart: Validating Release Engineering (006)

Validation scenarios for the implementation. Behavior details are in [contracts/](contracts/) and [data-model.md](data-model.md). Outward-facing steps (pushing tags, publishing) are marked **[maintainer confirms]**.

## Prerequisites

- `uv sync`; `specify` installed (`specify version`).
- `gh auth status` succeeds, needed only for Q4–Q6.
- No OpenProject access is needed for Q1–Q6 (FR-013). Q7 uses the maintainer's test instance via MCP.

## Q1 – Unit gates (local, no network)

```bash
uv run pytest tests/test_release.py -v
uv run ruff check . && uv run ruff format --check .
```

Expected result: tests cover the following, and all pass:
- tag grammar (valid, pre-release, `v1.0.0`, `extension-v1.0`, leading zero)
- core version vs manifest
- missing or empty changelog entry
- breaking change without migration
- repository mismatch
- archive allowlist and forbidden content
- reproducible build (same sha256 twice)
- catalog JSON shape

## Q2 – Local build and localhost install (mirrors the CI smoke test)

```bash
uv run python scripts/release.py check extension-v0.1.0-rc.1 --repository Nachklang-io/speckit-openproject
uv run python scripts/release.py build preset --version 1.0.0-rc.1
uv run python scripts/release.py build extension --version 0.1.0-rc.1
uv run python scripts/release.py verify-archive dist/openproject-extension-0.1.0-rc.1.zip
(cd dist && python3 -m http.server 8765 --bind 127.0.0.1) &
specify init .scratch/rel --non-interactive --integration claude --ignore-agent-tools
cd .scratch/rel
specify preset add --from http://127.0.0.1:8765/openproject-preset-1.0.0-rc.1.zip
specify extension add openproject --from http://127.0.0.1:8765/openproject-extension-0.1.0-rc.1.zip  # asks to confirm the untrusted source: y
specify preset list; specify extension list
```

Expected result:
- `check` prints JSON with `"prerelease": true`.
- Both installs succeed, and the lists show `1.0.0` and `0.1.0` (core versions).
- `extension add` needs the extension id (`openproject`) before `--from` and asks to confirm the source (no `--yes` flag in spec-kit 1.1.x); `preset add --from` needs neither.
- `.claude/skills/speckit-taskstoissues/SKILL.md` and `speckit-openproject-*` skills exist.

## Q3 – Negative gates (local)

- Edit the extension manifest version to `0.1.1` and run `check extension-v0.1.0`. Expected: exit 1 with `version mismatch`.
- Remove the changelog entry. Expected: `missing changelog entry`.
- Put a `.env` into `extension/` and build. Expected: `verify-archive` fails. Then delete the probe file.

Revert all edits.

## Q4 – Pre-release run on GitHub (SC-007, before merge) **[maintainer confirms]**

1. Push `preset-v1.0.0-rc.1` and `extension-v0.1.0-rc.1` on the feature branch head.
2. Expected:
   - two releases, each marked pre-release and not latest, each with one archive
   - the notes equal the changelog entries plus the hidden commit marker
3. Anonymous install, on a machine or shell without a GitHub login:
   `specify preset add --from https://github.com/Nachklang-io/speckit-openproject/releases/download/preset-v1.0.0-rc.1/openproject-preset-1.0.0-rc.1.zip`, and the same for the extension.
4. Idempotency: re-run the release workflow for the same tag. Expected: `release exists, complete`, and the release is unchanged.
5. Bundle rc: push `bundle-v0.1.0-rc.1`. The pins stay `1.0.0` / `0.1.0`. The suffix rule resolves them to the releases `preset-v1.0.0-rc.1` and `extension-v0.1.0-rc.1`, as described in contracts/release-workflow.md. Then run the install path from contracts/bundle-and-catalog.md in a fresh project. Expected: both packages are listed with the pinned versions. This also confirms the catalog redirect and the sha256 check.

## Q5 – Final tags on main (SC-007, after merge) **[maintainer confirms]**

On main, after merge:
1. Push `preset-v1.0.0`, `extension-v0.1.0` and `bundle-v0.1.0`.
2. Repeat Q4 steps 2, 3 and 5 with the final URLs.
3. Record the outcome in `docs/TESTING.md`.

## Q6 – CI

The PR shows these jobs:
- `test`
- `install-smoke (v1.1.0)` and `install-smoke (v1.1.2)`, both required and green
- `install-smoke-latest`, informational

## Q7 – Behavior parity with the dev install (US2-3)

In the project from Q4 step 3, configure the MCP server and run `/speckit-openproject-discover-fields --dry-run` against the test instance. Expected: the same output as with the `--dev` install, following the S-scenario in `docs/TESTING.md`.
