// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod services;

use tauri::path::BaseDirectory;
use tauri::Manager;

// -------- Clipboard imports --------
// -------- Clipboard imports --------
use tauri::command;
use std::path::{Path, PathBuf};
use arboard::{Clipboard, ImageData};
use std::borrow::Cow;
use image::GenericImageView;

// -------- Clipboard command --------
#[command]
fn copy_image_to_clipboard(path: String) -> Result<(), String> {
    let path = PathBuf::from(&path);

    // 🔐 Security checks
    if !path.is_absolute() {
        return Err("Expected absolute file path".into());
    }

    if path.components().any(|c| matches!(c, std::path::Component::ParentDir)) {
        return Err("Invalid path traversal detected".into());
    }

    if !path.exists() {
        return Err("File does not exist".into());
    }

    if !path.is_file() {
        return Err("Path is not a file".into());
    }

    // Load image
    let img = image::open(&path)
        .map_err(|e| format!("Failed to open image: {}", e))?;

    // Optional: prevent huge images
    let (w, h) = img.dimensions();
    if w > 8000 || h > 8000 {
        return Err("Image too large to copy".into());
    }

    let rgba = img.to_rgba8();

    let image_data = ImageData {
        width: rgba.width() as usize,
        height: rgba.height() as usize,
        bytes: Cow::Owned(rgba.into_raw()),
    };

    let mut clipboard = Clipboard::new()
        .map_err(|e| format!("Clipboard init failed: {}", e))?;

    clipboard
        .set_image(image_data)
        .map_err(|e| format!("Clipboard write failed: {}", e))?;

    Ok(())
}

fn main() {
    tauri::Builder::default()
        // -------- Existing plugins (unchanged) --------
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_process::init())

        // -------- Existing setup (unchanged) --------
        .setup(|app| {
            let resource_path = app
                .path()
                .resolve("resources/backend", BaseDirectory::Resource)?;
            println!("Resource path: {:?}", resource_path);
            Ok(())
        })

        // -------- Register commands --------
        .invoke_handler(tauri::generate_handler![
            services::get_resources_folder_path,
            copy_image_to_clipboard
        ])

        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
