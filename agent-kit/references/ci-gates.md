# CI gates

Every check that runs on a pull request, and how to reproduce it locally. Source of truth:
`.github/workflows/pr-check-tests.yml`. **If that workflow changes, change this file and
`agent-kit/skills/pre-pr-check/SKILL.md` with it.**

Workflow triggers on `pull_request` against `main`.

## Job: Linting

| Check | Local command |
| --- | --- |
| Markdown | `npx markdownlint-cli2 --config .github/.markdownlint-cli2.jsonc` |
| Frontend lint | `cd frontend && npm run lint:check` |
| Frontend format | `cd frontend && npm run format:check` |
| Python lint + format | `pre-commit run --config .pre-commit-config.yaml --all-files` |
| Agent hook tests | `node scripts/agent-format-hook.test.mjs` |
| Rust format | `cd frontend/src-tauri && cargo fmt -- --check` |

CI installs `pre-commit ruff black` and runs pre-commit from inside `backend/` with
`--config ../.pre-commit-config.yaml`. Running it from the repository root with
`--config .pre-commit-config.yaml` is equivalent and covers `sync-microservice/` too.

## Job: Frontend Tests

```bash
cd frontend && npm install && npm test
```

Jest with `jest.config.ts`. Node 18 on the runner.

## Job: Backend Tests

Three steps, and the two build checks fail more often than the tests do:

Each step runs in a subshell so the `cd` does not leak into the next one. Run them from the
repository root.

```bash
(cd backend && pip install -r requirements.txt && pyinstaller main.py --name PictoPy_Server --onedir --distpath dist)
(cd sync-microservice && pip install -r requirements.txt && pyinstaller main.py --name PictoPy_Sync_Microservice --onedir --distpath dist)
(cd backend && pytest)
```

The PyInstaller steps catch imports that work in development but break when frozen — a new
dependency that is imported dynamically will pass `pytest` and fail here. Python 3.11 on
the runner.

The agent hook tests cover the formatting hook's guard, its path exclusions, and the
entrypoint's exit codes. They need no dependencies, so the step runs before `npm install`.

## Not in this workflow

- `cargo test` is not run by `pr-check-tests.yml`, but `CONTRIBUTING.md` asks contributors
  to run it and `pr-check-build.yml` builds the Rust side. Run it for any `src-tauri/`
  change.
- CodeRabbit reviews every PR (`.coderabbit.yaml`), configured against `develop` as its
  base branch even though PR checks target `main`.
- `linked-issue.yml` copies labels from the issue referenced in the PR body onto the PR. A
  PR body without a `#<number>` reference gets no labels.

## Known local-only noise

`.github/.markdownlint-cli2.jsonc` excludes `node_modules`, `target`, `venv`, and `.venv`,
but not the virtualenv names this project's setup guides actually use — `.env`,
`.docs-env`, `.sync-env`. Running markdownlint locally therefore reports errors from
`site-packages` LICENSE files. CI is unaffected because a fresh checkout has no
virtualenvs. Ignore those paths; do not "fix" vendored files.
