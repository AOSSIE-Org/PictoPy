use tauri_plugin_store::StoreExt;

pub const STORE_PATH: &str = "settings.json";
pub const CLOSE_TO_TRAY_KEY: &str = "close_to_tray";
pub const START_MINIMIZED_KEY: &str = "start_minimized";

#[tauri::command]
pub fn get_close_to_tray(app: tauri::AppHandle) -> Result<bool, String> {
    let store = app.store(STORE_PATH).map_err(|e| e.to_string())?;
    Ok(store
        .get(CLOSE_TO_TRAY_KEY)
        .and_then(|v| v.as_bool())
        .unwrap_or(true))
}

#[tauri::command]
pub fn set_close_to_tray(app: tauri::AppHandle, enabled: bool) -> Result<(), String> {
    let store = app.store(STORE_PATH).map_err(|e| e.to_string())?;
    store.set(CLOSE_TO_TRAY_KEY, enabled);
    store.save().map_err(|e| e.to_string())
}

#[tauri::command]
pub fn get_start_minimized(app: tauri::AppHandle) -> Result<bool, String> {
    let store = app.store(STORE_PATH).map_err(|e| e.to_string())?;
    Ok(store
        .get(START_MINIMIZED_KEY)
        .and_then(|v| v.as_bool())
        .unwrap_or(true)) // default: start minimized to tray, matching prior behavior
}

#[tauri::command]
pub fn set_start_minimized(app: tauri::AppHandle, enabled: bool) -> Result<(), String> {
    let store = app.store(STORE_PATH).map_err(|e| e.to_string())?;
    store.set(START_MINIMIZED_KEY, enabled);
    store.save().map_err(|e| e.to_string())
}
