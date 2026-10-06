import json

import jsonschema
import pytest
import yaml


def schema(root, name):
    return json.loads((root / "schemas" / name).read_text())


def test_preset_config_template_matches_schema(root):
    cfg = yaml.safe_load((root / "preset" / "openproject-config.template.yml").read_text())
    jsonschema.validate(cfg, schema(root, "config.schema.json"))


def fixtures(root, sub, pattern):
    return sorted((root / "tests" / "fixtures" / sub).glob(pattern))


def test_fixture_sets_not_empty(root):
    assert fixtures(root, "config", "valid-*.yml")
    assert fixtures(root, "config", "invalid-*.yml")
    assert fixtures(root, "mapping", "valid-*.json")
    assert fixtures(root, "mapping", "invalid-*.json")


def test_config_fixtures(root):
    s = schema(root, "config.schema.json")
    for path in fixtures(root, "config", "valid-*.yml"):
        jsonschema.validate(yaml.safe_load(path.read_text()), s)
    for path in fixtures(root, "config", "invalid-*.yml"):
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(yaml.safe_load(path.read_text()), s)


def test_mapping_fixtures(root):
    s = schema(root, "mapping.schema.json")
    for path in fixtures(root, "mapping", "valid-*.json"):
        jsonschema.validate(json.loads(path.read_text()), s)
    for path in fixtures(root, "mapping", "invalid-*.json"):
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(json.loads(path.read_text()), s)


def test_s1_ledger_has_14_unique_items(root):
    data = json.loads((root / "tests/fixtures/mapping/valid-s1.json").read_text())
    ids = [item["id"] for item in data["items"].values()]
    assert len(ids) == 14
    assert len(set(ids)) == 14
    kinds = [item["kind"] for item in data["items"].values()]
    assert (kinds.count("feature"), kinds.count("phase"), kinds.count("task")) == (1, 3, 10)


def test_relations_reference_known_items(root):
    data = json.loads((root / "tests/fixtures/mapping/valid-with-relations.json").read_text())
    for rel in data["relations"]:
        assert rel["from"] in data["items"]
        assert rel["to"] in data["items"]


BASE_CONFIG = {
    "project": "p",
    "types": {"feature": "Feature", "phase": "Summary task", "task": "Task"},
}


@pytest.mark.parametrize(
    "statuses",
    [
        None,
        {},
        {"done": "Closed"},
        {"open": "New", "in_progress": "In progress", "done": "Closed"},
    ],
)
def test_statuses_optional_and_partial(root, statuses):
    cfg = dict(BASE_CONFIG)
    if statuses is not None:
        cfg["statuses"] = statuses
    jsonschema.validate(cfg, schema(root, "config.schema.json"))


@pytest.mark.parametrize("statuses", [{"blocked": "On hold"}, {"done": ""}, {"open": 1}])
def test_statuses_rejects_unknown_key_and_bad_values(root, statuses):
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            {**BASE_CONFIG, "statuses": statuses}, schema(root, "config.schema.json")
        )


def test_statuses_is_additive(root):
    s = schema(root, "config.schema.json")
    assert "statuses" not in s["required"]
    assert s["properties"]["statuses"]["additionalProperties"] is False


def test_hand_edited_fixture_validates_and_keeps_its_shape(root):
    path = root / "tests/fixtures/config/valid-hand-edited.yml"
    text = path.read_text()
    cfg = yaml.safe_load(text)
    jsonschema.validate(cfg, schema(root, "config.schema.json"))
    assert cfg["types"]["phase"] == "Task: v2 #1"
    assert cfg["create_relations"] is False
    assert "# my sandbox" in text
    assert "project:   " in text


def test_assignee_is_an_optional_non_empty_string(root):
    item = schema(root, "mapping.schema.json")["properties"]["items"]["additionalProperties"]
    assert "assignee" not in item["required"]
    assert item["properties"]["assignee"]["type"] == "string"
    assert item["properties"]["assignee"]["minLength"] == 1


def test_assignee_fixtures(root):
    s = schema(root, "mapping.schema.json")
    ok = json.loads((root / "tests/fixtures/mapping/valid-with-assignee.json").read_text())
    jsonschema.validate(ok, s)
    assert ok["items"]["T001"]["assignee"] == "Ada Example"
    for name in ("invalid-assignee-type", "invalid-assignee-empty"):
        bad = json.loads((root / f"tests/fixtures/mapping/{name}.json").read_text())
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(bad, s)


def test_documents_is_optional_and_closed(root):
    led = schema(root, "mapping.schema.json")
    assert "documents" not in led["required"]
    docs = led["properties"]["documents"]
    assert docs["propertyNames"]["enum"] == ["spec.md", "plan.md", "research.md", "data-model.md"]
    entry = docs["additionalProperties"]
    assert entry["required"] == ["hash", "attachment_id", "synced"]
    assert entry["additionalProperties"] is False
    assert led["properties"]["schema_version"]["const"] == "1.0"


def test_documents_fixtures(root):
    s = schema(root, "mapping.schema.json")
    ok = json.loads((root / "tests/fixtures/mapping/valid-with-documents.json").read_text())
    jsonschema.validate(ok, s)
    assert ok["documents"]["plan.md"]["pending_delete"] == 5
    for name in (
        "invalid-documents-unknown-name",
        "invalid-documents-hash",
        "invalid-documents-missing-id",
    ):
        bad = json.loads((root / f"tests/fixtures/mapping/{name}.json").read_text())
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(bad, s)
