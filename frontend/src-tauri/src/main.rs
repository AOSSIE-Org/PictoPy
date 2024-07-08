// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

// Learn more about Tauri commands at https://tauri.app/v1/guides/features/command
use tauri::Manager;
mod repositories;
mod services;
mod models;
mod utils;

use crate::services::{FileService, CacheService};

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            let file_service = FileService::new();
            let cache_service = CacheService::new();
            app.manage(file_service);
            app.manage(cache_service);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            services::get_folders_with_images,
            services::get_images_in_folder,
            services::get_all_images_with_cache,
            services::get_all_videos_with_cache,
            services::delete_cache,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}