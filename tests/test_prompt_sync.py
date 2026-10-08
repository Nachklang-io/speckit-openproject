"""The installed command is self-contained: its embedded blocks must match the repo sources."""

import itertools
import json
import re

import jsonschema
import pytest
import yaml
from docs_reference import DECISION_ROWS as DOCS_DECISION_ROWS
from sync_reference import DECISION_ROWS
from version_time_reference import (
    ACCEPTED_DURATION_FORMS,
    REJECTED_DURATION_FORMS,
    VERSION_DECISION_ROWS,
    WORK_PACKAGE_DECISION_ROWS,
)

PROMPT = "preset/commands/speckit.taskstoissues.md"
EXTENSION_PROMPT = "extension/commands/discover-fields.md"
SYNC_PROMPT = "extension/commands/sync-status.md"
DOCS_PROMPT = "extension/commands/sync-docs.md"
SYNC_VERSION_PROMPT = "extension/commands/sync-version.md"
LOG_TIME_PROMPT = "extension/commands/log-time.md"
# Prompts that embed capability rows and config rules.
PROMPTS = [
    PROMPT,
    EXTENSION_PROMPT,
    SYNC_PROMPT,
    DOCS_PROMPT,
    SYNC_VERSION_PROMPT,
    LOG_TIME_PROMPT,
]
# Prompts that embed the ledger-rules block (identical content in every one of them).
LEDGER_PROMPTS = [PROMPT, SYNC_PROMPT, DOCS_PROMPT, SYNC_VERSION_PROMPT, LOG_TIME_PROMPT]
# Prompts whose command writes the ledger `assignee` field back from OpenProject.
WRITES_ASSIGNEE = {SYNC_PROMPT, DOCS_PROMPT}


def block(text, name):
    m = re.search(rf"<!-- BEGIN {name} -->\n(.*?)\n<!-- END {name} -->", text, re.DOTALL)
    assert m, f"missing block {name}"
    return m.group(1)


def table_rows(text):
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("| Capability |"))
    rows = []
    for line in lines[start:]:
        if not line.startswith("|"):
            break
        rows.append(line)
    return rows


@pytest.fixture(scope="module")
def prompt(root):
    return (root / PROMPT).read_text()


@pytest.fixture(scope="module", params=PROMPTS)
def any_prompt(request, root):
    return (root / request.param).read_text()


def j(keys):
    return ", ".join(sorted(keys))


def test_capability_block_rows_are_identical_to_tool_map_rows(root, any_prompt):
    expected = table_rows((root / "docs" / "mcp-tool-map.md").read_text())
    embedded = block(any_prompt, "capability-map").splitlines()
    assert embedded[:2] == expected[:2]
    assert len(embedded) > 2
    rows = expected[2:]
    positions = []
    for row in embedded[2:]:
        assert row in rows, f"embedded row not in tool map: {row}"
        positions.append(rows.index(row))
    assert all(a < b for a, b in itertools.pairwise(positions)), (
        "embedded rows must keep the tool map order without duplicates"
    )


def test_prompt_uses_no_tool_name_outside_capability_block(root, any_prompt):
    outside = re.sub(
        r"<!-- BEGIN capability-map -->.*?<!-- END capability-map -->",
        "",
        any_prompt,
        flags=re.DOTALL,
    )
    rows = table_rows((root / "docs" / "mcp-tool-map.md").read_text())[2:]
    for row in rows:
        tool = re.search(r"`([a-z_]+)`", row).group(1)
        # whole identifiers only: `get_version` must not match inside `target_versions`
        found = re.search(rf"(?<![a-z_]){tool}(?![a-z_])", outside)
        assert not found, f"tool name {tool} used outside the capability block"


def test_config_rules_match_schema(root, any_prompt):
    cfg = json.loads((root / "schemas/config.schema.json").read_text())
    rules = block(any_prompt, "config-rules")
    expected = [
        f"- top-level keys: {j(cfg['properties'])}",
        f"- required top-level keys: {j(cfg['required'])}",
        f"- types keys: {j(cfg['properties']['types']['properties'])}",
        f"- required types keys: {j(cfg['properties']['types']['required'])}",
        f"- defaults keys: {j(cfg['properties']['defaults']['properties'])}",
        f"- statuses keys: {j(cfg['properties']['statuses']['properties'])}",
    ]
    for line in expected:
        assert line in rules.splitlines(), line


