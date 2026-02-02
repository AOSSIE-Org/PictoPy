# Tauri + React + Typescript

This template should help get you started developing with Tauri, React and Typescript in Vite.

## Recommended IDE Setup

- [VS Code](https://code.visualstudio.com/) + [Tauri](https://marketplace.visualstudio.com/items?itemName=tauri-apps.tauri-vscode) + [rust-analyzer](https://marketplace.visualstudio.com/items?itemName=rust-lang.rust-analyzer)
## Getting Started

Follow these steps to run the frontend locally.

**Prerequisites**

- Node.js (LTS) installed (recommended v18+)
- npm, pnpm, or yarn
- If you plan to run the desktop app with Tauri: Rust toolchain (install via `rustup`) and Tauri prerequisites — see https://tauri.app/

**Install dependencies**

```bash
cd frontend
npm install
```

**Run the frontend development server**

```bash
npm run dev
```

**Run the desktop app (Tauri) in development**

```bash
npm run tauri dev
```

**Build & preview**

```bash
npm run build
npm run preview
```

**Useful scripts**

- `npm run test` — run tests
- `npm run lint:check` / `npm run lint:fix` — linting
- `npm run format:check` / `npm run format:fix` — formatting
- `npm run setup:linux` — run `scripts/setup_env.sh` to prepare the Linux dev environment

**Troubleshooting**

- If `npm run tauri dev` fails, ensure you have Rust and the required toolchain installed (see Tauri docs). If the dev server doesn't start, check for port conflicts or errors in the terminal.