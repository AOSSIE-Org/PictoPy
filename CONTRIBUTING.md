# Contributing to PictoPy

Hi there! Thank you for considering contributing to **PictoPy** – we’re excited to collaborate with you. Whether you're fixing a bug, improving documentation, or suggesting a new feature — you're welcome here!

NOTE: Please do not open a PR for the issue which is not yet reviewed and labelled by the maintainer. Wait for the maintainer to give a green light.

## Setting Up the Project

## Setup

1. Setup Using Script (Recommended for Windows, Debian-based OS like Ubuntu, and Fedora/RedHat-based OS): [Guide](docs/Script_Setup_Guide.md)
2. Setup Manually(Recommended for other OSes): [Guide](docs/Manual_Setup_Guide.md)

## Docs Website Setup

PictoPy documentation uses MkDocs with the Material theme and the Swagger UI plugin.

To set up and run the docs website on your local machine:

1. Ensure you have **Python 3** and **pip** installed. Navigate to the `/docs` folder.
2. Create a virtual environment:

   ```bash
   python -m venv .docs-env
   ```

3. Activate the virtual environment:

   ```bash
   # On macOS/Linux:
   source .docs-env/bin/activate
   # On Windows:
   .docs-env\Scripts\activate
   ```

4. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

5. Start the local MkDocs server:

   ```bash
   mkdocs serve -f ../mkdocs.yml
   ```

6. Open your browser and navigate to: <http://127.0.0.1:8000>.

7. Edit Markdown files inside the `docs/` folder. The site will automatically reload when changes are saved.

8. To build the static site for production deployment, run:

   ```bash
   mkdocs build -f ../mkdocs.yml
   ```

## Testing

### Frontend

```bash
cd frontend
npm test
```

> **Note:** After running the frontend tests, you may see a warning:
> `Jest did not exit one second after the test run has completed.`
> This is a known behavior and **does not indicate a problem** when all tests pass. It occurs due to open handles (unclosed servers, DB connections, timers, etc.) that prevent the Node process from exiting cleanly. To identify the root cause, run `npx jest --detectOpenHandles` and ensure resources are properly closed in test teardown (`afterEach`/`afterAll`).

### Backend

- FastAPI

  ```bash
  cd backend
  pytest
  ```

- Tauri

  ```bash
  cd frontend/src-tauri/
  cargo test
  ```

## Building for Production

Create Signing Keys for tauri using the command:

```bash
npm run tauri signer generate
```

Set the public key in tauri.conf.json as pubkey and private key and password in Environment Variables(of your terminal) as TAURI_SIGNING_PRIVATE_KEY and TAURI_SIGNING_PRIVATE_KEY_PASSWORD

As an **example** of the private key would look like this:

```bash
TAURI_SIGNING_PRIVATE_KEY=dW50cnVzdGVkIGNvbW1lbnQ6IHJzaWduIGVuY3J5cHRlZCBzZWNyZXQga2V5ClJXUlRZMEl5NlF2SjE3cWNXOVlQQ0JBTlNITEpOUVoyQ3ZuNTdOSkwyNE1NN2RmVWQ1a0FBQkFBQUFBQUFBQUFBQUlBQUFBQU9XOGpTSFNRd0Q4SjNSbm5Oc1E0OThIUGx6SS9lWXI3ZjJxN3BESEh1QTRiQXlkR2E5aG1oK1g0Tk5kcmFzc0IvZFZScEpubnptRkxlbDlUR2R1d1Y5OGRSYUVmUGoxNTFBcHpQZ1dSS2lHWklZVHNkV1Byd1VQSnZCdTZFWlVGOUFNVENBRlgweUU9Cg==
```

```bash
TAURI_SIGNING_PRIVATE_KEY_PASSWORD=pass
```

```bash
npm run tauri build
```

## Release Management

PictoPy maintains version strings in three manifest files that must always stay in sync:

- `package.json` (root)
- `frontend/package.json`
- `frontend/src-tauri/Cargo.toml`

> **Note:** `frontend/src-tauri/tauri.conf.json` does not hold a version field in Tauri v2 - it inherits the version directly from `Cargo.toml` automatically.

A version bump script at `scripts/bump-version.mjs` acts as the single source of truth. To bump the version across all three files at once, run from the repository root:

```bash
npm run version:bump -- <version>
```

For example:

```bash
npm run version:bump -- 1.2.0
```

The version must follow the `X.Y.Z` format (digits only, no `v` prefix). The script will validate the format, read and verify all three files before writing anything, then print a summary of each file updated.

After running the script, regenerate the Cargo lock file:

```bash
cd frontend/src-tauri
cargo check
```

> **Note:** The `--` separator between `version:bump` and the version number is required by npm to forward the argument to the underlying script.

## Additional Resources

- [Tauri Documentation](https://tauri.app/start/)
- [React Documentation](https://reactjs.org/docs/getting-started.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Troubleshooting

If you encounter any issues, please check the respective documentation for Tauri, React, and FastAPI. For persistent problems, feel free to open an issue in the project repository.
