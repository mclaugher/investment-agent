#!/usr/bin/env bash
# PreToolUse hook (matcher: Bash). Vetoes dangerous shell commands and access
# to secret files. Reads the tool-call JSON on stdin; `exit 2` blocks the call
# and feeds the stderr message back to Claude. `exit 0` allows it.
set -euo pipefail

cmd="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("command",""))' 2>/dev/null || true)"
[ -z "$cmd" ] && exit 0

block() { echo "BLOCKED by guard-bash hook: $1" >&2; exit 2; }

# Recursive + forced rm aimed at a broad or sensitive path.
if printf '%s' "$cmd" | grep -Eq '\brm\b' \
   && printf '%s' "$cmd" | grep -Eq -- '-[a-zA-Z]*r' \
   && printf '%s' "$cmd" | grep -Eq -- '-[a-zA-Z]*f'; then
  if printf '%s' "$cmd" | grep -Eq '(^|[[:space:]])(/|~|\$HOME|/\*|\*|/etc|/var|/usr|/home|\.\.)'; then
    block "recursive/forced rm targeting a broad or sensitive path. Delete a specific subdirectory instead, or ask the human."
  fi
fi

# Force pushes — protect shared history. Use --force-with-lease on a feature branch if you truly must.
if printf '%s' "$cmd" | grep -Eq 'git[[:space:]].*\bpush\b' \
   && printf '%s' "$cmd" | grep -Eq -- '(--force([[:space:]]|=|$)|[[:space:]]-f([[:space:]]|$))'; then
  block "git force-push. Push normally to the feature branch, or ask the human before rewriting remote history."
fi

# Reading/copying a real .env secret file via the shell (the .env.example template is fine).
if printf '%s' "$cmd" | grep -Eq '(cat|less|more|head|tail|cp|mv|scp|rsync|nano|vim|vi|emacs|strings|xxd|od|grep)[[:space:]][^|;&]*\.env([[:space:]]|$|\.local|\.prod|\.production)' \
   && ! printf '%s' "$cmd" | grep -Eq '\.env\.(example|sample|template)'; then
  block "access to a .env secret file. Use .env.example for structure; never read real credentials."
fi

exit 0
