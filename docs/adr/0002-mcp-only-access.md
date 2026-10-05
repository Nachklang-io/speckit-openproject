# ADR-0002: OpenProject access only via MCP

Status: accepted (2026-10-05)

Decision: Commands use MCP tools only. Default server: `jtauschl/openproject-ce-mcp` (MIT, Community Edition compatible, preview-then-confirm, project allowlists). The official OpenProject MCP server is an Enterprise add-on and is a possible second target through the capability map.

Consequences: Safety features of the server (allowlists, confirm) apply. Tool names differ per server, so they are mapped centrally in `docs/mcp-tool-map.md`. Missing tools (e.g. wiki page creation) are limitations, not reasons to call REST.
