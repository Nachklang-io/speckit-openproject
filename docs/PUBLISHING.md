# Publishing

## Create the private GitHub repo and push
```bash
git branch -M main            # already main
gh repo create <owner>/speckit-openproject --private --source=. --remote=origin --push
```
Then replace `<owner>` in `preset/preset.yml`, `extension/extension.yml` and `README.md`.

## Before making it public
- No secrets in history (`git log -p | grep -i token`), no private instance URLs.
- `LICENSE` (MIT) present in both packages, READMEs complete, CI green.
- Tag `preset-v1.0.0` / `extension-v0.1.0`, create GitHub releases, then file the catalog-submission issues in github/spec-kit following the current contributing guide (re-read it; process changes).
