# ADR-0003: Documentation sync uses attachments and descriptions

Status: accepted (2026-10-05); re-verified in feature 004 on 2026-10-06: the MCP server (v0.4.1) still has wiki read and link tools only, no tool to create or edit a wiki page; attachments and the description work (see `docs/mcp-tool-map.md`)

Context: The MCP server exposes wiki read and link tools but no wiki page creation; OpenProject API v3 has no endpoint to create wiki pages.

Decision: spec.md and plan.md are attached to the feature work package, with a generated summary and relative links in its description. Revisit if the API or MCP server gains wiki writes.
