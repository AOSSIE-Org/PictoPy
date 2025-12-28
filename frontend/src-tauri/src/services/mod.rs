use tauri::path::BaseDirectory;
use tauri::Manager;

#[tauri::command]
pub fn get_resources_folder_path(handle: tauri::AppHandle) -> Result<String, String> {
    let resource_path = handle
        .path()
        .resolve("resources", BaseDirectory::Resource)
        .map_err(|e| e.to_string())?;
    Ok(resource_path.to_string_lossy().to_string())
}
