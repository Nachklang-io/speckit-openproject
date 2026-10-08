# OpenProject for spec-kit (bundle)

Installs the `openproject` preset and the `openproject` extension in one step, pinned to the
versions in `bundle.yml`. Both packages talk to OpenProject only through an MCP server; configure
that server in your agent's MCP client config first (see the main repository README).

## Install

spec-kit bundles reference packages instead of embedding them. Each bundle release therefore
ships two one-entry catalogs that point at the published preset and extension archives (pinned
by version and sha256). Replace `<release>` with the bundle release's download URL, for example
`https://github.com/Nachklang-io/speckit-openproject/releases/download/bundle-v0.1.0`.

```bash
specify preset catalog add <release>/openproject-presets-catalog.json --name openproject --install-allowed
specify extension catalog add <release>/openproject-extensions-catalog.json --name openproject --install-allowed
curl -LO <release>/openproject-0.1.0.zip
specify bundle install ./openproject-0.1.0.zip
```

## Contents

| Component | Version |
|-----------|---------|
| preset `openproject` | 1.0.0 |
| extension `openproject` | 0.1.0 |

Source and changelog: https://github.com/Nachklang-io/speckit-openproject