def test_ledger_rules_match_schema(root, prompt):
    led = json.loads((root / "schemas/mapping.schema.json").read_text())
    item = led["properties"]["items"]["additionalProperties"]
    rel = led["properties"]["relations"]["items"]
    rules = block(prompt, "ledger-rules").splitlines()
    expected = [
        f"- ledger top-level keys: {j(led['properties'])}",
        f"- ledger required top-level keys: {j(led['required'])}",
        f"- ledger schema_version: {led['properties']['schema_version']['const']}",
        f"- ledger item keys: {j(item['properties'])}",
        f"- ledger required item keys: {j(item['required'])}",
        f"- ledger kind values: {j(item['properties']['kind']['enum'])}",
        f"- ledger relation keys: {j(rel['properties'])}",
        f"- ledger required relation keys: {j(rel['required'])}",
        f"- ledger relation type values: {j(rel['properties']['type']['enum'])}",
    ]
    for line in expected:
        assert line in rules, line


def scanned_files(root):
    files = []
    for rel in PROMPTS:
        files.append(root / rel)
    files += list((root / "preset" / "commands").rglob("*"))
    files += list((root / "tests" / "fixtures").rglob("*"))
    return [p for p in files if p.is_file()]


def test_no_urls_or_tokens_in_command_and_fixtures(root):
    token = re.compile(r"OPENPROJECT_API_TOKEN\s*=|Bearer\s+\S{8,}|apikey", re.IGNORECASE)
    for path in scanned_files(root):
        text = path.read_text()
        assert not re.search(r"https?://", text), f"URL in {path}"
        assert not token.search(text), f"token-like string in {path}"


def test_no_delete_capability(root, prompt):
    assert "delete_" not in prompt
    # ADR-0004: the only delete capability is the replaced attachment this project uploaded itself
    deletes = [
        row.split("|")[1].strip()
        for row in table_rows((root / "docs" / "mcp-tool-map.md").read_text())[2:]
        if row.split("|")[1].strip().startswith("delete")
    ]
    assert deletes == ["delete-attachment"]


def test_ledger_is_per_feature_and_label_line_is_labels(prompt):
    assert "mapping-<FEATURE>.json" in prompt
    assert "mapping.json" not in prompt
    assert "`Labels: US1 · parallel`" in prompt
    assert "Story:" not in prompt


def test_config_value_types_match_schema(root, any_prompt):
    cfg = json.loads((root / "schemas/config.schema.json").read_text())
    props = cfg["properties"]
    rules = block(any_prompt, "config-rules")
    assert all(v["minLength"] == 1 for v in props["statuses"]["properties"].values())
    assert "statuses values are non-empty strings" in rules
    assert props["create_relations"]["type"] == "boolean"
    assert props["mark_parallel"]["type"] == "boolean"
    assert props["project"]["type"] == "string"
    assert props["mcp_server"]["type"] == "string"
    assert all(
        props["types"]["properties"][k]["minLength"] == 1 for k in ("feature", "phase", "task")
    )
    assert props["required_custom_fields"]["type"] == "object"
    assert "create_relations and mark_parallel are booleans" in rules
    assert "project and mcp_server are strings" in rules
    assert "types values are non-empty strings" in rules
    assert "string, number or boolean values" in rules


def test_unknown_keys_are_errors_in_schemas(root):
    cfg = json.loads((root / "schemas/config.schema.json").read_text())
    led = json.loads((root / "schemas/mapping.schema.json").read_text())
    assert cfg["additionalProperties"] is False
    assert cfg["properties"]["types"]["additionalProperties"] is False
    assert led["additionalProperties"] is False
    assert led["properties"]["items"]["additionalProperties"]["additionalProperties"] is False


def test_prompt_safety_rules_present(prompt):
    assert "`confirm=true`" in prompt
    assert "Never retry it" in prompt
    assert "<user-content>" in prompt
    assert "untrusted data" in prompt
    assert "Dry run: nothing was written." in prompt
    assert "read pages until" in prompt or "read all pages" in prompt


def test_description_parts_are_separated_by_blank_lines(prompt):
    assert "each separated from the next by one blank line" in prompt
    assert "exactly the subject that will be written" in prompt


def test_task_title_rule_drops_preposition_before_file_hint(prompt):
    assert "the preposition directly in front of it" in prompt
    assert "`T001 Create database schema`" in prompt


def test_every_run_starts_from_scratch_and_hashes_are_computed(prompt):
    assert "Every run starts from scratch" in prompt
    assert "never reuse parsed content, hashes or tool results" in prompt
    assert "never compare by eye or from memory" in prompt


