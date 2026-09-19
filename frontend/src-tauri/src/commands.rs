use std::path::{Path, PathBuf};
use tauri_plugin_opener::OpenerExt;

const FOLDERS_URL: &str = "http://localhost:52123/folders/all-folders";

/// Fetch the user's library folders from the Python backend (trusted source,
/// not from frontend input) and canonicalize them.
async fn fetch_library_folders() -> Result<Vec<PathBuf>, String> {
    let body = reqwest::get(FOLDERS_URL)
        .await
        .map_err(|e| format!("Could not reach backend: {e}"))?
        .text()
        .await
        .map_err(|e| e.to_string())?;

    let json: serde_json::Value = serde_json::from_str(&body).map_err(|e| e.to_string())?;

    let folders = json["data"]["folders"]
        .as_array()
        .ok_or("Unexpected backend response")?;

    Ok(folders
        .iter()
        .filter_map(|f| f["folder_path"].as_str())
        .filter_map(|p| Path::new(p).canonicalize().ok())
        .collect())
}

#[tauri::command]
pub async fn open_image_file(app: tauri::AppHandle, path: String) -> Result<(), String> {
    // Resolve the real path (blocks `..` tricks and symlinks).
    let canonical = Path::new(&path)
        .canonicalize()
        .map_err(|_| "File does not exist".to_string())?;

    if !canonical.is_file() {
        return Err("Path is not a file".into());
    }

    // Check the extension on the resolved path.
    let is_image = canonical
        .extension()
        .and_then(|e| e.to_str())
        .map(|e| matches!(e.to_lowercase().as_str(), "jpg" | "jpeg" | "png"))
        .unwrap_or(false);

    if !is_image {
        return Err("Only image files can be opened".into());
    }

    // Only allow files inside the user's configured library folders.
    let roots = fetch_library_folders().await?;
    if !roots.iter().any(|root| canonical.starts_with(root)) {
        return Err("File is outside the library folders".into());
    }

    let p = canonical.to_string_lossy().to_string();

    // On Windows, canonicalize() returns `\\?\C:\...`, which can confuse the opener.
    #[cfg(windows)]
    let p = p.strip_prefix(r"\\?\").map(str::to_string).unwrap_or(p);

    app.opener()
        .open_path(p, None::<String>)
        .map_err(|e| e.to_string())
}
