# API Documentation

The Rust backend (Tauri v2) exposes the IPC commands below to the frontend. All of them are registered in `frontend/src-tauri/src/main.rs` through `tauri::generate_handler!`.

Commands are invoked with `invoke` from `@tauri-apps/api/core`. Events are subscribed to with `listen` from `@tauri-apps/api/event`.

```typescript
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
```

> **Note:** Tauri v1 imported `invoke` from `@tauri-apps/api/tauri`. That path no longer exists in Tauri v2.

## Argument naming

Rust parameters are written in `snake_case`, but Tauri exposes them to JavaScript in `camelCase` by default. For example, the Rust parameter `memory_id` is passed as `memoryId`. Parameters such as `app: AppHandle` and `state: State<'_, T>` are injected by Tauri and are not passed from the frontend.

All commands that return `Result<T, String>` resolve to `T` on success and reject with the error `string` on failure.

## Command summary

| Command                     | Source file              | Returns                          |
| --------------------------- | ------------------------ | -------------------------------- |
| `get_resources_folder_path` | `src/services/mod.rs`    | `Result<String, String>`         |
| `open_image_file`           | `src/commands.rs`        | `Result<(), String>`             |
| `tunnel_start`              | `src/services/tunnel.rs` | `Result<String, String>`         |
| `tunnel_stop`               | `src/services/tunnel.rs` | `Result<(), String>`             |
| `tunnel_status`             | `src/services/tunnel.rs` | `Result<Option<String>, String>` |
| `open_model_manager`        | `src/main.rs`            | `Result<(), String>`             |
| `get_close_to_tray`         | `src/main.rs`            | `Result<bool, String>`           |
| `set_close_to_tray`         | `src/main.rs`            | `Result<(), String>`             |
| `enable_autostart`          | `src/main.rs`            | `Result<(), String>`             |
| `disable_autostart`         | `src/main.rs`            | `Result<(), String>`             |
| `is_autostart_enabled`      | `src/main.rs`            | `Result<bool, String>`           |
| `open_memory`               | `src/memories.rs`        | `Result<(), String>`             |
| `take_pending_memory`       | `src/memories.rs`        | `Option<Value>`                  |

All source paths are relative to `frontend/src-tauri/`.

## Resources

### get_resources_folder_path

Retrieves the path to the server resources directory.

- **Source**: `src/services/mod.rs`
- **Signature**: `pub fn get_resources_folder_path(handle: tauri::AppHandle) -> Result<String, String>`
- **Parameters**: _None_
- **Returns**: The absolute path of the `resources` folder, resolved with `BaseDirectory::Resource`.

```typescript
import { invoke } from '@tauri-apps/api/core';

const resourcesFolderPath = await invoke<string>('get_resources_folder_path');
console.log('Resources folder path:', resourcesFolderPath);
```

## File system and media

### open_image_file

Opens an image or video in the operating system's default application.

- **Source**: `src/commands.rs`
- **Signature**: `pub async fn open_image_file(app: tauri::AppHandle, path: String) -> Result<(), String>`
- **Parameters**:
  - `path` (`string`): Path of the file to open.
- **Returns**: `Result<(), String>`

The path is validated before the file is opened. The command rejects with an error if any check fails:

1. The path is resolved with `canonicalize`, which blocks `..` tricks and symlinks. If the file does not exist, the error is `File does not exist`.
2. The resolved path must be a file (`Path is not a file`).
3. Its extension must be in the list returned by the backend's `/config/supported-extensions` endpoint (`Only image and video files can be opened`).
4. It must be inside one of the library folders returned by the backend's `/folders/all-folders` endpoint (`File is outside the library folders`).

Because of the last two checks, the Python backend must be running on `localhost:52123` for this command to succeed.

```typescript
import { invoke } from '@tauri-apps/api/core';

try {
  await invoke('open_image_file', { path: '/home/user/Pictures/photo.jpg' });
} catch (error) {
  console.error('Could not open file:', error);
}
```

## Reverse tunnel service

