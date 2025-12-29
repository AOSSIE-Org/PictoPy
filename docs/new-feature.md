# API Security & CORS Configuration

## Overview
PictoPy enforces strict **Cross-Origin Resource Sharing (CORS)** policies to protect user privacy. Unlike typical web servers, the PictoPy backend runs locally on the user's machine. To prevent malicious websites from scanning a user's local network and accessing their photos via our API, we strictly allow only trusted origins.

## Allowed Origins
The middleware is configured to accept requests **only** from the local PictoPy frontend and development servers.

* **Production:**
    * `tauri://localhost` (Tauri default)
    * `https://tauri.localhost` (Tauri HTTPS)
* **Development:**
    * `http://localhost:1420` (Tauri dev server)
    * `http://localhost:5173` (Vite dev server)

## HTTP Methods & Headers
We follow the principle of least privilege. Only the following methods are permitted:
* `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`

If you are developing a new feature that requires a different origin or header, please ensure it does not expose the backend to the wider internet (wildcards `*` are strictly prohibited).
