## API Documentation

The Rust backend provides the following commands that can be invoked from the frontend:

### 1. get_folders_with_images

- **Description**: Retrieves folders containing images from a specified directory.
- **Parameters**:
  - `directory`: String
- **Returns**: `Vec<PathBuf>`

### 2. get_images_in_folder

- **Description**: Gets all images in a specific folder.
- **Parameters**:
  - `folder_path`: String
- **Returns**: `Vec<PathBuf>`


### 3. get_all_images_with_cache

- **Description**: Retrieves all images from multiple directories, organized by year and month, with caching.
- **Parameters**:
  - `directories`: Vec<String>
- **Returns**: `Result<HashMap<u32, HashMap<u32, Vec<String>>>, String>`

### 4. get_all_videos_with_cache

- **Description**: Retrieves all videos from multiple directories, organized by year and month, with caching.
- **Parameters**:
  - `directories`: Vec<String>
- **Returns**: `Result<HashMap<u32, HashMap<u32, Vec<String>>>, String>`

### 5. delete_cache

- **Description**: Deletes all cached data.
- **Parameters**: None
- **Returns**: `bool`

### 6. share_file

- **Description**: Opens the file in the system's default file manager and selects it.
- **Parameters**:
  - `path`: String
- **Returns**: `Result<(), String>`

### 7. save_edited_image

- **Description**: Saves an edited image with applied filters and adjustments.
- **Parameters**:
  - `image_data`: Vec<u8>
  - `save_path`: String
  - `filter`: String
  - `brightness`: i32
  - `contrast`: i32
  - `vibrance`: i32
  - `exposure`: i32
  - `temperature`: i32
  - `sharpness`: i32
  - `vignette`: i32
  - `highlights`: i32
- **Returns**: `Result<(), String>`

### 8. get_server_path

- **Description**: Retrieves the path to the server resources directory.
- **Parameters**: *None*
- **Returns**: `Result<String, String>`
### 9. move_to_secure_folder

- **Description**: Moves a file to the secure folder with encryption.
- **Parameters**:
  - `path`: String
  - `password`: String
- **Returns**: `Result<(), String>`

### 10. create_secure_folder

- **Description**: Creates a new secure folder with password protection.
- **Parameters**:
  - `password`: String
- **Returns**: `Result<(), String>`

### 11. unlock_secure_folder

- **Description**: Unlocks the secure folder with the provided password.
- **Parameters**:
  - `password`: String
- **Returns**: `Result<bool, String>`

### 12. get_secure_media

- **Description**: Retrieves all media files from the secure folder.
- **Parameters**:
  - `password`: String
- **Returns**: `Result<Vec<SecureMedia>, String>`

### 13. remove_from_secure_folder

- **Description**: Removes a file from the secure folder.
- **Parameters**:
  - `file_name`: String
  - `password`: String
- **Returns**: `Result<(), String>`

### 14. check_secure_folder_status

- **Description**: Checks if the secure folder is set up.
- **Parameters**: None
- **Returns**: `Result<bool, String>`

### 15. get_random_memories

- **Description**: Retrieves random memory images from specified directories.
- **Parameters**:
  - `directories`: Vec<String>
  - `count`: usize
- **Returns**: `Result<Vec<MemoryImage>, String>`

### 16. open_folder

- **Description**: Opens the parent folder of the specified file path.
- **Parameters**:
  - `path`: String
- **Returns**: `Result<(), String>`

### 17. open_with

- **Description**: Opens a file with the system's "Open With" dialog.
- **Parameters**:
  - `path`: String
- **Returns**: `Result<(), String>`

### 18. set_wallpaper

- **Description**: Sets an image as the desktop wallpaper.
- **Parameters**:
  - `path`: String
- **Returns**: `Result<(), String>`

## Data Structures

### SecureMedia

```rust
pub struct SecureMedia {
    pub id: String,
    pub url: String,
    pub path: String,
}
```

### MemoryImage

```rust
pub struct MemoryImage {
    path: String,
    created_at: DateTime<Utc>,
}
```

## Usage Examples

```javascript
// In your frontend JavaScript/TypeScript code:
import { invoke } from "@tauri-apps/api/tauri";

// Example: Get all images with cache from multiple directories
const imagesData = await invoke("get_all_images_with_cache", {
  directories: ["/path/to/images1", "/path/to/images2"],
});

// Example: Share a file
await invoke("share_file", { path: "/path/to/file.jpg" });

// Example: Save edited image
await invoke("save_edited_image", {
  image_data: imageBytes,
  save_path: "/path/to/save/edited.jpg",
  filter: "grayscale(100%)",
  brightness: 10,
  contrast: 20,
  vibrance: 15,
  exposure: 5,
  temperature: 0,
  sharpness: 10,
  vignette: 0,
  highlights: 0
});

// Example: Create secure folder
await invoke("create_secure_folder", { password: "mySecurePassword" });

// Example: Move file to secure folder
await invoke("move_to_secure_folder", {
  path: "/path/to/file.jpg",
  password: "mySecurePassword"
});

// Example: Get random memories
const memories = await invoke("get_random_memories", {
  directories: ["/path/to/photos"],
  count: 5
});

// Example: Set wallpaper
await invoke("set_wallpaper", { path: "/path/to/wallpaper.jpg" });

// Example: Delete cache
const cacheDeleted = await invoke("delete_cache");
```

## Key Components

- **FileService**: Handles file system operations for images and videos.
- **CacheService**: Manages caching of folders, images, and videos.
- **FileRepository**: Interacts directly with the file system to retrieve file information.
- **CacheRepository**: Handles reading from and writing to cache files.
- **Secure Storage**: Provides encrypted storage functionality with password protection.
- **Image Processing**: Handles image editing operations including filters, brightness, contrast, and other adjustments.
- **System Integration**: Provides integration with the operating system for file operations, wallpaper setting, and file management.

## Security Features

The API includes comprehensive security features for protecting sensitive media:

- **Encryption**: Files moved to secure folders are encrypted using AES-256-GCM
- **Password Protection**: Secure folders require password authentication
- **Salt-based Hashing**: Uses PBKDF2 with SHA-256 for password hashing
- **Secure Random**: Uses cryptographically secure random number generation

## Cross-Platform Support

The API provides cross-platform support for:
- **Windows**: File operations, wallpaper setting, and system integration
- **macOS**: Native file operations and AppleScript integration
- **Linux**: Support for GNOME and KDE desktop environments

This backend architecture provides efficient file management, caching capabilities, secure storage, image processing, and system integration, enhancing the overall functionality of the Tauri application.
