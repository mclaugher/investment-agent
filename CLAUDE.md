# Superhuman Alpha Fund – Claude Code Instructions

You are configuring and extending **Superhuman Alpha Fund**, a multi-agent, fundamentals-driven investment analysis system.

Whenever you need a quick lookup of names, paths, or interfaces, first check `org_config.md`. If something disagrees with `specifications.md`, treat `specifications.md` as authoritative and ask the human to fix the config file. [file:37]


## Canonical specification

- The single source of truth for this project is `specifications.md` at the repo root.
- Before starting **any** non-trivial task, you must:
  1. Open `specifications.md`.
  2. Skim the Table of Contents.
  3. Read the sections relevant to the task.
- Do not contradict or “simplify” the spec. If something seems inconsistent, ask the human instead of guessing.

## General rules

- Follow the implementation order and architecture in `specifications.md`. Do **not** invent your own stack or structure.
- Do not change tech choices (Python 3.12, LangGraph, FastAPI, React+TS, PostgreSQL, ChromaDB, Celery, Redis, etc.). [file:37]
- Prefer small, reviewable diffs. When a task is large, propose a phased plan and wait for approval.

## Task workflow

For any new request:

1. Restate the task briefly.
2. Identify **which sections** of `specifications.md` apply (e.g., “Agent Tools”, “Agent Definitions”, “Backend API”, “Frontend Application”, “Testing Strategy”). [file:37]
3. Ask any clarifying questions if the spec leaves something ambiguous.
4. Propose a short plan with 2–5 steps, ordered according to the implementation order in the spec. [file:37]
5. Execute the plan step by step, showing file paths and key code snippets.

Always:

- Keep database models, APIs, agents, tools, and the frontend consistent with their respective subsections in `specifications.md`. [file:37]
- When adding or modifying code, cite the relevant spec section (e.g., “per §4.1 Portfolio Models, add `RiskProfile` fields…”). [file:37]
- Create or update tests as specified in the “Testing Strategy” and `tests/` layout. [file:37]

## Hard constraints from the spec

- No margin trading, no leverage, no short selling, and no negative cash balances in any code path. [file:37]
- Enforce all risk limits and allocation rules in portfolio tools and the CEO/Risk Manager agents. [file:37]
- Every trade decision must be backed by recorded analysis reports and decision trails in the database. [file:37]

If a user request conflicts with these rules, explain the conflict and propose a compliant alternative.

## Project structure reminder

The codebase must match the structure defined in `specifications.md` section “Project Structure”. [file:37]

Key roots:

- `backend/` – FastAPI app, models, services, agents (LangGraph), Celery tasks, tests.
- `frontend/` – React + TypeScript + Vite SPA with dashboard, agents, reports, chat, settings.
- `scripts/` – `seed_universe.py`, `setup_db.py`, `run_analysis.py`.

Do **not** create ad-hoc folders; extend only within this structure unless the human explicitly approves a change.

## Canonical “Build Superhuman Alpha Fund” workflow

When asked to “implement Superhuman Alpha Fund” or similar:

1. **Phase 1 – Backend foundations**
   - Create `backend/app/config.py`, `database.py`, and the SQLAlchemy models exactly as in “Database Schema”. [file:37]
   - Wire Alembic migrations and `scripts/setup_db.py` and `scripts/seed_universe.py`. [file:37]
   - Add unit tests under `tests/testservices` and `tests/testapi` as described. [file:37]

2. **Phase 2 – Agent tools and agents**
   - Implement tools in `backend/app/agents/tools/*.py` following “Agent Tools”. [file:37]
   - Implement sector teams, supervisors, CIO, Risk Manager, Macro, and CEO agents per “Agent Definitions” and “Agent Architecture”. [file:37]
   - Implement the orchestrator graph in `backend/app/agents/orchestrator.py` and its execution modes. [file:37]

3. **Phase 3 – Tasks, scheduling, and API**
   - Implement Celery tasks per “Data Ingestion & Scheduling”. [file:37]
   - Implement FastAPI routers in `backend/app/api/*.py` following “Backend API”. [file:37]
   - Implement WebSocket server endpoint and message schema. [file:37]

4. **Phase 4 – Frontend**
   - Scaffold the React + TypeScript frontend under `frontend/` according to “Frontend Application”. [file:37]
   - Implement dashboard, portfolio, agents, reports, chat, and settings pages and components specified. [file:37]

5. **Phase 5 – Testing and polish**
   - Ensure all tests described in “Testing Strategy” exist and pass. [file:37]
   - Add any missing wiring, error handling, and logging required by “Data Management Policies” and “Hard Constraints”. [file:37]

## Verification (close every task on an artifact, not a claim)

Before saying a change is done, run the relevant gate and report the real result. Or run `/check` to do all of it.

- Backend tests: `cd backend && pytest tests/test_tools tests/test_services tests/test_api -v`
- Backend lint/format (must pass for files you touch): `cd backend && ruff check . && ruff format --check .`
- Frontend build (runs `tsc` + `vite`): `cd frontend && npm run build`
- Frontend lint: `cd frontend && npm run lint`

Do not weaken or delete a test to make a failure pass. CI (`.github/workflows/ci.yml`) treats tests and the frontend build as hard gates; ruff and eslint are advisory while the legacy code is brought into line.

## Local tooling (`.claude/`)

- **Hooks** (enforced, not optional): edited `.py`/frontend files are auto-formatted; reads of `.env`/secrets and dangerous shell commands (`rm -rf` of broad paths, force-push) are blocked.
- **Commands:** `/check` (verify), `/spec <topic>` (load governing spec sections before coding), `/pr-description`, `/changelog`.
- **Subagents (read-only):** `spec-explorer` (map a task onto the spec + code) and `code-reviewer` (fresh-eyes diff review). Delegate fan-out exploration to keep the main thread clean; do edits in the main session.

For each phase, ask the human whether to proceed before making large changes.
