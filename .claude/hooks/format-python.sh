#!/usr/bin/env bash
# PostToolUse hook (matcher: Write|Edit). Auto-formats and safe-fixes the single
# Python file that was just edited, so newly touched code stays clean without
# churning the rest of the repo. Best-effort and always non-blocking.
set -euo pipefail

path="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' 2>/dev/null || true)"
[ -z "$path" ] && exit 0
[[ "$path" == *.py ]] || exit 0
[ -f "$path" ] || exit 0

if command -v ruff >/dev/null 2>&1; then
  RUFF=(ruff)
elif python3 -m ruff --version >/dev/null 2>&1; then
  RUFF=(python3 -m ruff)
else
  exit 0
fi

"${RUFF[@]}" check --fix --quiet "$path" >/dev/null 2>&1 || true
"${RUFF[@]}" format --quiet "$path" >/dev/null 2>&1 || true
exit 0
