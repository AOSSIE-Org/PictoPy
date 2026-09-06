use tauri_plugin_opener::OpenerExt;

#[tauri::command]
pub fn open_image_file(app: tauri::AppHandle, path: String) -> Result<(), String> {
    let allowed_extensions = [".jpg", ".jpeg", ".png"];
    let lower = path.to_lowercase();
    if !allowed_extensions.iter().any(|ext| lower.ends_with(ext)) {
        return Err("Only image files can be opened".into());
    }
    app.opener()
        .open_path(path, None::<String>)
        .map_err(|e| e.to_string())
}