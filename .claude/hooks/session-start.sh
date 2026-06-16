#!/usr/bin/env bash
# SessionStart hook. Prints a lean primer that is injected as context at the
# start of every session (and after a compaction, where supported), keeping the
# non-negotiables in front of the model instead of trusting CLAUDE.md to hold.
set -euo pipefail

branch="$(git -C "${CLAUDE_PROJECT_DIR:-.}" branch --show-current 2>/dev/null || echo unknown)"

cat <<EOF
[Superhuman Alpha Fund — session primer]

Source of truth: specifications.md is authoritative (1700+ lines). Skim its TOC
and read the relevant sections BEFORE any non-trivial change. Quick name/path
lookups: org_config.json. If the two disagree, the spec wins — ask the human.

Current branch: ${branch}

Verify before claiming done (trust artifacts, not narration) — or just run /check:
  backend tests:  cd backend && pytest tests/test_tools tests/test_services tests/test_api -v
  backend lint:   cd backend && ruff check . && ruff format --check .
  frontend build: cd frontend && npm run build
  frontend lint:  cd frontend && npm run lint

HARD CONSTRAINTS (never violate, no exceptions):
  - No margin, no leverage, no short selling, no negative cash balance in any code path.
  - Enforce all risk limits and allocation rules in portfolio tools + CEO/Risk Manager agents.
  - Every trade decision must be backed by recorded analysis reports and decision trails in the DB.
EOF
exit 0
