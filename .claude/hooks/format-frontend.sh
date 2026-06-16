#!/usr/bin/env bash
# PostToolUse hook (matcher: Write|Edit). Runs eslint --fix on the single
# frontend file just edited. Best-effort and always non-blocking; skips quietly
# if node_modules is not installed.
set -euo pipefail

path="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' 2>/dev/null || true)"
[ -z "$path" ] && exit 0
case "$path" in
  *.ts|*.tsx|*.js|*.jsx) ;;
  *) exit 0 ;;
esac
case "$path" in
  *"/frontend/"*) ;;
  *) exit 0 ;;
esac

cd "${CLAUDE_PROJECT_DIR:-.}/frontend" 2>/dev/null || exit 0
[ -d node_modules ] || exit 0
npx --no-install eslint --fix "$path" >/dev/null 2>&1 || true
exit 0
