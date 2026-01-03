diff --git a/CONTRIBUTING.md b/CONTRIBUTING.md
index XXXXXXX..YYYYYYY 100644
--- a/CONTRIBUTING.md
+++ b/CONTRIBUTING.md
@@ -1,3 +1,35 @@
-# Old CONTRIBUTING.md content removed
+# Contributing to PictoPy
+
+Thank you for your interest in contributing to PictoPy. We welcome
+contributions of all kinds, including bug fixes, documentation improvements,
+and new features.
+
+This document describes the contribution workflow, setup instructions,
+testing and build processes, and platform-specific notes.
+
+---
+
+## Setup
+
+PictoPy consists of a backend (FastAPI) and a frontend application.
+Contributors are expected to set up both components locally.
+
+### Prerequisites
+
+- Git
+- Python 3.9+
+- Node.js (LTS recommended)
+- Rust toolchain (for Tauri development)
+
+### Repository Setup
+
+1. Fork the repository and clone your fork:
+   ```bash
+   git clone https://github.com/<your-username>/PictoPy.git
+   cd PictoPy
+   ```
+
+2. Create a new branch for your work:
+   ```bash
+   git checkout -b feature/my-change
+   ```
+
+3. Follow the platform-appropriate setup instructions below and in
+   `docs/setup.md`.
+
+For detailed setup options (script-based, manual, and documentation site
+setup), see `docs/setup.md`.
+
+---
+
+## Testing
+
+- Ensure backend and frontend run without errors.
+- Run test suites relevant to your changes.
+- Verify documentation renders correctly in Markdown.
+
+---
+
+## Building
+
+- Backend builds: standard FastAPI tooling.
+- Frontend/package builds: verify on your target platform.
+
+---
+
+## Troubleshooting
+
+- Verify required services are running.
+- Check logs for startup/runtime errors.
+- Ensure required ports are free.
+- See `docs/setup.md` for common pitfalls.
+
+---
+
+## Windows Support and Development
+
+PictoPy supports Windows primarily through the packaged `.exe` build. Local
+development on Windows is possible but differs from other platforms and has
+known limitations in the Tauri development flow.
+
+### User Workflow (Recommended)
+
+- Download latest `.exe` from releases page.
+- Launch the application.
+- On first run, grant firewall/network permissions if prompted.
+- If the app fails initially, close and reopen it.
+
+After granting permissions, the application should run normally.
+
+### Developer Workflow (Windows)
+
+Run backend manually; do not rely on Tauri auto-start:
+
+#### Backend (FastAPI)
+
+```bash
+fastapi dev
+```
+
+- FastAPI defaults to port `8000`.
+- If `8000` is in use, an alternate port (e.g., `8001`) may be configured.
+
+#### Frontend / UI
+
+- Run frontend independently.
+- Do not rely on Tauri dev to auto-start the backend.
+
+#### Tauri Dev Mode
+
+- Tauri dev may be unstable on Windows due to:
+  - Backend auto-start failures
+  - Logging recursion
+  - Server readiness race conditions
+
+### Known Windows-Specific Issues
+
+- Backend auto-start via Tauri may fail
+  - Logging or server startup race conditions can occur
+  - Firewall or antivirus may block local services
+  - Port conflicts are more common
+
+### Troubleshooting (Windows)
+
+#### Backend runs but UI does not load
+
+- Confirm backend is running independently.
+- Check backend port (`8000` default; fallback `8001`).
+- Match frontend configuration to backend port.
+
+Use PowerShell to identify port conflicts:
+```powershell
+netstat -ano | findstr :8000
+```
+
+#### Diagnosing startup/logging issues
+
+- Review backend logs for errors.
+- Look for repeated startups, retries, logging recursion.
+- Run backend outside Tauri to isolate issues.
+
+#### Firewall / Antivirus interference
+
+- Allow PictoPy through Windows Defender.
+- For third-party antivirus: allow local traffic and executable.
+- Restart app after updating firewall/antivirus rules.
+
+### Windows Support Summary
+
+| Workflow                | Windows Support     |
+|-------------------------|---------------------|
+| Packaged `.exe`         | Fully supported     |
+| Backend development     | Supported           |
+| Frontend development    | Supported           |
+| Tauri dev mode          | Limited / unstable  |
+
+---
+
+## Additional Resources
+
+- README.md
+- docs/setup.md
+- Issue tracker
+- Pull Requests for discussion
