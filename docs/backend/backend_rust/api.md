## API Documentation

The Rust backend provides the following command that can be invoked from the frontend:

### get_server_path

- **Description**: Retrieves the path to the server resources directory.
- **Parameters**: *None*
- **Returns**: `Result<String, String>`

## Usage Examples

```javascript
// In your frontend JavaScript/TypeScript code:
import { invoke } from "@tauri-apps/api/tauri";

// Example: Get server path
const serverPath = await invoke("get_server_path");
console.log("Server path:", serverPath);
```

## Cross-Platform Support

The API provides cross-platform support using Tauri's unified `AppHandle.path().resolve(..., BaseDirectory::Resource)` for path resolution across Windows, macOS, and Linux.

This backend provides essential path resolution functionality for the Tauri application.