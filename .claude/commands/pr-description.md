---
description: Draft a PR description from the actual diff against the base branch — summary, spec sections touched, test evidence, risk.
allowed-tools: Bash(git diff:*), Bash(git log:*), Bash(git status:*), Bash(git branch:*), Read, Grep
argument-hint: [base branch, default: main]
---

Base branch: `$ARGUMENTS` (default to `main` if empty).

1. Inspect the real change set: `git diff <base>...HEAD --stat` then `git log <base>..HEAD --oneline` and a full `git diff <base>...HEAD` for the substantive files.
2. Write a PR description in this structure:
   - **Summary** — what changed and why, in 2–4 sentences.
   - **Spec alignment** — which `specifications.md` sections this implements/affects (cite section names), confirming no deviation from the spec or hard constraints (no margin/leverage/shorting/negative cash; decisions backed by recorded reports).
   - **Changes** — bulleted list grouped by area (backend models / agents / tools / API / frontend / tests / infra).
   - **Verification** — the exact commands run and their results (e.g. `pytest ... → 94 passed`). State plainly if something was not run.
   - **Risk & follow-ups** — anything reviewers should scrutinize.
3. Keep it factual and tied to the diff. Do not describe work that isn't in the diff.

Do NOT open a PR unless the human explicitly asks. Output the description as markdown for review.
