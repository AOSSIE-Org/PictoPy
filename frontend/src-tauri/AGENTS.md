# AGENTS.md — Tauri shell

Rules for the Rust side of the desktop app. The root `AGENTS.md` still applies.

## Layout

- `src/main.rs` — binary entry point, thin.
- `src/lib.rs` — the Tauri builder: plugins, state, and the `invoke_handler` where every
  command is registered.
- `src/services/` — the actual command implementations, grouped by concern.
- `capabilities/*.json` — permission scopes. A command the frontend can call must be
  permitted here or it fails at runtime, not at compile time.

## Adding a command

1. Implement it in `src/services/`, annotated `#[tauri::command]`.
2. Register it in the `invoke_handler` list in `src/lib.rs`.
3. If it needs a plugin capability the app does not already have, add it to the right file
   in `capabilities/`.
4. Call it from the frontend with `invoke` from `@tauri-apps/api`.

Forgetting step 2 or 3 produces a runtime error with no compile-time warning. Check both.

## Formatting and tests

`cargo fmt` is CI-enforced as `cargo fmt -- --check`. Run it before pushing.

```bash
cargo fmt
cargo test
```

## Versioning

`tauri.conf.json` has no version field in Tauri v2 — the version comes from `Cargo.toml`,
which must stay in sync with both `package.json` files. Change it only via
`npm run version:bump -- X.Y.Z` from the repository root.
