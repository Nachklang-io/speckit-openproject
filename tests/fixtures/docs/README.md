# Fixtures recorded for feature 004 (task T002)

Recorded 2026-10-06 against the sandbox (OpenProject 17.9.1, `jtauschl/openproject-ce-mcp` v0.4.1, `OPENPROJECT_ATTACHMENT_ROOT` set to the repo root). Scratch work package 113 (`VERIFY-004 ...`) and attachments 3 and 4; the maintainer removes them by hand. Secret-free: the host part of every `download_url` was removed (path only), no token, no `.env` content.

| File | What it shows |
|---|---|
| `attachment-upload-preview.json` | preview of an upload: `payload.fileName` is the base name of the file |
| `attachment-upload-confirm.json` | confirm result: `attachment_id`, `result.download_url` (the real response contains the instance host: never copy it) |
| `attachments-list.json` | `list_work_package_attachments` fields: id, file_name, file_size_bytes, no digest |
| `attachments-list-duplicate-name.json` | two attachments with the same name coexist (upload first, delete second leaves this state briefly) |
| `attachment-delete-preview.json` | `delete_attachment` has a `confirm` step; the preview names the attachment |
| `description-roundtrip.json` | the description written with begin/end comment markers comes back byte for byte, wrapped in `<user-content>`; `attachment:` links render without `href`, path links render with `href` |

Not recorded: the path-outside-root preview, which fails with the generic `Error executing tool create_work_package_attachment` (no body).