The tunnel exposes a local port to the internet over SSH so an album can be shared. The tunnel state is managed by `TunnelState`, and any running tunnel is shut down when the application exits.

### tunnel_start

Opens a tunnel to the share server, or returns the URL of the one already running.

- **Source**: `src/services/tunnel.rs`
- **Signature**: `pub async fn tunnel_start(app: AppHandle, state: State<'_, TunnelState>, port: u16) -> Result<String, String>`
- **Parameters**:
  - `port` (`number`): Local port to expose.
- **Returns**: The public URL of the tunnel.

The command waits up to 30 seconds for the provider to announce a URL. If no provider succeeds, it rejects with an error listing each provider's failure.

```typescript
import { invoke } from '@tauri-apps/api/core';

const url = await invoke<string>('tunnel_start', { port: 52123 });
console.log('Public URL:', url);
```

### tunnel_stop

Closes the tunnel. It is safe to call when no tunnel is open.

- **Source**: `src/services/tunnel.rs`
- **Signature**: `pub async fn tunnel_stop(state: State<'_, TunnelState>) -> Result<(), String>`
- **Parameters**: _None_
- **Returns**: `Result<(), String>`

```typescript
import { invoke } from '@tauri-apps/api/core';

await invoke('tunnel_stop');
```

### tunnel_status

Returns the public URL if a tunnel is open and has announced one.

- **Source**: `src/services/tunnel.rs`
- **Signature**: `pub fn tunnel_status(state: State<'_, TunnelState>) -> Result<Option<String>, String>`
- **Parameters**: _None_
- **Returns**: The public URL, or `null` if no tunnel is active.

```typescript
import { invoke } from '@tauri-apps/api/core';

const url = await invoke<string | null>('tunnel_status');
console.log(url ? `Sharing at ${url}` : 'Not sharing');
```

## Window and UI management

### open_model_manager

Opens the Model Manager settings window, or shows and focuses it if it is already open.

- **Source**: `src/main.rs`
- **Signature**: `async fn open_model_manager(app: tauri::AppHandle) -> Result<(), String>`
- **Parameters**: _None_
- **Returns**: `Result<(), String>`

The window has the label `model-manager`, loads `index.html?route=/model-manager`, and has a minimum size of 1023 x 632.

```typescript
import { invoke } from '@tauri-apps/api/core';

await invoke('open_model_manager');
```

### get_close_to_tray

Reads the close-to-tray preference from the persistent store.

- **Source**: `src/main.rs`
- **Signature**: `fn get_close_to_tray(app: tauri::AppHandle) -> Result<bool, String>`
- **Parameters**: _None_
- **Returns**: `true` if closing the main window hides it to the system tray. Defaults to `true` when the preference has never been set.

```typescript
import { invoke } from '@tauri-apps/api/core';

const closeToTray = await invoke<boolean>('get_close_to_tray');
```

### set_close_to_tray

Saves the close-to-tray preference to the persistent store.

- **Source**: `src/main.rs`
- **Signature**: `fn set_close_to_tray(app: tauri::AppHandle, enabled: bool) -> Result<(), String>`
- **Parameters**:
  - `enabled` (`boolean`): Whether closing the main window should hide it to the tray.
- **Returns**: `Result<(), String>`

```typescript
import { invoke } from '@tauri-apps/api/core';

await invoke('set_close_to_tray', { enabled: false });
```

## System autostart

When autostart is enabled, the application launches at login with the `--minimized` flag so the window starts hidden. On macOS it uses a Launch Agent.

### enable_autostart

Registers the application to launch at login.

- **Source**: `src/main.rs`
- **Signature**: `fn enable_autostart(app: tauri::AppHandle) -> Result<(), String>`
- **Parameters**: _None_
- **Returns**: `Result<(), String>`

```typescript
import { invoke } from '@tauri-apps/api/core';

await invoke('enable_autostart');
```

### disable_autostart

Removes the application from the login items.

- **Source**: `src/main.rs`
- **Signature**: `fn disable_autostart(app: tauri::AppHandle) -> Result<(), String>`
- **Parameters**: _None_
- **Returns**: `Result<(), String>`

