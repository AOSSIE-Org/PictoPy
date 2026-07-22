# AGENTS.md

Instructions for AI coding agents working on PictoPy. Read this before making changes.

This file is the project's rules. Multi-step procedures (adding an endpoint, adding a
feature, pre-PR checks, onboarding) live in `agent-kit/` — see `agent-kit/README.md`.

More specific rules live in the nearest `AGENTS.md` to the file you are editing:
`backend/`, `frontend/`, `frontend/src-tauri/`, and `sync-microservice/` each have one.

## Project overview

PictoPy is an offline, privacy-first desktop photo manager. Nothing leaves the user's
machine; all AI runs on-device via ONNX.

Four moving parts:

- `frontend/src` — React 19 + TypeScript UI (Vite, Redux Toolkit, Tailwind v4, shadcn/ui)
- `frontend/src-tauri` — Rust shell (Tauri v2), packaging and OS integration
- `backend` — Python FastAPI sidecar, entry point `backend/main.py`, SQLite storage
- `sync-microservice` — a second, separate FastAPI service

ONNX models are downloaded at runtime by `backend/app/utils/model_bootstrap.py`. They are
not vendored in the repository.

## Commands

These are exactly what CI runs. Run the ones for the areas you touched.

| Task | Command |
| --- | --- |
| Frontend lint | `cd frontend && npm run lint:check` |
| Frontend format | `cd frontend && npm run format:fix` |
| Frontend tests | `cd frontend && npm test` |
| Backend tests | `cd backend && pytest` |
| Python lint + format | `pre-commit run --config .pre-commit-config.yaml --all-files` |
| Rust format | `cd frontend/src-tauri && cargo fmt` |
| Rust tests | `cd frontend/src-tauri && cargo test` |
| Version bump | `npm run version:bump -- X.Y.Z` |

Setup is scripted: see `docs/Script_Setup_Guide.md` (Windows, Debian, Fedora) or
`docs/Manual_Setup_Guide.md` (everything else).

## Rules that are not obvious from the code

These are the mistakes agents make most often in this repository.

### Never run `ruff format`

Format Python with **black** (88 columns). `backend/pyproject.toml` sets Ruff's
`line-length = 300`, so `ruff format` would reflow the entire codebase to 300 columns and
the black hook in `.pre-commit-config.yaml` would immediately fight it. Ruff is configured
here as a **linter only** — `ruff --fix` is fine, `ruff format` is not.

### Never write `TODO` or `FIXME` comments

`frontend/.eslintrc.json` sets `no-warning-comments` to `error` for those terms, and lint
runs with `--max-warnings 0`. A single leftover `// TODO` fails CI. If work is genuinely
incomplete, open an issue instead of leaving a marker in the code.

### Keep comments short

One or two lines, explaining *why* rather than *what*. The codebase does not use long
prose comment blocks or multi-paragraph docstrings. Match what is already there.

### Version strings are triplicated

`package.json`, `frontend/package.json`, and `frontend/src-tauri/Cargo.toml` must always
agree. Only ever change them through `npm run version:bump -- X.Y.Z`. `tauri.conf.json`
has no version field in Tauri v2 — it inherits from `Cargo.toml`.

### Do not edit generated or vendored paths

`dist/`, `target/`, `gen/`, `node_modules/`, `__pycache__/`, `.mypy_cache/`, `.ruff_cache/`,
`htmlcov/`, and `frontend/src/components/ui/` (shadcn-generated). Leave
`frontend/package-lock.json` alone unless you actually changed dependencies.

### Markdown is linted too

`markdownlint-cli2` runs over every `.md` in CI, configured by
`.github/.markdownlint-cli2.jsonc`. Line length (`MD013`) is off; duplicate headings are
allowed only among siblings.

## Contribution workflow

- **Do not open a PR for an issue that maintainers have not reviewed and labelled.** Wait
  for the green light. This is the project's most-enforced process rule.
- PRs target `main`.
- The PR body must reference its issue as `#<number>` — `.github/workflows/linked-issue.yml`
  copies labels from the linked issue onto the PR.
- CodeRabbit reviews every PR automatically (`.coderabbit.yaml`).
- Commit messages: short imperative subject prefixed `fix:`, `feat:`, `docs:`, or `test:`.

## Definition of done

A change is not finished until, for every area you touched, lint passes, formatting is
clean, and tests pass locally. Do not hand back work that only compiles.

The `pre-pr-check` playbook in `agent-kit/skills/pre-pr-check/` runs every gate CI runs, in
order. Use it before pushing.
