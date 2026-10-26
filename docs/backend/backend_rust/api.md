# Rust Backend IPC API Documentation

The desktop shell of PictoPy is built on Tauri v2. The React frontend interacts with the Rust backend via Tauri's inter-process communication (IPC) bridge using the `invoke` API from `@tauri-apps/api/core`.

This document details all 13 Tauri IPC commands registered in `frontend/src-tauri/src/main.rs`, their parameters, return values, error handling, and frontend usage examples.

## Overview

### IPC Architecture

Tauri commands are defined in Rust using the `#[tauri::command]` attribute macro and registered in `tauri::generate_handler!`. When the frontend calls `invoke('command_name', { argName: value })`:

1. Tauri serializes the JavaScript arguments into JSON and maps camelCase JavaScript keys to snake_case Rust function parameters.
2. The Rust handler runs asynchronously or synchronously on Tauri's worker threads.
3. The returned `Result<T, String>` or `Option<T>` resolves the frontend Promise on `Ok(T)` / `Some(T)` or rejects the Promise on `Err(String)` / `None`.

### Basic Frontend Import

In Tauri v2, import `invoke` from `@tauri-apps/api/core` (not the obsolete `@tauri-apps/api/tauri` v1 module):

```typescript
import { invoke } from '@tauri-apps/api/core';
```

---

## Command Reference

### Resource Resolution

#### `get_resources_folder_path`

Retrieves the absolute path to the application's bundled resources directory. Uses Tauri's `AppHandle.path().resolve("resources", BaseDirectory::Resource)` for consistent cross-platform resolution across Windows, macOS, and Linux.

- **Rust Signature**: `pub fn get_resources_folder_path(handle: tauri::AppHandle) -> Result<String, String>`
- **Source**: `frontend/src-tauri/src/services/mod.rs`
- **Parameters**: None
- **Returns**: `Promise<string>` — Resolves with the filesystem path to the `resources` directory.

```typescript
import { invoke } from '@tauri-apps/api/core';

try {
  const resourcesPath = await invoke<string>('get_resources_folder_path');
  console.log('Resources folder path:', resourcesPath);
} catch (error) {
  console.error('Failed to resolve resources path:', error);
}
```

---

### File System Operations

#### `open_image_file`

Opens a media file in the operating system's default viewer or editor (e.g., Photos on Windows, Preview on macOS, xdg-open on Linux) via Tauri's opener plugin.

- **Rust Signature**: `pub async fn open_image_file(app: tauri::AppHandle, path: String) -> Result<(), String>`
- **Source**: `frontend/src-tauri/src/commands.rs`
- **Parameters**:
  - `path` (`string`, required): The filesystem path of the image or video file to open.
- **Returns**: `Promise<void>` — Resolves when the OS default viewer is successfully launched.
- **Security Validations**:
  1. **Canonicalization**: Resolves symlinks and strips relative traversal sequences (`..`) to obtain the canonical path.
  2. **File Verification**: Verifies that the canonical path exists and is a file.
  3. **Extension Whitelist**: Queries the FastAPI backend (`/media/supported-extensions`) to verify the file extension is supported.
  4. **Boundary Sandboxing**: Queries configured library folders (`/folders/get-folders`) to guarantee the file resides within an authorized library folder.

```typescript
import { invoke } from '@tauri-apps/api/core';

async function openMedia(filePath: string) {
  try {
    await invoke<void>('open_image_file', { path: filePath });
  } catch (error) {
    console.error('Failed to open file in system viewer:', error);
  }
}
```

---

### Reverse Tunnel Service (Album Sharing)

PictoPy provides temporary remote album sharing by establishing an outbound SSH reverse tunnel to public tunnel providers (such as `localhost.run` or `pinggy.io`). The tunnel is managed by the Rust core, ensuring child SSH processes are properly tracked and cleaned up on application exit.

#### `tunnel_start`

Spawns an SSH reverse tunnel process forwarding the local backend port to an external public endpoint and returns the allocated public HTTPS URL. If a tunnel is already running, it returns the existing URL.

