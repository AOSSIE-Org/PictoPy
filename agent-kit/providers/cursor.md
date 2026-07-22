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

- No hooks equivalent, so nothing auto-formats. Run the gates in
  `agent-kit/skills/pre-pr-check/SKILL.md` before pushing.
- Cursor's shadcn integration may want to write into `frontend/src/components/ui/`. That
  directory is generated — regenerate rather than hand-editing, and never commit ad-hoc
  edits there.
