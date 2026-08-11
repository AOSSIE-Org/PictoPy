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

`npx skills@1.5.21 add <owner>/<repo>#<reviewed-tag-or-commit>` installs into this
directory. See `agent-kit/references/third-party-skills.md` before adopting anything.

## Notes

- Codex supports hooks of its own, through `hooks.json` or an inline `[hooks]` table in
  `config.toml`, but this repository does not wire any up. Only Claude Code gets the
  automatic formatting here, so unless you add equivalent hooks yourself, run the checks in
  `agent-kit/skills/pre-pr-check/SKILL.md` manually before pushing — especially
  `pre-commit`, since nothing will have reformatted Python for you.
- `disable-model-invocation` and `allowed-tools` in the stub frontmatter are Claude Code
  extensions. Codex ignores them harmlessly.
