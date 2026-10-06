"""The installed command is self-contained: its embedded blocks must match the repo sources."""

import itertools
import json
import re

import jsonschema
import pytest
import yaml
from sync_reference import DECISION_ROWS

PROMPT = "preset/commands/speckit.taskstoissues.md"
EXTENSION_PROMPT = "extension/commands/discover-fields.md"
SYNC_PROMPT = "extension/commands/sync-status.md"
# Prompts that embed capability rows and config rules.
PROMPTS = [PROMPT, EXTENSION_PROMPT, SYNC_PROMPT]


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
        assert tool not in outside, f"tool name {tool} used outside the capability block"


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
    assert not any(
        row.split("|")[1].strip().startswith("delete")
        for row in table_rows((root / "docs" / "mcp-tool-map.md").read_text())[2:]
    )


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


@pytest.mark.parametrize("path", [PROMPT, SYNC_PROMPT])
def test_ledger_rules_match_schema_and_include_assignee(root, path):
    led = json.loads((root / "schemas/mapping.schema.json").read_text())
    item = led["properties"]["items"]["additionalProperties"]
    rules = block((root / path).read_text(), "ledger-rules").splitlines()
    assert f"- ledger item keys: {j(item['properties'])}" in rules
    assert "- ledger item keys: assignee, hash, id, kind, status, url" in rules
    assert "- ledger assignee: non-empty string (never written by this command)" in rules or (
        "- ledger assignee: non-empty string" in rules
    )
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
