# agent-kit

Reusable knowledge for AI coding agents working on PictoPy.

`AGENTS.md` files hold the project's **rules** — facts every session needs, loaded into
context every time. This directory holds everything else: procedures, reference material,
templates, and provider notes, loaded only when they are actually needed.

The rule for deciding where something goes:

| It is… | Put it in |
| --- | --- |
| a fact every session needs | the nearest `AGENTS.md` |
| a multi-step procedure | `agent-kit/skills/<name>/SKILL.md` |
| detail a procedure cites | `agent-kit/references/` |
| a skeleton to copy and adapt | `agent-kit/templates/` |
| specific to one AI tool | `agent-kit/providers/` |

If you are about to add a numbered list of steps to an `AGENTS.md`, it belongs here
instead.

## Contents

### `skills/`

Playbooks in the [Agent Skills](https://agentskills.io) `SKILL.md` format, which works
unmodified across Claude Code, Cursor, Codex, and Gemini CLI.

- `onboard/` — first-time setup and a tour of the codebase
- `add-backend-endpoint/` — scaffold a FastAPI endpoint end to end
- `add-frontend-feature/` — scaffold a slice, API wrapper, hook, component, and test
- `pre-pr-check/` — run every gate CI runs, in CI's order

No tool scans this directory. Each playbook has a short stub in `.claude/skills/<name>/`
(Claude Code) and `.agents/skills/<name>/` (Codex, Cursor, Gemini CLI) that carries the
frontmatter and points here. That keeps the always-loaded index tiny while the full
playbook loads on demand.

### `references/`

Detail that playbooks cite rather than inline, so `SKILL.md` files stay short:

- `backend-endpoint-walkthrough.md` — the `videos` resource traced through all four layers
- `frontend-feature-walkthrough.md` — the video feature traced from slice to component
- `ci-gates.md` — every CI check, what it runs, and how to reproduce it locally
- `third-party-skills.md` — provenance for skills adopted from the ecosystem

### `templates/`

Annotated skeletons for a route, a database module, a Redux slice, and a component test.
Copy and adapt rather than writing from memory.

### `providers/`

Short notes on how each AI tool reads this repository's configuration, and tool-specific
gotchas. Notes only — never copies of the playbooks, which are already portable.

## Adding a playbook

1. Write `agent-kit/skills/<name>/SKILL.md` with `name` and `description` frontmatter.
   Keep it under 500 lines; push detail into `references/`.
2. Create the two stubs, both carrying the same frontmatter and a one-line pointer here:
   `.claude/skills/<name>/SKILL.md` and `.agents/skills/<name>/SKILL.md`.
3. List it in this README and in `CLAUDE.md` if it is worth invoking directly.

`pre-pr-check` verifies that every playbook has matching stubs, so drift is caught
mechanically.

## Adopting a third-party skill

```bash
npx skills add <owner>/<repo>
```

This installs into `.claude/skills/` or `.agents/skills/` and stays updatable with
`npx skills update`. Leave it where the installer put it — moving it here breaks updates —
and record what you adopted and why in `references/third-party-skills.md`.
