#!/usr/bin/env python3
"""PostToolUse: syntax-check edited YAML/JSON files; feedback to Claude on exit 2."""

import json
import sys

try:
    data = json.load(sys.stdin)
    path = (data.get("tool_input") or {}).get("file_path", "")
except Exception:
    sys.exit(0)

try:
    if path.endswith(".json"):
        json.load(open(path))
    elif path.endswith((".yml", ".yaml")):
        try:
            import yaml
        except ImportError:
            sys.exit(0)
        yaml.safe_load(open(path))
except FileNotFoundError:
    sys.exit(0)
except Exception as exc:
    print(f"Syntax error in {path}: {exc}", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
