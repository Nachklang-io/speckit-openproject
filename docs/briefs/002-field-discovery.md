# Brief 002: Field discovery and config bootstrap (extension)

Command `speckit.openproject.discover-fields`: reads types, statuses, priorities, versions, custom fields (incl. mandatory ones) of the target project via MCP and writes/updates `.specify/openproject/config.yml` interactively, proposing mappings for phase/task types and status names. Never overwrites user edits without showing a diff. Acceptance: fresh project reaches a valid config in one run; schema-valid output.
