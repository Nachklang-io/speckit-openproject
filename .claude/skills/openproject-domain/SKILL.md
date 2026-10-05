---
name: openproject-domain
description: OpenProject concepts and the MCP tool map used by this repo (work packages, types, relations, versions, time entries, attachments, wiki limits). Load before writing or reviewing any prompt that touches OpenProject.
---

# OpenProject domain notes

## Concept mapping (spec-kit → OpenProject)
| spec-kit | OpenProject | Notes |
|---|---|---|
| Feature (`specs/NNN-*`) | Version (milestone) or parent work package | configurable, default: parent work package of type "Feature"/"Epic" |
| Phase in tasks.md | Work package (type Phase/Milestone) | |
| Task `T001` | Work package (type Task), parent = phase | subject starts with `T001` for lookup |
| Dependency | Relation `follows` / `blocks` | not between `[P]` tasks |
| spec.md / plan.md | Attachment + link in description | wiki pages cannot be created via API v3 |
| Implementation time | Time entry on the work package | optional |
| Status in tasks.md (`[ ]`/`[X]`) | Work package status | mapping in config |

## MCP server: jtauschl/openproject-ce-mcp (verified v0.4.1, MIT)
Env: `OPENPROJECT_BASE_URL`, `OPENPROJECT_API_TOKEN`, `OPENPROJECT_READ_PROJECTS`, `OPENPROJECT_WRITE_PROJECTS`, feature flags `OPENPROJECT_ENABLE_WORK_PACKAGE_WRITE`, `..._VERSION_WRITE`, `..._WIKI_*` etc.
Writes use preview first, then call again with `confirm=true`. OpenProject permissions apply on top.

Verified tool names (from the package source):
- Projects/metadata: `list_projects`, `get_project`, `list_types`, `list_statuses`, `list_priorities`, `list_versions`, `get_project_configuration`
- Work packages: `list_work_packages`, `get_work_package`, `create_work_package`, `update_work_package`, `add_work_package_comment`
- Relations: `create_work_package_relation`, `list_relations`, `update_relation`, `delete_relation`, `get_work_package_relations`
- Versions: `create_version`, `get_version`
- Time: `create_time_entry`, `list_time_entries`, `list_time_entry_activities`
- Attachments: `create_work_package_attachment`, `list_work_package_attachments`
- Wiki: `get_wiki_page`, `create_work_package_wiki_link` (read and link only, no page creation)

Not verified yet (check before relying): exact parameter names of each tool, how the parent is set on create, custom-field payload shape, preview response format. Record findings in `docs/mcp-tool-map.md` as they are verified.

## Pitfalls
- Types, statuses, workflows and required custom fields differ per project; always discover first.
- Closed statuses may block edits; status transitions follow the workflow of type + role.
- Parent/child dates and progress are derived by OpenProject depending on the project's mode.
- Subject length limit and markdown flavour (CommonMark/GFM) apply to descriptions.
- Other community MCP servers use different tool names; do not hardcode names outside the capability table.
