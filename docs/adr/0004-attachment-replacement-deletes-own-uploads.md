# ADR-0004: Replacing a synced document deletes the attachment this project uploaded

Status: accepted (2026-10-06), maintainer decision during feature 004

Context: Constitution principle III said "Deletions are never performed by this project". Documentation sync (feature 004) keeps one attachment per design document on the feature work package. OpenProject does not version attachments, so a changed document can only be represented by uploading the new content and removing the old attachment.

Decision: Principle III gets one narrow exception. The project may delete an attachment only if (1) it uploaded that attachment itself, recognised by the attachment id in the ledger (`documents.<file>.attachment_id` or `pending_delete`), (2) a newer version of the same document replaces it, and (3) the plan naming the deletion was shown and confirmed. The new attachment is uploaded first and the ledger records the old id as `pending_delete` before it is deleted, so an interrupted run can finish the cleanup. Constitution version 1.2.0 (MINOR).

Consequences: Attachments the project did not create are never deleted; an unknown attachment with a document's name makes that document `blocked` and is reported. Work packages, comments, relations and everything else remain undeletable by this project; the maintainer still removes test data by hand.

Rejected alternatives: versioned names such as `spec.<hash>.md` (attachments pile up, the work package becomes noisy); a separate confirmation per file (adds prompts without adding safety beyond the confirmed plan).
