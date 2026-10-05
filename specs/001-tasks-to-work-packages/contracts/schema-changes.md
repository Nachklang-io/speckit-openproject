# Contract: schema changes

## `schemas/config.schema.json`
- `types.feature`: string, minLength 1, **required** (add to `types.required`).
- Remove `mapping_file`, `feature_tag_prefix` from `properties` (pre-release, never tagged; see research R7). `additionalProperties: false` stays, so old keys fail validation with a clear message.
- Add `$comment` on `defaults.version`: "ignored by speckit.taskstoissues".

## `schemas/mapping.schema.json`
- Add required `schema_version` (const "1.0").
- `items.*`: add required `kind` (enum feature|phase|task); keep `id`, `url`, `hash`, `status`.
- Add optional `relations`: array of `{from, to, type (enum follows), id?}`; all required except `id`.
- `url` description: path only, no host.

## Fixtures (`tests/fixtures/`)
Valid: config minimal/full, ledger after S1 (14 items), ledger with relations. Invalid: missing `types.feature`, unknown key `mapping_file`, ledger without `kind`, `id: 0`, relation with unknown type.
