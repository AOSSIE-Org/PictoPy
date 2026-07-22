# Cursor

## What it reads

- `.cursor/rules/pictopy.mdc` — has `alwaysApply: true`, so it is in context for every
  request. It is a pointer, not a copy: it tells Cursor to follow `AGENTS.md`.
- `AGENTS.md` natively, at the root and in subdirectories.
- `.agents/skills/<name>/SKILL.md` — the cross-agent skill stubs.

The `.mdc` pointer exists because Cursor's own rules system is what users expect to find,
and an empty `.cursor/` directory reads as "this project has no conventions".

## Adding a Cursor-specific rule

Only add one if it genuinely cannot live in `AGENTS.md` — a Cursor UI behaviour, or a
workaround for something specific to it. Anything about the codebase itself belongs in
`AGENTS.md`, where every other tool can see it too.

Path-scoped rules use `globs` in the frontmatter:

```text
---
description: Rust-specific guidance
globs: ["frontend/src-tauri/**/*.rs"]
---
```

## Notes

- **This repository does not configure Cursor hooks**, so nothing auto-formats for you.
  Run the gates in `agent-kit/skills/pre-pr-check/SKILL.md` before pushing.

  Cursor does support them: `.cursor/hooks.json` (project) or `~/.cursor/hooks.json`
  (user), with lifecycle events including `afterFileEdit` and `beforeShellExecution`, and
  it can load third-party Claude Code hooks. Those two events line up with what
  `.claude/settings.json` already does — auto-format an edited file, and block the Ruff
  formatter — so `scripts/agent-format-hook.mjs` could be wired up for Cursor without
  changing the script. That is worth doing once the hook has proven itself in Claude Code;
  raise an issue if you want to take it on.
- Cursor's shadcn integration may want to write into `frontend/src/components/ui/`. That
  directory is generated — regenerate rather than hand-editing, and never commit ad-hoc
  edits there.
