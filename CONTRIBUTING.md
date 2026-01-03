diff --git a/CONTRIBUTING.md b/CONTRIBUTING.md
index XXXXXXX..YYYYYYY 100644
--- a/CONTRIBUTING.md
+++ b/CONTRIBUTING.md
@@ -## End of existing content##
 
+## Windows Support and Development
+
+PictoPy supports Windows primarily through the packaged `.exe` build. Local
+development on Windows is possible but differs from other platforms and has
+known limitations in the Tauri development flow.
+
+### User Workflow (Recommended)
+
+For Windows end users:
+1. Download the latest Windows `.exe` from the releases page.
+2. Launch the app.
+3. On first run, Windows Firewall may prompt for network access — grant
+   permissions.
+4. If the app fails initially, close and reopen it.
+
+After granting permissions, the application should run normally.
+
+### Developer Workflow
+
+On Windows, avoid assuming that Tauri will auto-start the backend:
+
+**Backend (FastAPI)**
+
+Run the backend manually:
+
+```bash
+fastapi dev
+```
+
+Ensure the backend is reachable (usually on port `8000` / `8001`).
+
+**Frontend / UI**
+
+Run the frontend independently. Do not rely on the Tauri dev command to
+auto-start the backend on Windows.
+
+**Tauri Dev Mode**
+
+The `tauri dev` workflow may be unstable on Windows due to issues with auto
+startup, logging recursion, and server readiness. This is a known limitation
+and does not affect the packaged `.exe` build.
+
+### Known Windows-Specific Issues
+
+- Backend auto-start via Tauri may fail
+ - Logging or server startup race conditions can occur
+ - Firewall or antivirus may block local services
+ - Port conflicts are more common
+
+### Troubleshooting
+
+**Backend runs but UI does not load**
+
+- Confirm the backend is running
+- Verify ports `8000` / `8001` are free
+  
+**Firewall / Network**
+
+- Allow PictoPy through Windows Defender Firewall
+- Restart the application after granting permissions

- [Tauri Documentation](https://tauri.app/start/)
- [React Documentation](https://reactjs.org/docs/getting-started.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Troubleshooting

If you encounter any issues, please check the respective documentation for Tauri, React, and FastAPI. For persistent problems, feel free to open an issue in the project repository.
