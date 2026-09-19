use std::path::Path;
use tauri_plugin_opener::OpenerExt;

#[tauri::command]
pub fn open_image_file(app: tauri::AppHandle, path: String) -> Result<(), String> {
    // Resolve the real path first (blocks `..` tricks and symlinks),
    // and confirm it points at an existing file.
    let canonical = Path::new(&path)
        .canonicalize()
        .map_err(|_| "File does not exist".to_string())?;

    if !canonical.is_file() {
        return Err("Path is not a file".into());
    }

    // Check the extension on the resolved path, not the raw input.
    let is_image = canonical
        .extension()
        .and_then(|e| e.to_str())
        .map(|e| matches!(e.to_lowercase().as_str(), "jpg" | "jpeg" | "png"))
        .unwrap_or(false);

    if !is_image {
        return Err("Only image files can be opened".into());
    }

    let p = canonical.to_string_lossy().to_string();

    // On Windows, canonicalize() returns `\\?\C:\...`, which can confuse the opener.
    #[cfg(windows)]
    let p = p.strip_prefix(r"\\?\").map(str::to_string).unwrap_or(p);

    app.opener()
        .open_path(p, None::<String>)
        .map_err(|e| e.to_string())
}