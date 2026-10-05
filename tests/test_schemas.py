import json

import jsonschema
import pytest
import yaml


def schema(root, name):
    return json.loads((root / "schemas" / name).read_text())


def test_preset_config_template_matches_schema(root):
    cfg = yaml.safe_load((root / "preset" / "openproject-config.template.yml").read_text())
    jsonschema.validate(cfg, schema(root, "config.schema.json"))


def test_mapping_valid(root):
    data = json.loads((root / "tests/fixtures/mapping.valid.json").read_text())
    jsonschema.validate(data, schema(root, "mapping.schema.json"))


def test_mapping_invalid(root):
    data = json.loads((root / "tests/fixtures/mapping.invalid.json").read_text())
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(data, schema(root, "mapping.schema.json"))
