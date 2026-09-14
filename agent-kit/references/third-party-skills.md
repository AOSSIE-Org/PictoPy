# Third-party skills

Provenance for skills adopted from the agent-skills ecosystem. Nothing is adopted yet —
this file documents the process so the first adoption follows it.

## How to adopt one

```bash
npx skills@1.5.21 add <owner>/<repo>#<reviewed-tag-or-commit>
```

Both halves are pinned on purpose. `npx skills` on its own runs the latest published
release, and installing from a moving branch means the instructions an agent follows can
change after you reviewed them. Record the exact revision in the table below.

The installer writes into `.claude/skills/` (Claude Code) or `.agents/skills/` (Codex,
Cursor, Gemini CLI). **Leave it there.** Moving it into `agent-kit/skills/` breaks
`npx skills@1.5.21 update`, which matches on the install path.

That is the one exception to the rule that `agent-kit/` holds the canonical copy: vendored
skills stay where their installer manages them, and this file records what they are.

## Before adopting

A third-party skill is a set of instructions an agent will follow on this codebase. Read it
first.

- Does it contradict anything in our `AGENTS.md` files? Ours wins — either skip the skill
  or note the conflict below.
- Does it run commands? Check what they do.
- Is it maintained? An abandoned skill encoding an old API is worse than none.
- Which exact revision did you read? Install that tag or commit, not the default branch,
  and put it in the table. Re-reading is the only way to know an update is safe, so an
  update is a fresh review, not a version bump.

## Adopted skills

None yet.

When you add one, record it here:

| Skill | Source | Version/commit | Adopted | Why | Conflicts |
| --- | --- | --- | --- | --- | --- |
| example | `owner/repo` | `v1.2.0` | 2026-01-01 | what it gives us | none |

## Candidates

- **shadcn/ui** (`npx skills@1.5.21 add shadcn/ui#<reviewed-tag>`) — component generation
  guidance. Relevant
  because `frontend/src/components/ui/` is shadcn-generated and must not be hand-edited.
  Check it agrees with our Tailwind v4 setup before adopting.
