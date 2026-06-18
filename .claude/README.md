# `.claude/` — Superhuman Alpha Fund coding factory

Infrastructure that keeps Claude Code's context lean, its feedback loops closed,
and its non-negotiables enforced deterministically. Everything here is checked
into the repo so it travels with the codebase and the team.

## Layout

```
.claude/
├── settings.json        # permissions (allow/deny) + hook wiring
├── hooks/               # deterministic shell hooks (enforcement)
│   ├── guard-bash.sh        PreToolUse(Bash): block rm -rf of broad paths, force-push, .env access
│   ├── protect-secrets.sh   PreToolUse(Read|Edit|Write): block secret/credential files
│   ├── format-python.sh     PostToolUse(Write|Edit): ruff format+fix the edited .py
│   ├── format-frontend.sh   PostToolUse(Write|Edit): eslint --fix the edited TS/JS
│   └── session-start.sh     SessionStart: inject a lean primer (spec, verify cmds, hard constraints)
├── commands/            # slash commands (repeatable workflows)
│   ├── check.md             /check — run the full verification suite
│   ├── spec.md              /spec <topic> — load governing specifications.md sections
│   ├── pr-description.md     /pr-description — draft a PR body from the real diff
│   └── changelog.md          /changelog — changelog from commits
├── agents/              # read-only subagents (context firewalls)
│   ├── spec-explorer.md     map a task onto the spec + code (haiku, fast)
│   └── code-reviewer.md     fresh-eyes diff review against explicit criteria
└── skills/              # vendored 3rd-party skills (see ATTRIBUTION.md)
    └── ...                  Matt Pocock's "Skills For Real Engineers" (MIT)
```

## Vendored skills (`skills/`)

The 17 folders under `.claude/skills/` are Matt Pocock's
[`mattpocock/skills`](https://github.com/mattpocock/skills) plugin set, vendored
in (MIT — see `skills/ATTRIBUTION.md`). Highlights: `/tdd`, `/diagnosing-bugs`,
`/grilling` (stress-test a plan), `/triage`, `/to-prd`, `/to-issues`,
`/domain-modeling`, `/codebase-design`. **Run `/setup-matt-pocock-skills` once**
to wire up the issue tracker + doc layout the engineering skills expect.

## Design principles (why it's shaped this way)

- **`CLAUDE.md` advises; hooks enforce.** Anything that must always hold (no
  secret reads, no destructive commands, auto-format on edit) is a hook, because
  hooks can't be forgotten or compacted away.
- **Permissions unlock flow.** The allow-list covers the safe, high-frequency
  95% (read/grep, `git status|diff|log`, `pytest`, `npm run build|lint`, `ruff`)
  so Claude runs unattended; the deny-list + hooks stop the genuinely dangerous.
- **Correctness gates are hard; style is advisory.** Tests and the frontend
  build fail CI; ruff/eslint report but don't block while the legacy code is
  brought into line. New/edited files are auto-formatted so the gap shrinks.
- **Subagents are read-only.** They isolate search noise from the main thread
  and can't handle approval prompts, so edits happen in the main session.

## Conventions for extending this

- New always-true preference → a lean line in `CLAUDE.md`.
- New repeatable workflow → a command in `.claude/commands/`.
- New non-negotiable → a hook in `.claude/hooks/` (and wire it in `settings.json`).
- Keep hooks fast and non-blocking unless they are a true veto (`exit 2`).
