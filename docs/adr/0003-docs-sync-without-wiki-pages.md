# ADR-0003: Documentation sync uses attachments and descriptions

Status: accepted (2026-10-05), to be re-verified in feature 004

Context: The MCP server exposes wiki read and link tools but no wiki page creation; OpenProject API v3 has no endpoint to create wiki pages.

Decision: spec.md and plan.md are attached to the feature's parent work package, with a generated summary and relative links in its description. Revisit if the API or MCP server gains wiki writes.
