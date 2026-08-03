---
name: onboard
description: Set up PictoPy for the first time and tour the codebase. Use when a contributor is new to the project, is setting up their environment, or asks where something lives.
disable-model-invocation: true
allowed-tools: Bash Read Grep Glob
---

# Onboard

Get a new contributor from a fresh clone to a running app, and orient them in the codebase.
Ask before running anything that installs or downloads.

## 1. Before any code

Tell the contributor the process rule up front, because it is the one that wastes the most
effort when missed:

> Do not open a PR for an issue that maintainers have not reviewed and labelled. Comment on
> the issue and wait for the green light first.

PRs target `main`, and the PR body must reference its issue as `#<number>`.

## 2. Prerequisites

Check what is already installed and report what is missing:

```bash
node --version
python --version
cargo --version
```

Node 18+, Python 3.11, and a Rust toolchain are all needed for a full build. A
frontend-only contributor can skip Python; a backend-only contributor can skip Rust.

## 3. Setup

Two supported paths:

- **Scripted** (Windows, Debian/Ubuntu, Fedora/RHEL) — `docs/Script_Setup_Guide.md`.
  From the repository root: `npm run setup`.
- **Manual** (everything else) — `docs/Manual_Setup_Guide.md`.

Python dependencies go into a virtualenv the contributor creates; none is committed. ONNX
models are **not** in the repository — `backend/app/utils/model_bootstrap.py` downloads them
at runtime on first use, so the first launch is slower and needs a network connection even
though the app itself is offline.

## 4. Running it

```bash
npm run win-dev     # Windows
npm run linux-dev   # Linux
```

These start the Python backend and the Tauri dev build together. The app window is the
frontend; the FastAPI sidecar runs behind it.

## 5. The four moving parts

| Part | Path | What it does |
| --- | --- | --- |
| UI | `frontend/src` | React 19, Redux Toolkit, Tailwind v4, shadcn/ui |
| Desktop shell | `frontend/src-tauri` | Rust, Tauri v2 — packaging, OS integration, commands |
| Backend | `backend` | FastAPI sidecar, SQLite, ONNX inference |
| Sync service | `sync-microservice` | Separate FastAPI service watching folders for changes |

The UI talks to the backend over HTTP through `frontend/src/api/`, and to the Rust shell
through Tauri `invoke` calls. Those are two different channels — knowing which one a
feature needs is usually the first design question.

## 6. Where things live

Backend features are four layers deep: `routes/` → `schemas/` → `database/` → `utils/`,
all under `backend/app/`. Frontend features are `features/` (state), `api/` (data),
`hooks/`, and `components/`, all under `frontend/src/`.

Read `backend/AGENTS.md` and `frontend/AGENTS.md` for the conventions in each.

## 7. Two rules that break builds

- Format Python with **black** at 88 columns. **Never `ruff format`** — Ruff is configured
  here at 300 columns and would reflow the entire codebase.
- **Never write `TODO` or `FIXME` comments.** ESLint fails the build on them.

## 8. Before the first PR

Run `/pre-pr-check`, or work through `agent-kit/skills/pre-pr-check/SKILL.md`. It runs
every gate CI runs, so nothing is a surprise on the PR.

Finish by asking what the contributor wants to work on, and point them at the relevant
area's `AGENTS.md`.
