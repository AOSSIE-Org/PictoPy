# Contributing to PictoPy

Thanks for your interest in contributing to PictoPy. We welcome bug fixes, documentation updates, and feature work that fits the project and improves the product.

> [!IMPORTANT]
> Do not open a pull request for an issue until the maintainer has reviewed and labelled it.
>
> Low-effort, unreviewed, or AI-generated submissions that do not meaningfully improve the codebase or product may be closed without discussion.

Before making changes, read the repository-level guidance in `AGENTS.md` and the closest area-specific `AGENTS.md` for the part of the codebase you are touching.

## Project setup

### Setup options

1. Use the automated setup script for Windows, Debian-based systems, and Fedora/Red Hat-based systems: [Script setup guide](docs/Script_Setup_Guide.md)
2. Use the manual setup guide for other operating systems: [Manual setup guide](docs/Manual_Setup_Guide.md)

## Documentation site

PictoPy's docs use MkDocs with the Material theme and the Swagger UI plugin.

To run the site locally:

1. Ensure Python 3 and `pip` are installed.
2. Change into the `docs/` directory.
3. Create a virtual environment:

   ```bash
   python -m venv .docs-env
   ```

4. Activate it:

   ```bash
   # macOS/Linux
   source .docs-env/bin/activate

   # Windows PowerShell
   .docs-env\Scripts\Activate.ps1
   ```

5. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

6. Start the MkDocs development server:

   ```bash
   mkdocs serve -f ../mkdocs.yml
   ```

7. Open <http://127.0.0.1:8000> in your browser.
8. Edit the Markdown files under `docs/`; the site reloads automatically on save.
9. To build a production static site:

   ```bash
   mkdocs build -f ../mkdocs.yml
   ```

## Working with AI coding agents

If you use Claude Code, Cursor, GitHub Copilot, Codex, or Gemini CLI, this repository ships committed agent configuration so your tools already know the project's conventions. You do not need to paste instructions into chat.

Start with the repository root `AGENTS.md`. The project also includes reusable playbooks in `agent-kit/` for common tasks such as adding an endpoint, adding a frontend feature, and running the pre-PR checks.

See [docs/ai-contributing.md](docs/ai-contributing.md) for the full explanation, including how to add your own rules and playbooks.

You remain responsible for everything you submit. Review your diff before opening a PR.

## Contribution workflow

- Keep the change focused on the issue or feature you are addressing.
- Follow the nearest `AGENTS.md` for architectural and formatting rules.
- Run only the checks relevant to the area you changed.
- Open a PR only after the issue has been reviewed and labelled by maintainers.
- PRs target `dev`; `main` is updated through release PRs from `dev`.
- Reference the related issue in the PR body using `#<number>`.

## Testing

### Frontend

```bash
cd frontend
npm test
```

### Backend

- FastAPI:

  ```bash
  cd backend
  pytest
  ```

- Tauri:

  ```bash
  cd frontend/src-tauri/
  cargo test
  ```

## Building for production

From the repository root, generate a signing key in the `frontend/` directory. The values below are examples; replace them with the private key and password generated for your build:

```bash
cd frontend
npm run tauri signer generate
export TAURI_SIGNING_PRIVATE_KEY="<generated private key>"
export TAURI_SIGNING_PRIVATE_KEY_PASSWORD="<key password>"
```

Set the corresponding public key under `plugins.updater.pubkey` in `frontend/src-tauri/tauri.conf.json`.

On Windows PowerShell, use:

```powershell
Set-Location frontend
$env:TAURI_SIGNING_PRIVATE_KEY = "<generated private key>"
$env:TAURI_SIGNING_PRIVATE_KEY_PASSWORD = "<key password>"
```

With your terminal still in `frontend/`, build the app:

```bash
npm run tauri build
```

## Release management

PictoPy keeps version strings in sync across these files:

- `package.json`
- `frontend/package.json`
- `frontend/src-tauri/Cargo.toml`

> [!NOTE]
> `frontend/src-tauri/tauri.conf.json` does not contain a version field in Tauri v2; it inherits the version directly from `Cargo.toml`.

Use the version bump script as the single source of truth from the repository root:

```bash
npm run version:bump -- <version>
```

Example:

```bash
npm run version:bump -- 1.2.0
```

The version must follow the `X.Y.Z` format (digits only, no `v` prefix). The script validates the format, verifies the three manifests, then writes the changes and summarizes each file updated.

After bumping the version, regenerate the Cargo lock file:

```bash
cd frontend/src-tauri
cargo check
```

> [!NOTE]
> The `--` separator between `version:bump` and the version string is required by npm so the argument is forwarded to the underlying script.

### Automated release prep

When a release is approaching, trigger the release prep workflow from the GitHub Actions tab:

1. Go to **Actions → Release Prep → Run workflow**.
2. Enter the target version in `X.Y.Z` format.
3. The workflow opens a PR that includes:
   - a version bump across all manifest files
   - a draft `CHANGELOG.md` entry with merged PRs grouped by label
4. Review the PR, clean up the changelog prose, and merge it.
5. Create the GitHub Release with tag `v<version>` to trigger the build pipeline.

### Release validation (CI gate)

`build-and-release.yml` contains a `validate-changelog` job that runs on every release trigger. It checks that `CHANGELOG.md` contains a `## [X.Y.Z]` entry matching the release tag before publishing proceeds. If the entry is missing, the release is blocked. Always merge the release prep PR before creating the GitHub Release.

## Additional resources

- [Tauri documentation](https://tauri.app/start/)
- [React documentation](https://react.dev/learn)
- [FastAPI documentation](https://fastapi.tiangolo.com/)

## Troubleshooting

If you run into issues, check the relevant documentation for Tauri, React, and FastAPI. For persistent problems, open an issue in the project repository.