- **Rust Signature**: `pub async fn tunnel_start(app: AppHandle, state: State<'_, TunnelState>, port: u16) -> Result<String, String>`
- **Source**: `frontend/src-tauri/src/services/tunnel.rs`
- **Parameters**:
  - `port` (`number`, required): The local port number running the FastAPI sharing server (e.g. `8000`).
- **Returns**: `Promise<string>` — The public HTTPS URL (e.g., `https://abc123.a.pinggy.link`).

```typescript
import { invoke } from '@tauri-apps/api/core';

async function shareAlbum(backendPort: number) {
  try {
    const publicUrl = await invoke<string>('tunnel_start', { port: backendPort });
    console.log('Public album sharing URL:', publicUrl);
  } catch (error) {
    console.error('Could not start tunnel:', error);
  }
}
```

#### `tunnel_stop`

Terminates the active SSH reverse tunnel child process and resets tunnel state. It is safe to call even when no tunnel is running.

- **Rust Signature**: `pub async fn tunnel_stop(state: State<'_, TunnelState>) -> Result<(), String>`
- **Source**: `frontend/src-tauri/src/services/tunnel.rs`
- **Parameters**: None
- **Returns**: `Promise<void>` — Resolves when the tunnel process has stopped.

```typescript
import { invoke } from '@tauri-apps/api/core';

await invoke<void>('tunnel_stop');
```

#### `tunnel_status`

Checks the current state of the SSH reverse tunnel.

- **Rust Signature**: `pub fn tunnel_status(state: State<'_, TunnelState>) -> Result<Option<String>, String>`
- **Source**: `frontend/src-tauri/src/services/tunnel.rs`
- **Parameters**: None
- **Returns**: `Promise<string | null>` — Resolves with the public URL if active, or `null` if no tunnel is running or the tunnel process exited.

```typescript
import { invoke } from '@tauri-apps/api/core';

const activeUrl = await invoke<string | null>('tunnel_status');
if (activeUrl) {
  console.log('Tunnel is active at:', activeUrl);
} else {
  console.log('No tunnel is active.');
}
```

---

### Window & UI Management

#### `open_model_manager`

Opens the Model Manager in a dedicated secondary webview window (`index.html?route=/model-manager`) with fixed minimum dimensions (1023x632). If the window is already open, it is unminimized and focused.

- **Rust Signature**: `async fn open_model_manager(app: tauri::AppHandle) -> Result<(), String>`
- **Source**: `frontend/src-tauri/src/main.rs`
- **Parameters**: None
- **Returns**: `Promise<void>`

```typescript
import { invoke } from '@tauri-apps/api/core';

await invoke<void>('open_model_manager');
```

#### `get_close_to_tray`

Reads the user preference indicating whether closing the main window minimizes to the system tray instead of quitting the application. Persisted via `tauri-plugin-store` in `.settings.dat`.

- **Rust Signature**: `fn get_close_to_tray(app: tauri::AppHandle) -> Result<bool, String>`
- **Source**: `frontend/src-tauri/src/main.rs`
- **Parameters**: None
- **Returns**: `Promise<boolean>` — `true` if close-to-tray is enabled (default `true`), `false` otherwise.

```typescript
import { invoke } from '@tauri-apps/api/core';

const closeToTray = await invoke<boolean>('get_close_to_tray');
```

#### `set_close_to_tray`

Sets and persists the close-to-tray user preference in `.settings.dat`.

- **Rust Signature**: `fn set_close_to_tray(app: tauri::AppHandle, enabled: bool) -> Result<(), String>`
- **Source**: `frontend/src-tauri/src/main.rs`
- **Parameters**:
  - `enabled` (`boolean`, required): Whether closing the window should minimize to tray.
- **Returns**: `Promise<void>`

```typescript
import { invoke } from '@tauri-apps/api/core';

await invoke<void>('set_close_to_tray', { enabled: true });
```

---

### System Autostart

Manages starting PictoPy automatically upon system login via `tauri-plugin-autostart`. When launched at boot, the application receives `--minimized` to remain in the system tray.