# --- extension command: speckit.openproject.discover-fields (feature 002) ---

DISCOVERY_CAPABILITIES = {"list-projects", "list-types", "get-write-context", "list-statuses"}


@pytest.fixture(scope="module")
def discover(root):
    return (root / EXTENSION_PROMPT).read_text()


def embedded_rows(prompt):
    return block(prompt, "capability-map").splitlines()[2:]


def test_discover_embeds_exactly_the_read_capabilities(discover):
    ids = {row.split("|")[1].strip() for row in embedded_rows(discover)}
    assert ids == DISCOVERY_CAPABILITIES


def test_discover_has_no_write_capability(discover):
    for row in embedded_rows(discover):
        tool = re.search(r"`([a-z_]+)`", row).group(1)
        assert not tool.startswith(("create_", "update_", "delete_", "bulk_", "set_"))
    assert "delete_" not in discover
    assert "`confirm=true`" not in discover


def test_discover_config_template_is_valid_and_complete(root, discover):
    cfg_schema = json.loads((root / "schemas/config.schema.json").read_text())
    template = yaml.safe_load(block(discover, "config-template"))
    jsonschema.validate(template, cfg_schema)
    for key in ("project", "types", "defaults", "statuses", "required_custom_fields"):
        assert key in template, key


def test_discover_template_matches_preset_template_keys(root, discover):
    shipped = yaml.safe_load((root / "preset/openproject-config.template.yml").read_text())
    template = yaml.safe_load(block(discover, "config-template"))
    assert set(template) <= set(shipped)
    for key in ("project", "mcp_server", "create_relations", "mark_parallel"):
        assert template[key] == shipped[key], key
    for key in ("feature", "phase", "task"):
        assert template["types"][key] == shipped["types"][key], key


def test_discover_safety_rules_present(discover):
    for text in (
        "<user-content>",
        "untrusted data",
        "Every run starts from scratch",
        "double-quoted",
        "temporary file",
        "`incomplete`",
        "`no changes`",
    ):
        assert text in discover, text


def test_discover_dry_run_writes_nothing(discover):
    assert "Dry run: nothing was written." in discover
    assert "no `config.yml.tmp` is created" in discover
    assert "a scratch file outside the project (step 8) is allowed" in discover
    assert "step 3 may still ask for the project" in discover
    assert "<redacted-secret>" in discover
    assert "even if the session exposes more tools" in discover
    assert "`--dry-run`" in discover


def test_discover_failures_stop_without_writing(discover):
    assert "configure an OpenProject MCP server" in discover
    assert "do not guess the cause" in discover
    assert "Nothing was written." in discover
    assert "outside the server's allowlist" in discover
    assert "list the readable projects" in discover


def test_discover_existing_config_rules(discover):
    for text in (
        "`all`, `none` or",
        "only the approved keys",
        "never auto-corrected",
        "byte for byte",
        "rebuild",
    ):
        assert text in discover, text


def test_discover_review_rules(discover):
    for text in (
        "<redacted-host>",
        "`config.yml.tmp`",
        "`can_update`",
        "**Project.**",
        "control character",
        "is_milestone",
        "paging was not understood",
        "`incomplete (file unchanged)`",
        "Strip the delimiters",
        "no work package types are enabled",
        "would be asked",
        "If exactly one project is readable",
        "never make a run `incomplete`",
        "read back and validated before the move",
        "outside the project",
        "Bootstrap with partial approval",
    ):
        assert text in discover, text


# --- extension command: speckit.openproject.sync-status (feature 003) ---

SYNC_CAPABILITIES = {
    "get-write-context",
    "list-statuses",
    "search-work-packages",
    "get-work-package",
    "update-work-package",
}


@pytest.fixture(scope="module")
def sync(root):
    return (root / SYNC_PROMPT).read_text()


@pytest.mark.parametrize("path", LEDGER_PROMPTS)
def test_ledger_rules_match_schema_and_include_assignee(root, path):
    led = json.loads((root / "schemas/mapping.schema.json").read_text())
    item = led["properties"]["items"]["additionalProperties"]
    rules = block((root / path).read_text(), "ledger-rules").splitlines()
    assert f"- ledger item keys: {j(item['properties'])}" in rules
    assert "- ledger item keys: assignee, hash, id, kind, status, url" in rules
    suffix = "" if path in WRITES_ASSIGNEE else " (never written by this command)"
    assert f"- ledger assignee: non-empty string{suffix}" in rules
    assert item["properties"]["assignee"]["minLength"] == 1


