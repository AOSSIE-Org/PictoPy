# Contributing with AI coding agents

Most contributors now use an AI coding agent — Claude Code, Cursor, GitHub Copilot, Codex,
Gemini CLI. PictoPy ships committed configuration so those agents already know the
project's conventions when you clone the repository. You do not need to paste instructions
into chat.

This page explains what the configuration is, and how to extend it.

## What is committed

| File or directory | Purpose | Read by |
| --- | --- | --- |
| `AGENTS.md` (root) | Project rules — architecture, commands, conventions, workflow | Codex, Cursor, Copilot, Gemini CLI, Windsurf, Aider, Devin, Jules |
| `backend/AGENTS.md` and siblings | Area-specific rules, loaded when the agent works in that directory | as above |
| `CLAUDE.md` files | One-line bridges that import the matching `AGENTS.md` | Claude Code |
| `agent-kit/` | Reusable knowledge — playbooks, references, templates, provider notes | on demand |
| `.claude/skills/`, `.agents/skills/` | Short stubs that point at `agent-kit/skills/` | Claude Code / everything else |
| `.claude/settings.json` | Hooks that auto-format edited files | Claude Code |
| `.github/copilot-instructions.md`, `.cursor/rules/` | Pointers to `AGENTS.md` | Copilot, Cursor |

Claude Code does not read `AGENTS.md`, which is why the `CLAUDE.md` bridges exist. They
contain a single `@AGENTS.md` import, so there is exactly one copy of every rule.

## The two layers

The split matters, and it is the rule to follow when you add anything:

**`AGENTS.md` is for facts every session needs.** Build commands, naming conventions,
formatting rules, the contribution workflow. These load into the agent's context at the
start of every session, so they cost tokens every time. Keep each file under 200 lines.

**`agent-kit/` is for procedures and reference material.** "How to add a backend endpoint"
is seven steps across four files — that is a playbook, not a fact. It loads only when it is
actually needed, so it costs nothing the rest of the time.

If you are about to add a numbered list of steps to an `AGENTS.md`, it belongs in
`agent-kit/` instead.

## Using the playbooks

In Claude Code, type `/` and pick one:

- `/onboard` — setup and a tour of the codebase
- `/add-backend-endpoint` — scaffold a FastAPI endpoint end to end
- `/add-frontend-feature` — scaffold a slice, API wrapper, hook, component, and test
- `/pre-pr-check` — run every gate CI runs, before you push

In other tools, the same playbooks are in `agent-kit/skills/` — point your agent at the
relevant file, or let it find them through `agent-kit/README.md`.

## Adding a rule

1. Decide which layer it belongs to (see above).
2. For a rule: add it to the **nearest** `AGENTS.md`, not the root one, unless it genuinely
   applies everywhere.
3. For a procedure: add `agent-kit/skills/<name>/SKILL.md`, then add the matching stubs in
   `.claude/skills/<name>/` and `.agents/skills/<name>/` so tools can discover it.
4. Write rules that are concrete enough to check. "Use 2-space indentation" works;
   "format code properly" does not.

## Adopting a third-party skill

The agent-skills ecosystem publishes installable skills, for example:

```bash
npx skills add shadcn/ui
```

This installs into `.claude/skills/` or `.agents/skills/` and stays updatable in place with
`npx skills update`. **Leave it where the installer put it** — moving it into `agent-kit/`
breaks updates. Record what you adopted and why in
`agent-kit/references/third-party-skills.md`.

## Keeping it from rotting

Stale instructions are worse than none, because agents follow them confidently.

- Change a CI gate → update `agent-kit/skills/pre-pr-check/` and
  `agent-kit/references/ci-gates.md`.
- Change a convention → update the nearest `AGENTS.md`.
- Change a playbook → check its stubs still describe it accurately.

`/pre-pr-check` verifies the stubs match their playbooks, so drift there is caught
mechanically.

## Reviewing AI-written code

The configuration improves the odds; it does not guarantee correctness. You are still the
author of every line you submit. Read the diff before you open the PR, and remember that
maintainers review contributions, not prompts.
