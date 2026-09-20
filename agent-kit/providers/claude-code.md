# Claude Code

## What it reads

| File | Loaded |
| --- | --- |
| `CLAUDE.md` (root) | every session |
| `backend/CLAUDE.md` and siblings | when Claude reads a file in that directory |
| `.claude/skills/<name>/SKILL.md` | descriptions always; body on invocation |
| `.claude/agents/*.md` | when delegating to a subagent |
| `.claude/settings.json` | at session start, after the workspace trust prompt |

**Claude Code does not read `AGENTS.md`.** Each `CLAUDE.md` is a heading plus an
`@AGENTS.md` import, which expands the matching `AGENTS.md` into context. That is why there
is one `CLAUDE.md` per directory that has an `AGENTS.md`.

A symlink would also work, but creating one on Windows needs Administrator rights or
Developer Mode, so the import is used instead.

## Skills

Skills are stubs pointing at `agent-kit/skills/`. The stub carries the frontmatter — which
is what Claude matches on when deciding whether a skill is relevant — and the body is one
line telling Claude to read the real playbook. Full content therefore stays out of context
until the skill actually runs.

`onboard` and `pre-pr-check` set `disable-model-invocation: true`, so only a human can
trigger them with `/onboard` and `/pre-pr-check`. The two `add-*` skills can also be picked
up by Claude on its own when the task matches.

## Hooks

`.claude/settings.json` registers two hooks, both running `scripts/agent-format-hook.mjs`:

- `PostToolUse` on `Edit|Write` — formats the edited file with black, Prettier + ESLint, or
  `cargo fmt` depending on its extension.
- `PreToolUse` on `Bash` — blocks `ruff format`.

Hooks are the only part of this setup that is enforced rather than advisory. Contributors
accept the workspace trust dialog once, per clone.

## Verifying it loaded

Run `/context` and check the **Memory files** list. Read a file under `backend/` and run it
again — `backend/CLAUDE.md` should now appear too.

## Personal overrides

`CLAUDE.local.md` and `.claude/settings.local.json` are gitignored. Use them for machine-
specific paths and preferences; never commit them.
