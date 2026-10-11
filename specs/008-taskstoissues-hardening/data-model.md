# Data Model: taskstoissues Hardening

No stored data changes: no new config key, no change to the mapping ledger or to a schema (FR-010). The two entities below exist only in the printed output of the command.

## Plan row

One line of the plan table of step 9, one per ledger key (feature, `phase-N`, `T###`).

| Field | Source | Rule |
|---|---|---|
| key | tasks.md / ledger key | one row per key; no ranges, no "…" |
| kind | feature, phase, task, subtask | unchanged |
| subject | step 7 | unchanged |
| parent key | step 9 | unchanged |
| action | step 9 | unchanged |
| hash | step 7 shell command | first 12 hex characters of the current hash |
| stored | ledger entry `hash` | first 12 hex characters, or `—` without a ledger entry |
| reason | step 9 | unchanged |

Long plans are printed in parts of at most 40 rows (header repeated, `part i of n`); the counts line follows the last part.

## Stop message

| Reason | Trigger | Content |
|---|---|---|
| missing file | prerequisite script exits non-zero | the script's message verbatim; the missing file; the command that creates it for the current mode |
| missing write permission | capability `work_packages/create/w<project_id>-<user_id>` is `[not_found]` | project identifier, user id, capability id; no write was made; the grant list is informational |
| missing type | a configured type is not in the type list (role may create) | unchanged: name it, list the available types |

State transitions: none. Every stop happens before the first write, so nothing needs cleanup.