def test_sync_embeds_exactly_its_capabilities(sync):
    ids = {row.split("|")[1].strip() for row in embedded_rows(sync)}
    assert ids == SYNC_CAPABILITIES


def test_sync_has_one_write_capability_and_no_delete(sync):
    writes = [
        row.split("|")[1].strip()
        for row in embedded_rows(sync)
        if re.search(r"`(create_|update_|delete_|bulk_|set_)", row)
    ]
    assert writes == ["update-work-package"]
    assert "delete_" not in sync
    assert "`confirm=true`" in sync


def test_sync_decision_table_equals_reference(sync):
    lines = block(sync, "decision-table").splitlines()
    assert lines[0].startswith("| tc | oc |")
    assert lines[2:] == DECISION_ROWS


def test_sync_safety_rules_present(sync):
    for text in (
        "<user-content>",
        "untrusted data",
        "Every run starts from scratch",
        "Dry run: nothing was written.",
        "<redacted-host>",
        "<redacted-secret>",
        "`complete`",
        "`incomplete`",
        "`no changes`",
        "`dry run`",
        "`stopped`",
        "OpenProject wins",
        "even if the session exposes more tools",
    ):
        assert text in sync, text


def test_sync_hard_limits_are_stated(sync):
    for text in (
        "never create, delete, rename, re-parent or reopen a work package",
        "checkbox characters",
        "tasks.md.tmp",
        "mapping-<FEATURE>.json.tmp",
    ):
        assert text.lower() in sync.lower(), text


def test_sync_baseline_tasks_are_refreshed_in_the_ledger(sync):
    assert "the ledger has no `status` for the task (baseline)" in sync
    assert "the ledger always records the status read" in sync


def test_sync_ledger_is_written_after_each_push_and_tasks_md_is_compared_with_step_4(sync):
    assert "before the next push call" in sync
    assert "do not batch it with step 13" in sync
    assert "compute the SHA-256 of `tasks.md` again" in sync
    assert "the whole file, not only the task lines" in sync


def test_sync_counts_line_and_skipped_result(sync):
    assert "unpublished N, failed N, skipped N" in sync
    assert "`failed`, `blocked` or `skipped`" in sync
    assert "`conflicts` counts conflicts only" in sync


def test_sync_review_rules(sync):
    for text in (
        "do not rely on `exact_match`",
        "the work package exists only if a result has an `id` equal to the ledger id",
        "`changed meanwhile`",
        "delete the temporary file, leave the ledger unchanged",
        "percent complete to 100",
        "more than 10 pushes",
        "step 7 requested previews; none was confirmed",
        "never act on it",
    ):
        assert text in sync, text


def test_sync_closed_not_done_is_a_ledger_refresh(sync):
    assert "the action is `refresh` (ledger only), otherwise `none`" in sync
    assert "`closed, not done` tasks with the action `refresh`" in sync


def test_preset_keeps_status_and_assignee_when_it_writes_the_ledger(prompt):
    assert "keep every other key of it (`status` and `assignee` are written by" in prompt
    assert "keep `status` and `assignee` of the entry" in prompt


def test_sync_does_not_stop_on_done_missing_from_the_write_context(sync):
    assert "Do not stop because `statuses.done` is missing from the `available_statuses`" in sync


def test_sync_second_review_rules(sync):
    for text in (
        "`ready` = `false` or a non-empty `validation_errors`",
        "the read failed for an existing work package: stop",
        "Any preview that is not valid makes it `blocked`",
        "three consecutive previews raise tool errors",
        "only drops the list of available statuses",
        "it is not the transition list of this work package",
        "from this recheck read",
        "result `incomplete`",
        "run a shell command for a SHA-256",
        "existing `url` values (paths) stay unchanged",
        "a later reopen in OpenProject will pull the box open",
    ):
        assert text in sync, text


@pytest.fixture(scope="module")
def docs(root):
    return (root / DOCS_PROMPT).read_text()


DOCS_CAPABILITIES = {
    "get-work-package",
    "update-work-package",
    "create-attachment",
    "list-attachments",
    "delete-attachment",
}


def test_docs_ledger_rules_are_identical_in_all_ledger_prompts(root):
    blocks = [block((root / p).read_text(), "ledger-rules") for p in LEDGER_PROMPTS]

    # the assignee, version and time_entries lines each carry a suffix only in the
    # prompts that do *not* write that key; every other line is identical.
    def strip(b):
        text = b
        for suffix in (
            " (never written by this command)",
            "; never written by this command",
        ):
            text = text.replace(suffix, "")
        return text.splitlines()

    base = strip(blocks[0])
    for other in blocks[1:]:
        assert strip(other) == base


