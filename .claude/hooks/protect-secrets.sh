#!/usr/bin/env bash
# PreToolUse hook (matcher: Read|Edit|Write). Blocks reads/writes of secret and
# credential files. `exit 2` vetoes the call; `exit 0` allows it.
set -euo pipefail

path="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' 2>/dev/null || true)"
[ -z "$path" ] && exit 0

# Allow the committed templates explicitly.
case "$path" in
  *.env.example|*.env.sample|*.env.template) exit 0 ;;
esac

case "$path" in
  *.env|*/.env|*.env.local|*.env.*|*/secrets/*|*/.secrets/*|*id_rsa*|*id_ed25519*|*.pem|*.p12|*.pfx|*.key)
    echo "BLOCKED by protect-secrets hook: '$path' looks like a secret/credential file. Refer to .env.example for structure instead." >&2
    exit 2 ;;
esac

exit 0
