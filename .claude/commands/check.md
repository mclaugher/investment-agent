---
description: Run the full verification suite (backend tests + lint, frontend build + lint) and report real results.
allowed-tools: Bash(cd:*), Bash(pytest:*), Bash(python -m pytest:*), Bash(ruff check:*), Bash(ruff format:*), Bash(npm run build:*), Bash(npm run lint:*), Bash(npm ci:*), Read, Grep
---

Run the project's verification gates and report **actual exit codes and output** — never claim success without the evidence. Run each step even if an earlier one fails, then give a single summary table (pass/fail per gate).

1. **Backend tests (hard gate):**
   `cd backend && pytest tests/test_tools tests/test_services tests/test_api -v`
2. **Backend agent tests (advisory — may need an API key/network):**
   `cd backend && pytest tests/test_agents -v -k "not slow"`
3. **Backend lint/format (advisory on legacy code; must pass for files you touched):**
   `cd backend && ruff check . && ruff format --check .`
4. **Frontend build (hard gate — runs tsc + vite):**
   `cd frontend && npm run build`  (run `npm ci` first if `node_modules` is missing)
5. **Frontend lint (advisory):**
   `cd frontend && npm run lint`

Report the failing test names / error lines verbatim. If a gate fails because of code you changed in this session, fix it and re-run. If it fails for a pre-existing/legacy reason, say so explicitly and do not paper over it.
