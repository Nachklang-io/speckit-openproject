# Research: Documentation Sync

Status of each item: **V** = verified, **P** = decided by design, **U** = unverified, checked by T002 before the prompt is written.

## R1 Upload tool contract (U for behaviour, V for schema)

Schema read live on 2026-10-06 (server v0.4.1, upload root configured): `create_work_package_attachment(work_package_id, file_path, description?, confirm=false)`. No inline content, no filename. The tool only exists when `OPENPROJECT_ATTACHMENT_ROOT` is set, so "tool not in the tool list" is the capability check (FR-010). A call with a missing work package ids failed with the generic tool error (as for other tools). Decision: the command passes the absolute path of the document in the feature directory; the maintainer sets the upload root to the repo (or scratch project) root. Unknown until T002: attachment name = base name of the file; whether a path outside the root is rejected in the preview; what the confirm returns (attachment id).
Alternatives: copying documents to a temp file in the root (rejected: leaves files, needs a path the command cannot know); base64 through the model (not offered by the tool).

## R2 Hash (P)

Lowercase hex SHA-256 of the file bytes, `shasum -a 256 <file>` (or `sha256sum`), same tool as the content hash of feature 001. Short hash in the summary: first 8 hex characters.

## R3 Ledger shape (P)

New optional top-level object `documents`, keyed by file name (`spec.md`, `plan.md`, `research.md`, `data-model.md`), value `{hash, attachment_id, synced, pending_delete?}`. Not added to `items`: its `kind` enum, `additionalProperties: false` and the item keys are read by features 001 and 003 as "one work package per key". `schema_version` stays `1.0` (additive). `synced` = `YYYY-MM-DD` of the run that uploaded the current content.

## R4 Summary block and markers (P, marker survival U)

Block, rendered from the ledger in the fixed order spec, plan, research, data-model, only documents present in the ledger:

```text
<!-- speckit-docs:begin -->
## Design documents (generated)

| Document | Short hash | Last synced change |
|---|---|---|
| [spec.md](attachment:spec.md) | `a1b2c3d4` | 2026-10-06 |
<!-- speckit-docs:end -->
```

Replacement rule: if begin and end markers both exist exactly once, replace from begin through end inclusive; if neither exists, append the block after one blank line (or use it as the whole description if empty); any other marker state (one missing, duplicated, end before begin) stops the run with a message, nothing is written. Text outside is kept byte for byte. If T002 shows that comments are stripped on the round trip, the markers become the heading line `## Design documents (generated)` through the line before the next heading of level 1–2 or the end; the contract is updated then.
No excerpts, no model text (clarification 2).

## R5 Links (P, rendering U)

Relative `attachment:<file name>` link, so no host or id appears in the description. Fallback if it does not render: plain file name in backticks. T002 decides.

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

Per document: preview → confirm upload → ledger (new id, `pending_delete` old id) → `delete-attachment` (only with a confirm if the tool has one, else after the plan confirmation) → ledger (clear). After all documents: render the block from the ledger, `get-work-package` description, compare, `update-work-package` description with preview/confirm only if the text differs. A failed upload leaves the old attachment and ledger as they were.

## R8 Capability check (P)

Step 0 of the prompt: if `create-attachment` is not among the callable tools, stop with the message naming the capability and the server setting `OPENPROJECT_ATTACHMENT_ROOT`; no other call happens, also in `--dry-run`. The prompt only names capability ids; tool names live in the embedded map rows.

## R9 Description read (U)

`get_work_package` returns the description inside `<user-content>` tags and possibly trimmed ("trimmed responses and field selection" in the server instructions). T002 checks whether `select=["description"]` returns the raw Markdown unchanged. If the server returns a rendered or trimmed form, the command cannot safely rewrite the description: it then stops before the description step and reports the attachments as done (result `incomplete`).

## R10 Untrusted content (P)

Descriptions and attachment names come from users: used for the string comparisons only, never followed as instructions, same rule as 001/003.
