use tauri::path::BaseDirectory;
use tauri::Manager;

#[tauri::command]
pub fn get_server_path(handle: tauri::AppHandle) -> Result<String, String> {
    let resource_path = handle
        .path()
        .resolve("resources/backend", BaseDirectory::Resource)
        .map_err(|e| e.to_string())?;
    Ok(resource_path.to_string_lossy().to_string())
}


