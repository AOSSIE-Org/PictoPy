---
name: pre-pr-check
description: Run every gate CI runs, before opening a PR. Use before pushing, before opening a pull request, or when asked to verify a change is ready.
disable-model-invocation: true
allowed-tools: Bash Read Grep Glob
---

# Pre-PR check

Run the same checks CI runs, in the same order, and report each one. Do not stop at the
first failure — run everything, then summarise, so the contributor sees the full picture in
one pass.

`agent-kit/references/ci-gates.md` documents which workflow job each gate comes from. If
you change this list, change that file too.

## 1. Scope

Find what changed:

```bash
git diff --name-only origin/main...HEAD
```

Skip gates for areas the diff does not touch, and say which ones you skipped and why. A
docs-only change does not need `cargo test`.

## 2. Markdown

Runs on every `.md` in the repository regardless of what changed.

```bash
npx markdownlint-cli2 --config .github/.markdownlint-cli2.jsonc
```

Errors from paths inside local virtualenvs (`.env/`, `.docs-env/`, `.sync-env/`,
`site-packages/`) are pre-existing noise, not caused by the change. Ignore them and say so.

## 3. Agent hook tests

Only needed if the diff touches `scripts/agent-format-hook*.mjs`, but it is fast and needs
no dependencies.

```bash
node scripts/agent-format-hook.test.mjs
```

## 4. Frontend

Every command below runs from the repository root. Each `cd` is wrapped in a subshell so it
does not leak into the next command.

```bash
(cd frontend && npm run lint:check)
(cd frontend && npm run format:check)
(cd frontend && npm test)
```

`lint:check` runs with `--max-warnings 0`. The most common failure by far is a leftover
`TODO` or `FIXME` comment, which `no-warning-comments` treats as an error. If you see one,
remove it — do not disable the rule.

If `format:check` fails, fix it with `cd frontend && npm run format:fix` rather than editing
by hand.

## 5. Python

Covers both `backend/` and `sync-microservice/`.

```bash
pre-commit run --config .pre-commit-config.yaml --all-files
(cd backend && pytest)
```

If the black hook reformats files, that is a pass with changes — re-stage them. **Never**
resolve a formatting disagreement by running `ruff format`; Ruff is configured at 300
columns here and would reflow the entire codebase.

## 6. Rust

```bash
(cd frontend/src-tauri && cargo fmt -- --check)
(cd frontend/src-tauri && cargo test)
```

If the format check fails, run `cargo fmt` without `--check` to fix it.

## 7. Repository consistency

- If `git diff` touches any of `package.json`, `frontend/package.json`, or
  `frontend/src-tauri/Cargo.toml`, confirm all three versions still match. They must only
  change via `npm run version:bump -- X.Y.Z`.
- If any file under `agent-kit/skills/` changed, confirm the matching stubs exist at
  `.claude/skills/<name>/SKILL.md` and `.agents/skills/<name>/SKILL.md`, and that the
  `description` in each stub matches the playbook's. This is the one place the stub layout
  can silently rot.

## 8. Pull request readiness

- The PR body must reference its issue as `#<number>` — `linked-issue.yml` copies labels
  from the linked issue onto the PR.
- Confirm the issue was reviewed and labelled by a maintainer. PictoPy asks contributors
  not to open PRs against unlabelled issues.
- PRs target `main`.

## Report

Finish with a table: gate, status, and for failures the exact command to reproduce. State
plainly whether the change is ready to push. If something failed, do not describe it as
ready.