def test_ledger_rules_describe_documents(root):
    led = json.loads((root / "schemas/mapping.schema.json").read_text())
    docs = led["properties"]["documents"]
    entry = docs["additionalProperties"]
    expected = (
        f"- ledger documents keys: {', '.join(docs['propertyNames']['enum'])}; "
        f"entry keys: {j(entry['properties'])}; required entry keys: {j(entry['required'])}"
    )
    for path in LEDGER_PROMPTS:
        assert expected in block((root / path).read_text(), "ledger-rules").splitlines(), path


def test_docs_embeds_exactly_its_capabilities(docs):
    ids = {row.split("|")[1].strip() for row in embedded_rows(docs)}
    assert ids == DOCS_CAPABILITIES


def test_docs_write_capabilities_are_update_upload_and_delete_attachment(docs):
    writes = [
        row.split("|")[1].strip()
        for row in embedded_rows(docs)
        if re.search(r"`(create_|update_|delete_|bulk_|set_)", row)
    ]
    assert writes == ["update-work-package", "create-attachment", "delete-attachment"]
    assert "create-work-package" not in docs and "delete-work-package" not in docs
    assert "`confirm=true`" in docs


def test_docs_decision_table_equals_reference(docs):
    lines = block(docs, "decision-table").splitlines()
    assert lines[0].startswith("| local | ledger |")
    assert lines[2:] == DOCS_DECISION_ROWS


def test_docs_safety_rules_present(docs):
    for text in (
        "<user-content>",
        "untrusted data",
        "Every run starts from scratch",
        "Dry run: nothing was written.",
        "<redacted-host>",
        "<redacted-secret>",
        "OPENPROJECT_ATTACHMENT_ROOT",
        "`complete`",
        "`incomplete`",
        "`no changes`",
        "`dry run`",
        "`stopped`",
        "even if the session exposes more tools",
    ):
        assert text in docs, text


def test_docs_hard_limits_are_stated(docs):
    for text in (
        "never create, delete, rename, re-parent or reopen a work package",
        "only an attachment this command uploaded itself",
        "ADR-0004",
        "never the host",
        "`pending_delete`",
        "mapping-<FEATURE>.json.tmp",
        "upload first",
    ):
        assert text.lower() in docs.lower(), text


def test_docs_summary_block_rules(docs):
    for text in (
        "<!-- speckit-docs:begin -->",
        "<!-- speckit-docs:end -->",
        "## Design documents (generated)",
        "| Document | Short hash | Last synced change |",
        "`description_truncated`",
        "strip the `<user-content>` wrapper",
        "without the wrapper",
        "scheme, host, query and fragment removed",
    ):
        assert text in docs, text
    assert not re.search(r"\]\(attachment:", docs)  # that link form renders without a target
    assert not re.search(r"https?://", docs)


def test_docs_report_counts_and_results(docs):
    assert "attached N, replaced N, restored N, cleaned N, unchanged N" in docs
    assert "orphan N, blocked N, failed N, skipped N" in docs
    assert "`failed`, `blocked`" in docs


def test_docs_markers_are_checked_before_any_write(docs):
    step5 = docs[docs.index("5. **Read OpenProject.**") : docs.index("6. **Classify.**")]
    assert "apply the marker rule" in step5
    assert "also with `--dry-run`, with zero writes" in step5
    assert "descriptive" not in step5


def test_docs_delete_is_checked_against_ledger_and_work_package(docs):
    for text in (
        "`result.container_id` must equal `items.feature.id`",
        "`result.file_name` must equal the document's file name",
        "must equal the ledger id",
        "`pending_delete` must differ from `attachment_id`",
        "never an id that does not come from the ledger entry",
    ):
        assert text in docs, text


def test_docs_link_rules(docs):
    for text in (
        "no query string, no fragment",
        "`<prefix>/api/v3/attachments/<id>/content`",
        "never match by file name",
        "equals the ledger `attachment_id`",
    ):
        assert text in docs, text


def test_docs_order_upload_before_delete_before_ledger(docs):
    step10 = docs[docs.index("10. **Documents.**") : docs.index("11. **Link paths.**")]
    assert (
        step10.index("upload first")
        < step10.index("Immediately after the confirmed upload write the ledger")
        < step10.index("delete the replaced attachment")
    )


