# Research: Documentation Sync

Status of each item: **V** = verified, **P** = decided by design, **U** = unverified, checked by T002 before the prompt is written.

## R1 Upload tool contract (V, verified live 2026-10-06, task T002)

Schema: `create_work_package_attachment(work_package_id, file_path, description?, confirm=false)`; no inline content, no filename. The tool only exists when `OPENPROJECT_ATTACHMENT_ROOT` is set, so "tool not in the tool list" is the capability check (FR-010). Verified with the root set to the repo root and scratch work package 113:
- The preview shows `payload.fileName` = base name of the file and `fileSize`; the attachment name is the file name (no way to choose another).
- The confirm returns `attachment_id` and `result` (id, file_name, file_size_bytes, status `uploaded`, `download_url`). **`download_url` contains the instance host**: it is read for its path only and never written to a file, the report or the description.
- A file outside the root fails already in the preview with the generic `Error executing tool create_work_package_attachment` (no message): the command reports a failed document and names the upload root as the likely cause.
- Two attachments with the same file name can coexist (ids 3 and 4), so "upload first, then delete" really leaves a duplicate until the delete.
- `list_work_package_attachments` returns per attachment `id`, `file_name`, `file_size_bytes`, `content_type`, `status`, `author`, `container_id`, `created_at`, `download_url`; no digest. The ledger hash therefore decides what is current.
- `delete_attachment(attachment_id, confirm=false)` has preview-then-confirm; the preview names the attachment; after the confirm the list shows only the new attachment.
Decision: the command passes the absolute path of the document in the feature directory; the maintainer's upload root must contain it (documented in the README).
Alternatives: copying documents to a temp file in the root (rejected: leaves files, the command cannot know the root); base64 through the model (not offered by the tool).

## R2 Hash (P)

Lowercase hex SHA-256 of the file bytes, `shasum -a 256 <file>` (or `sha256sum`), same tool as the content hash of feature 001. Short hash in the summary: first 8 hex characters.

## R3 Ledger shape (P)

New optional top-level object `documents`, keyed by file name (`spec.md`, `plan.md`, `research.md`, `data-model.md`), value `{hash, attachment_id, synced, pending_delete?}`. Not added to `items`: its `kind` enum, `additionalProperties: false` and the item keys are read by features 001 and 003 as "one work package per key". `schema_version` stays `1.0` (additive). `synced` = `YYYY-MM-DD` of the run that uploaded the current content.

## R4 Summary block and markers (P; marker survival V)

Block, rendered from the ledger in the fixed order spec, plan, research, data-model, only documents present in the ledger:

```text
<!-- speckit-docs:begin -->
## Design documents (generated)

| Document | Short hash | Last synced change |
|---|---|---|
| [spec.md](/openproject/api/v3/attachments/4/content) | `a1b2c3d4` | 2026-10-06 |
<!-- speckit-docs:end -->
```

Replacement rule: if begin and end markers both exist exactly once, replace from begin through end inclusive; if neither exists, append the block after one blank line (or use it as the whole description if empty); any other marker state (one missing, duplicated, end before begin) stops the run with a message, nothing is written. Text outside is kept byte for byte. Verified 2026-10-06 (T002): the description written with the comment markers comes back byte for byte from `get_work_package` (`select` works), and the comments are invisible in the rendered HTML, so the comment markers stay and the heading fallback is not needed.
No excerpts, no model text (clarification 2).

## R5 Links (V, decided 2026-10-06 after T002)

The `attachment:<file name>` form renders as an `<a>` **without `href`** (not a working link), so it is not used. A path-only Markdown link renders with `href`: `[spec.md](/openproject/api/v3/attachments/4/content)` (verified in the update preview). The link path is the `download_url` of the attachment from `list-attachments` with scheme and host removed; it contains the instance's path prefix and the attachment id but no host. If the path cannot be derived, the row shows the file name in backticks without a link. The block text is rendered from the ledger plus the current attachment paths, so the same input gives the same text. Links go stale only if the instance's path prefix changes; the next change of a document rewrites the block.

## R6 Decision table (P)

Inputs per document: `local` (exists, hash), `ledger` (hash `h`, attachment id `i`, optional `pending_delete` `p`), `A` = ids of attachments on the work package named like the document, minus `p`.

| local | ledger | A | Action | Writes |
|---|---|---|---|---|
| missing | none | empty | skip (`spec.md` missing: stop) | none |
| missing | any | any | orphan | none |
| present | none | empty | new | upload, ledger |
| present | none | non-empty | blocked (foreign attachment) | none |
| present | entry | empty | restored | upload, ledger |
| present | entry | `{i}` and `h` = local | unchanged | none |
| present | entry | `{i}` and `h` ≠ local | changed | upload, ledger (new id, `pending_delete` = i), delete i, ledger (clear) |
| present | entry | other ids | blocked (ambiguous) | none |

Cleanup: independent of the row, a `pending_delete` `p` that still exists on the work package is deleted and cleared (action `cleaned`); one that no longer exists is only cleared. A document with `blocked` does not stop the others.
Why `blocked` for unknown extras: the command may only delete what it uploaded (ADR-0004); anything else is reported.

## R7 Order of writes (P, from clarification 1)

Per document: preview → confirm upload → ledger (new id, `pending_delete` old id) → `delete-attachment` (only with a confirm if the tool has one, else after the plan confirmation) → ledger (clear). After all documents: render the block from the ledger, `get-work-package` description, compare, `update-work-package` description with preview/confirm only if the text differs. A failed upload leaves the old attachment and ledger as they were. The description write has no ledger entry: its idempotence comes from the text comparison (same block = no write), not from the ledger.

## R8 Capability check (P)

Step 0 of the prompt: if `create-attachment` is not among the callable tools, stop with the message naming the capability and the server setting `OPENPROJECT_ATTACHMENT_ROOT`; no other call happens, also in `--dry-run`. The prompt only names capability ids; tool names live in the embedded map rows.

## R9 Description read (V)

`get_work_package` with `select=["description","lock_version","description_truncated"]` returns the raw Markdown wrapped in `<user-content>…</user-content>`, `description_truncated: false` for a 256-character description, and `lock_version`. The command strips exactly that wrapper (first `<user-content>` and last `</user-content>`) before replacing the block, and writes the new description without the wrapper. If `description_truncated` is true the command stops before the description step and reports the attachments as done (`incomplete`). An update with a stale `lock_version` is rejected by the server (not exercised, labelled untested).

## R10 Untrusted content (P)

Descriptions and attachment names come from users: used for the string comparisons only, never followed as instructions, same rule as 001/003.
