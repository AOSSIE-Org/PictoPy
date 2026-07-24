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

Run the ones for the areas you touched. CI runs the **check** column; use the **fix** column
locally so the check passes. Run everything from the repository root — the `cd` is wrapped in
a subshell so it does not leak into the next command.

| Task | Check (what CI runs) | Fix |
| --- | --- | --- |
| Frontend lint | `(cd frontend && npm run lint:check)` | `npm run lint:fix` |
| Frontend format | `(cd frontend && npm run format:check)` | `npm run format:fix` |
| Frontend tests | `(cd frontend && npm test)` | — |
| Python lint + format | `pre-commit run --config .pre-commit-config.yaml --all-files` | rewrites in place |
| Backend tests | `(cd backend && pytest)` | — |
| Rust format | `(cd frontend/src-tauri && cargo fmt -- --check)` | `cargo fmt` |
| Version bump | `npm run version:bump -- X.Y.Z` | — |

`cargo test` is not part of the PR check workflow, but run it for any `frontend/src-tauri/`
change. `agent-kit/references/ci-gates.md` maps every gate to the workflow job it comes from.

Setup is scripted: see `docs/Script_Setup_Guide.md` (Windows, Debian, Fedora) or
`docs/Manual_Setup_Guide.md` (everything else).

## Code quality

### Match the codebase before anything else

Before writing a new file, read the nearest existing file that does the same kind of job
and follow its structure, naming, and idiom. Consistency with what is already here beats
any general best practice. If you are about to introduce a pattern the codebase does not
use — a new state library, a different test style, a second way to call the API — don't;
extend the existing pattern, or raise it on the issue first.

### Reuse before adding

Search before you create. Adding a second component that does what an existing one already
does is the most common quality problem in this repository.

| Before adding a… | Search here first |
| --- | --- |
| UI primitive (button, dialog, input) | `frontend/src/components/ui/` — 27 already exist |
| Shared helper | `frontend/src/utils/`, `frontend/src/lib/utils.ts` |
| Hook | `frontend/src/hooks/` |
| Constant, route, or static list | `frontend/src/constants/` |
| Python helper | `backend/app/utils/` |

Extract shared code on the **third** occurrence, not the second — premature abstraction is
also a cost. When you do extract, put it in the directories above so the next person finds
it.

### Keep modules focused

One module, one job. A route file handles HTTP; business logic belongs in `app/utils/`, and
data access in `app/database/`. A component renders; data fetching belongs in a hook, and
derived data in a selector. If a file has grown past a few hundred lines it is usually doing
more than one job.

### Types are not optional

- **TypeScript**: `tsconfig.json` sets `strict`, `noUnusedLocals`, and `noUnusedParameters`,
  and `npm run build` runs `tsc`. Type every export and every API boundary. The codebase
  still has some `any` — do not add more, and do not use `as` to silence a real type error.
- **Python**: annotate function signatures and return types, as the existing modules do.
  Table rows are `TypedDict` classes, not bare dicts. There is no mypy gate in CI, so
  annotations are for the reader and for the next agent — write them accordingly.
- Frontend types must match the backend's Pydantic response model. The backend is the
  source of truth; check `backend/app/routes/` rather than guessing the shape.

### Comments explain why

One or two lines, explaining *why* rather than *what*. The codebase does not use long prose
comment blocks or multi-paragraph docstrings — match what is already there. A comment that
restates the code is noise; a comment that records a non-obvious reason is valuable.

Do not leave commented-out code. Delete it; git remembers.

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
