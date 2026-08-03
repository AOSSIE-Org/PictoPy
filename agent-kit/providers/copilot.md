# GitHub Copilot

## What it reads

Copilot supports three custom-instruction formats, and which ones apply depends on the
surface you are using:

| Format | Location | Scope |
| --- | --- | --- |
| Repository-wide | `.github/copilot-instructions.md` | every surface |
| Path-specific | `.github/instructions/**/*.instructions.md`, with an `applyTo` glob | most IDEs, CLI, cloud agent and code review; not GitHub.com Chat |
| Agent files | `AGENTS.md`, including nested files | VS Code, Copilot CLI, cloud agent; varies elsewhere |

This repository uses the first and third. `.github/copilot-instructions.md` is a pointer to
`AGENTS.md` plus the rules that break builds most often; keep it short and let it delegate,
because duplicating rules into it creates a second copy that will drift.

We deliberately do **not** maintain `.github/instructions/*.instructions.md`. The nested
`AGENTS.md` files already provide per-directory scoping for every tool, and a parallel set
of Copilot-only path rules would be a second thing to keep in sync. On a surface that
resolves `AGENTS.md` natively, the nested files are picked up directly; on one that only
reads the repository-wide file, Copilot follows the pointer.

## Skills

Copilot loads project-level agent skills from `.github/skills/`, `.claude/skills/`, and
`.agents/skills/`. This repository already ships the last two, so **Copilot picks up the
same four playbooks with no extra configuration** — no `.github/skills/` copy is needed,
and adding one would be a third set of stubs to keep in sync.

Project skills are available in Copilot CLI, VS Code and JetBrains agent mode, the Copilot
app, the cloud agent, and Copilot code review. They are not available to inline
completions.

## Limitations to be aware of

- **Inline completions ignore all of this.** Ghost-text suggestions are not instruction-
  aware, so they will happily suggest a `// TODO` comment that fails ESLint, or Python
  formatted at the wrong width. Review completions rather than accepting them blind.
- Instruction support varies by surface. Visual Studio reads only the repository-wide
  file; GitHub.com Chat does not read path-specific instructions. If a rule seems to be
  ignored, check the **References** section of the Copilot response to see which
  instruction files were actually applied.
- This repository configures no Copilot hooks, so nothing auto-formats. Run the gates in
  `agent-kit/skills/pre-pr-check/SKILL.md` before pushing.

## Notes

Copilot also reviews pull requests in some configurations. That is separate from
CodeRabbit, which this repository configures in `.coderabbit.yaml` and which runs on every
PR.
