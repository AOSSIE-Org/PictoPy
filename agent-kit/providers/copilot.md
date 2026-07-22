# GitHub Copilot

## What it reads

- `.github/copilot-instructions.md` — a pointer to `AGENTS.md` plus the three rules that
  break builds most often.
- `AGENTS.md` in recent versions of Copilot's agent mode.

Copilot's instruction file is repository-wide; there is no per-directory equivalent, so the
nested `AGENTS.md` files are only picked up when Copilot follows the pointer. Keep
`.github/copilot-instructions.md` short and let it delegate — duplicating rules into it
creates a second copy that will drift.

## Limitations to be aware of

- **Inline completions ignore all of this.** Ghost-text suggestions are not instruction-
  aware, so they will happily suggest a `// TODO` comment that fails ESLint, or Python
  formatted at the wrong width. Review completions rather than accepting them blind.
- No skills support. The playbooks in `agent-kit/skills/` are still readable — point
  Copilot at the file directly when you want one.
- No hooks. Nothing auto-formats; run the gates in
  `agent-kit/skills/pre-pr-check/SKILL.md` before pushing.

## Notes

Copilot also reviews pull requests in some configurations. That is separate from
CodeRabbit, which this repository configures in `.coderabbit.yaml` and which runs on every
PR.
