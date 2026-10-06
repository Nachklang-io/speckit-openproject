# Contract: `speckit.openproject.sync-docs`

Invocation: `/speckit-openproject-sync-docs [--dry-run] [feature-dir]` (skills mode), `/speckit.openproject.sync-docs` (command mode). Feature directory: argument, else `.specify/feature.json`.

## Capabilities used (embedded map rows)

`get-work-package`, `update-work-package`, `create-attachment`, `list-attachments`, `delete-attachment`. Tool names only in the embedded table.

## Steps (numbered in the prompt; every run starts from scratch)

0. Capability check: `create-attachment` callable? No → stop (FR-010), also with `--dry-run`.
1. Read config (`project`), ledger (`items.feature.id`, `documents`), documents, hashes. Missing/invalid → stop naming the file; `spec.md` missing → stop.
2. `get-work-package` (feature WP: exists? description, lock version); `list-attachments` for it.
3. Classify (decision table R6) and show the plan table. `--dry-run` ends here with `Dry run: nothing was written.`
4. One confirmation for the whole plan.
5. Per document, in fixed order: cleanup of `pending_delete`; upload/replace per R7; ledger after each write.
6. Render the summary block from the ledger and the attachment link paths (path of `download_url` without scheme and host; fallback: file name in backticks); re-read the description (`get-work-package`; truncated → stop before this step); strip the `<user-content>` wrapper; replace/append the block; write the description without the wrapper; preview, confirm; only if the text differs. The host part of `download_url` is never written, printed or logged.
7. Report: counts (attached, replaced, restored, cleaned, unchanged, orphan, blocked, failed, skipped), changed items, warnings, result `complete` | `incomplete` | `no changes` | `dry run` | `stopped`.

## Stop conditions (zero writes)

Upload capability missing; config or ledger missing/invalid; no `items.feature.id`; feature work package not found (stale); `spec.md` missing; MCP server not connected; summary markers in an inconsistent state (before step 5 only if the description is already readable; otherwise at step 6 with the attachments reported as done).

## Guarantees

No work package is created, deleted or re-parented; only attachments uploaded by this command are deleted; text outside the summary markers is untouched; no host, URL or token appears in a file, the report or the description; a second run on unchanged inputs writes nothing.