def test_docs_append_rule_and_counts(docs):
    assert "the text before the block is never trimmed or changed" in docs
    assert "not as `replaced`" in docs
    assert "`Description: update` whenever any document is `new`, `changed` or `restored`" in docs
    assert "stop with an error if it does not increase" in docs


def test_docs_does_not_compare_the_project_display_name(docs):
    assert "display name, not its identifier" in docs
    assert "must equal `project` of the configuration" not in docs


# --- extension command: speckit.openproject.sync-version (feature 005) -----------------
# These tests are expected to fail (file missing / assertions red) until T012 creates
# extension/commands/sync-version.md. Test first, by design (tasks.md T011).

SYNC_VERSION_CAPABILITIES = {
    "list-versions",
    "get-version",
    "create-version",
    "get-work-package",
    "bulk-update-work-packages",
    "update-work-package",
}


@pytest.fixture(scope="module")
def sync_version(root):
    return (root / SYNC_VERSION_PROMPT).read_text()


def test_sync_version_embeds_exactly_its_capabilities(sync_version):
    ids = {row.split("|")[1].strip() for row in embedded_rows(sync_version)}
    assert ids == SYNC_VERSION_CAPABILITIES


def test_sync_version_has_no_delete_or_forbidden_rows(sync_version):
    assert "delete_" not in sync_version
    for forbidden in ("create-work-package", "delete-version", "update-version"):
        assert forbidden not in sync_version


def test_sync_version_decision_table_equals_reference(sync_version):
    lines = block(sync_version, "decision-table").splitlines()
    assert lines[0] == "| L | M | Action | Writes |"
    wp_header = next(i for i, line in enumerate(lines) if line.startswith("| W |"))
    version_rows = [line for line in lines[2:wp_header] if line.startswith("|")]
    wp_rows = [line for line in lines[wp_header + 2 :] if line.startswith("|")]
    assert version_rows == VERSION_DECISION_ROWS
    assert wp_rows == WORK_PACKAGE_DECISION_ROWS


def test_sync_version_safety_rules_present(sync_version):
    for text in (
        "untrusted data",
        "Dry run: nothing was written.",
        "<redacted-host>",
        "<redacted-secret>",
        "`complete`",
        "`incomplete`",
        "`no changes`",
        "`dry run`",
        "`stopped`",
    ):
        assert text in sync_version, text


# --- extension command: speckit.openproject.log-time (feature 005) ---------------------
# Same note as above: red until T012 creates extension/commands/log-time.md.

LOG_TIME_CAPABILITIES = {"list-time-activities", "create-time-entry", "get-work-package"}


@pytest.fixture(scope="module")
def log_time(root):
    return (root / LOG_TIME_PROMPT).read_text()


def test_log_time_embeds_exactly_its_capabilities(log_time):
    ids = {row.split("|")[1].strip() for row in embedded_rows(log_time)}
    assert ids == LOG_TIME_CAPABILITIES


def test_log_time_has_no_delete_or_forbidden_rows(log_time):
    assert "delete_" not in log_time
    for forbidden in ("create-work-package", "delete-version", "update-version"):
        assert forbidden not in log_time


def test_log_time_duration_grammar_lists_every_form(log_time):
    grammar = block(log_time, "duration-grammar")
    for form in ACCEPTED_DURATION_FORMS:
        assert f"`{form}`" in grammar, form
    for form in REJECTED_DURATION_FORMS:
        if form == "":
            assert "empty line" in grammar
        elif form == "<date in the future>":
            assert "date in the future" in grammar
        else:
            assert f"`{form}`" in grammar, form


def test_log_time_safety_rules_present(log_time):
    for text in (
        "untrusted data",
        "Dry run: nothing was written.",
        "<redacted-host>",
        "<redacted-secret>",
        "`complete`",
        "`incomplete`",
        "`no changes`",
        "`dry run`",
        "`stopped`",
    ):
        assert text in log_time, text


def test_log_time_skipped_lines_make_run_incomplete(log_time):
    assert "first matching rule wins" in log_time
    assert (
        "At least one line is `failed`, `stale`, `unknown` or `rejected` "
        "(even if every attempted write succeeded): `incomplete`."
    ) in log_time


def test_taskstoissues_caps_subject_length(root):
    text = (root / PROMPT).read_text()
    assert "at most 255 characters" in text
    assert "first 254 characters and append `…`" in text
    assert "never shortened" in text
