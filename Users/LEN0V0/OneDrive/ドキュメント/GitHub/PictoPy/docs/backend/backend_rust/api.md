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

- **Description**: Retrieves all images, organized by year and month, with caching.
- **Parameters**:
  - `directory`: String
- **Returns**: `Result<HashMap<u32, HashMap<u32, Vec<String>>>, String>`

### 4. get_all_videos_with_cache

- **Description**: Retrieves all videos, organized by year and month, with caching.
- **Parameters**:
  - `directory`: String
- **Returns**: `Result<HashMap<u32, HashMap<u32, Vec<String>>>, String>`

### 5. delete_cache

- **Description**: Deletes all cached data.
- **Parameters**: None
- **Returns**: `bool`

## Usage Example

```javascript
// In your frontend JavaScript/TypeScript code:
import { invoke } from "@tauri-apps/api/tauri";

// Example: Get all images with cache
const imagesData = await invoke("get_all_images_with_cache", {
  directory: "/path/to/images",
});

// Example: Delete cache
const cacheDeleted = await invoke("delete_cache");
```

## Key Components

- **FileService**: Handles file system operations for images and videos.
- **CacheService**: Manages caching of folders, images, and videos.
- **FileRepository**: Interacts directly with the file system to retrieve file information.
- **CacheRepository**: Handles reading from and writing to cache files.

This backend architecture provides efficient file management and caching capabilities, enhancing the performance of image and video retrieval operations in the Tauri application.
