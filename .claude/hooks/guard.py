#!/usr/bin/env python3
"""PreToolUse guard: block writes to secret files and obvious token leaks (exit 2 = block)."""

import json
import re
import sys

try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool = data.get("tool_name", "")
inp = data.get("tool_input", {}) or {}

SECRET_PATH = re.compile(r"(^|/)\.env($|\.(?!example$))|(^|/)(id_rsa|.*\.pem|.*\.key)$")
TOKEN_TEXT = re.compile(r"OPENPROJECT_API_TOKEN\s*=\s*['\"]?[A-Za-z0-9_\-]{16,}")


def block(msg):
    print(f"BLOCKED by .claude/hooks/guard.py: {msg}", file=sys.stderr)
    sys.exit(2)


path = inp.get("file_path", "")
if path and SECRET_PATH.search(path):
    block(f"{path} is a secret file. Tokens belong in the MCP client config, not in the repo.")

text = " ".join(str(inp.get(k, "")) for k in ("content", "new_string", "command"))
if TOKEN_TEXT.search(text):
    block("text looks like it contains an OpenProject API token.")
sys.exit(0)
