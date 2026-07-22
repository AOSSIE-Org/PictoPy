# Codex CLI

## What it reads

- `AGENTS.md` natively, at the root and in subdirectories. No adapter file needed.
- `.agents/skills/<name>/SKILL.md` — the same stubs Claude Code uses, copied into the
  cross-agent skills directory.

Resolution is by proximity: the `AGENTS.md` nearest the file being edited wins, with the
root file applying everywhere else. Explicit instructions in chat override both.

## Skills

`.agents/skills/` is the project-level path shared by Codex, Cursor, and Gemini CLI. The
stubs there are byte-identical to the ones in `.claude/skills/`; both point at
`agent-kit/skills/`.

`npx skills add <owner>/<repo>` installs into this directory. See
`agent-kit/references/third-party-skills.md` before adopting anything.

## Notes

- Codex has no equivalent of Claude Code's hooks, so the automatic formatting does not
  apply. Run the checks in `agent-kit/skills/pre-pr-check/SKILL.md` manually before
  pushing — especially `pre-commit`, since nothing will have reformatted Python for you.
- `disable-model-invocation` and `allowed-tools` in the stub frontmatter are Claude Code
  extensions. Codex ignores them harmlessly.
