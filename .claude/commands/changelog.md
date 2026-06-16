---
description: Generate a human-readable changelog entry from commits since a ref or tag.
allowed-tools: Bash(git log:*), Bash(git tag:*), Bash(git diff:*), Read
argument-hint: [since ref/tag, default: last tag or main]
---

Range start: `$ARGUMENTS` (if empty, use the most recent tag from `git tag --sort=-creatordate | head -1`, or `main` if there are no tags).

1. Collect commits: `git log <start>..HEAD --oneline --no-merges`.
2. Group them under **Added / Changed / Fixed / Removed / Infra**. Translate terse commit subjects into clear, user-facing one-liners; drop noise (formatting-only, merge churn).
3. Where a change maps to a `specifications.md` area (agents, tools, API, frontend, schema), name it so reviewers can trace it.
4. Output a dated markdown block ready to paste into `CHANGELOG.md`. Do not invent entries that aren't backed by a commit.
