// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod services;

use tauri::path::BaseDirectory;
use tauri::Manager;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_process::init())
        .setup(|app| {
            let resource_path = app
                .path()
                .resolve("resources/backend", BaseDirectory::Resource)?;
            println!("Resource path: {:?}", resource_path);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            services::get_resources_folder_path,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
