---
description: Locate and load the specifications.md sections relevant to a task before implementing. Use at the start of any non-trivial change.
allowed-tools: Read, Grep, Glob
argument-hint: [topic, e.g. "portfolio models" or "risk manager agent"]
---

The single source of truth is `specifications.md` (per CLAUDE.md). For the task described by `$ARGUMENTS`:

1. Read the Table of Contents at the top of `specifications.md` and identify the 1–3 sections that govern this task (e.g. "Database Schema", "Agent Tools", "Agent Definitions", "Backend API", "Frontend Application", "Testing Strategy", "Hard Constraints").
2. Read those sections in full — do not skim a couple of lines.
3. Cross-check `org_config.json` for the concrete names/paths/interfaces involved. If it disagrees with the spec, flag it and treat the spec as authoritative.
4. Summarize back: which sections apply, the exact models/paths/interfaces named, any hard constraints that bind this task, and any genuine ambiguity worth asking the human about before coding.

Do not propose or write code in this step — this is the explore/plan groundwork.