```typescript
import { invoke } from '@tauri-apps/api/core';

await invoke('disable_autostart');
```

### is_autostart_enabled

Checks whether the application is registered to launch at login.

- **Source**: `src/main.rs`
- **Signature**: `fn is_autostart_enabled(app: tauri::AppHandle) -> Result<bool, String>`
- **Parameters**: _None_
- **Returns**: `true` if autostart is enabled.

```typescript
import { invoke } from '@tauri-apps/api/core';

const enabled = await invoke<boolean>('is_autostart_enabled');
```

## Memories service

A background task in `src/memories.rs` checks the backend for a new memory and announces it to the frontend. See [Events](#events) for the event flow.

### open_memory

Brings the main window to the front and routes the app to a memory.

- **Source**: `src/memories.rs`
- **Signature**: `pub fn open_memory(app: AppHandle, memory_id: String) -> Result<(), String>`
- **Parameters**:
  - `memoryId` (`string`): ID of the memory to open.
- **Returns**: `Result<(), String>`

The command unminimizes, shows and focuses the `main` window, then emits the `memory:open` event (see [Events](#events)). It is the single entry point for the in-app card and for any notification-click handler.

```typescript
import { invoke } from '@tauri-apps/api/core';

await invoke('open_memory', { memoryId: 'mem-9' });
```

### take_pending_memory

Returns the latest memory announcement that the frontend has not yet collected, and clears it.

- **Source**: `src/memories.rs`
- **Signature**: `pub fn take_pending_memory(app: AppHandle) -> Option<Value>`
- **Parameters**: _None_
- **Returns**: A `MemoryAnnouncement` object (see `memory:pending` under [Events](#events)), or `null` if there is nothing pending.

The background task can finish before the webview has mounted, in which case the `memory:pending` event would be lost. The announcement is therefore stored before the event is emitted, and the frontend calls this command on mount to collect it.

```typescript
import { invoke } from '@tauri-apps/api/core';

const pending = await invoke<MemoryAnnouncement | null>('take_pending_memory');
```

## Events

The Rust backend emits the following events to the webview. Subscribe with `listen`, which returns a promise of an unlisten function that must be called on cleanup.

### memory:pending

Emitted when a new memory is ready and has not been announced before.

**Payload** (`MemoryAnnouncement`):

```typescript
interface MemoryAnnouncement {
  memory_id: string;
  title: string;
  subtitle: string | null;
  image_count: number;
  video_count: number;
}
```

Payload keys are `snake_case`, because they are serialised directly from Rust.

### memory:open

Emitted by the `open_memory` command when the app should navigate to a memory.

**Payload**:

```typescript
interface MemoryOpenPayload {
  memory_id: string;
}
```

### Subscription pattern

Register the listeners, then call `take_pending_memory` to collect any announcement emitted before the listeners existed.

```typescript
import { useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';

function useMemoryEvents(
  onPending: (memory: MemoryAnnouncement) => void,
  onOpen: (memoryId: string) => void,
) {
  useEffect(() => {
    const subscriptions = [
      listen<MemoryAnnouncement>('memory:pending', (event) =>
        onPending(event.payload),
      ),
      listen<{ memory_id: string }>('memory:open', (event) =>
        onOpen(event.payload.memory_id),
      ),
    ];

    // Collect an announcement emitted before the listeners were registered.
    invoke<MemoryAnnouncement | null>('take_pending_memory').then((pending) => {
      if (pending) onPending(pending);
    });

    return () => {
      subscriptions.forEach((subscription) =>
        subscription.then((unlisten) => unlisten()),
      );
    };
  }, [onPending, onOpen]);
}
```

## Cross-Platform Support

Path resolution uses Tauri's unified `AppHandle.path().resolve(..., BaseDirectory::Resource)`, which works across Windows, macOS, and Linux. On Windows, `open_image_file` strips the `\\?\` prefix that `canonicalize` adds so the default opener can handle the path.
