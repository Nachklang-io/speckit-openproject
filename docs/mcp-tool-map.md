# MCP capability → tool map

Single place that maps capabilities used by the commands to tool names. Add a column per supported server.

| Capability | jtauschl/openproject-ce-mcp v0.4.1 | Verified params |
|---|---|---|
| list projects | `list_projects` | no |
| list types / statuses / priorities | `list_types`, `list_statuses`, `list_priorities` | no |
| list versions / create version | `list_versions`, `create_version` | no |
| search work packages | `list_work_packages` | no |
| create / update work package | `create_work_package`, `update_work_package` (preview, then `confirm=true`) | no |
| create relation | `create_work_package_relation` | no |
| add comment | `add_work_package_comment` | no |
| create time entry | `create_time_entry`, `list_time_entry_activities` | no |
| attach file | `create_work_package_attachment` | no |

"Verified params" = parameters exercised against a real instance. Fill this in during feature 001.
