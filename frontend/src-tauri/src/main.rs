// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod services;

use tauri::path::BaseDirectory;
use tauri::Manager;

// -------- Clipboard imports --------
use tauri::command;
use tauri::AppHandle;
use std::path::PathBuf;
use arboard::{Clipboard, ImageData};
use std::borrow::Cow;
use image::GenericImageView;

// -------- Clipboard command --------
#[command]
fn copy_image_to_clipboard(app: AppHandle, path: String) -> Result<(), String> {
    let resolved: PathBuf = app
        .path()
        .resolve(&path, BaseDirectory::AppData)
        .map_err(|_| "Invalid file path")?;

    if !resolved.exists() {
        return Err("File does not exist".into());
    }

    let img = image::open(&resolved).map_err(|e| e.to_string())?;
    
    // Fix: Add a Size Limit
    let (width, height) = img.dimensions();
    const MAX_PIXELS: u32 = 30_000_000; // ~120MB RGBA

    if width * height > MAX_PIXELS {
        return Err("Image too large to copy to clipboard".into());
    }

    let rgba = img.to_rgba8();

    let image_data = ImageData {
        width: rgba.width() as usize,
        height: rgba.height() as usize,
        bytes: Cow::Owned(rgba.into_raw()),
    };

    let mut clipboard = Clipboard::new().map_err(|e| e.to_string())?;
    clipboard
        .set_image(image_data)
        .map_err(|e| e.to_string())?;

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
            services::get_server_path,
            copy_image_to_clipboard
        ])

        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