#### `enable_autostart`

Enables automatic startup on system boot.

- **Rust Signature**: `fn enable_autostart(app: tauri::AppHandle) -> Result<(), String>`
- **Source**: `frontend/src-tauri/src/main.rs`
- **Parameters**: None
- **Returns**: `Promise<void>`

```typescript
import { invoke } from '@tauri-apps/api/core';

await invoke<void>('enable_autostart');
```

#### `disable_autostart`

Disables automatic startup on system boot.

- **Rust Signature**: `fn disable_autostart(app: tauri::AppHandle) -> Result<(), String>`
- **Source**: `frontend/src-tauri/src/main.rs`
- **Parameters**: None
- **Returns**: `Promise<void>`

```typescript
import { invoke } from '@tauri-apps/api/core';

await invoke<void>('disable_autostart');
```

#### `is_autostart_enabled`

Checks whether automatic startup on boot is currently enabled.

- **Rust Signature**: `fn is_autostart_enabled(app: tauri::AppHandle) -> Result<bool, String>`
- **Source**: `frontend/src-tauri/src/main.rs`
- **Parameters**: None
- **Returns**: `Promise<boolean>` — `true` if autostart is enabled, `false` otherwise.

```typescript
import { invoke } from '@tauri-apps/api/core';

const isAutostart = await invoke<boolean>('is_autostart_enabled');
```

---

### Memories Service

The Memories service generates daily memory collections in the background. Because the background task may finish before the React application mounts, these commands and events ensure notifications are reliably delivered.

#### `take_pending_memory`

Retrieves and consumes any pending memory announcement that was generated before the frontend listener was mounted. Calling this clears the internal pending buffer so dismissed memories are not re-announced.

- **Rust Signature**: `pub fn take_pending_memory(app: AppHandle) -> Option<Value>`
- **Source**: `frontend/src-tauri/src/memories.rs`
- **Parameters**: None
- **Returns**: `Promise<object | null>` — Resolves with the memory summary payload or `null` if none is pending.

```typescript
import { invoke } from '@tauri-apps/api/core';

interface PendingMemory {
  memory_id: string;
  title: string;
  subtitle?: string | null;
  image_count: number;
  video_count: number;
}

const pending = await invoke<PendingMemory | null>('take_pending_memory');
if (pending) {
  console.log('Pending memory retrieved:', pending.title);
}
```

#### `open_memory`

Focuses the application window (unminimizing if necessary) and emits the `memory:open` event with `{ memory_id }` to trigger frontend navigation.

- **Rust Signature**: `pub fn open_memory(app: AppHandle, memory_id: String) -> Result<(), String>`
- **Source**: `frontend/src-tauri/src/memories.rs`
- **Parameters**:
  - `memoryId` (`string`, required): The ID of the memory to open (maps to Rust `memory_id`).
- **Returns**: `Promise<void>`

```typescript
import { invoke } from '@tauri-apps/api/core';

await invoke<void>('open_memory', { memoryId: 'memory-uuid' });
```

---

## Event Bridge

In addition to request-response commands via `invoke`, the Rust backend emits native desktop events to the frontend via Tauri's event bus:

| Event Name | Direction | Payload | Description |
| --- | --- | --- | --- |
| `memory:pending` | Rust -> Frontend | `MemorySummary` object | Emitted when a new daily memory is ready for display in the notification card. |
| `memory:open` | Rust -> Frontend | `{ memory_id: string }` | Emitted when a memory notification or card is clicked, instructing the UI to navigate to that memory. |

### Listening to Events

Frontend components subscribe to events using `listen` from `@tauri-apps/api/event`:

```typescript
import { useEffect } from 'react';
import { listen } from '@tauri-apps/api/event';

useEffect(() => {
  const unlistenPromise = listen<{ memory_id: string }>('memory:open', (event) => {
    console.log('Navigating to memory:', event.payload.memory_id);
  });

  return () => {
    unlistenPromise.then((unlisten) => unlisten()).catch(() => {});
  };
}, []);
```
