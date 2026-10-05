"""The installed command is self-contained: its embedded blocks must match the repo sources."""

import json
import re

import pytest

PROMPT = "preset/commands/speckit.taskstoissues.md"


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


def j(keys):
    return ", ".join(sorted(keys))


def test_capability_block_matches_tool_map(root, prompt):
    expected = table_rows((root / "docs" / "mcp-tool-map.md").read_text())
    assert block(prompt, "capability-map").splitlines() == expected


def test_prompt_uses_no_tool_name_outside_capability_block(root, prompt):
    outside = re.sub(
        r"<!-- BEGIN capability-map -->.*?<!-- END capability-map -->", "", prompt, flags=re.DOTALL
    )
    rows = table_rows((root / "docs" / "mcp-tool-map.md").read_text())[2:]
    for row in rows:
        tool = re.search(r"`([a-z_]+)`", row).group(1)
        assert tool not in outside, f"tool name {tool} used outside the capability block"


def test_config_rules_match_schema(root, prompt):
    cfg = json.loads((root / "schemas/config.schema.json").read_text())
    rules = block(prompt, "config-rules")
    expected = [
        f"- top-level keys: {j(cfg['properties'])}",
        f"- required top-level keys: {j(cfg['required'])}",
        f"- types keys: {j(cfg['properties']['types']['properties'])}",
        f"- required types keys: {j(cfg['properties']['types']['required'])}",
        f"- defaults keys: {j(cfg['properties']['defaults']['properties'])}",
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
    files = list((root / "preset" / "commands").rglob("*"))
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


def test_config_value_types_match_schema(root, prompt):
    cfg = json.loads((root / "schemas/config.schema.json").read_text())
    props = cfg["properties"]
    rules = block(prompt, "config-rules")
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
