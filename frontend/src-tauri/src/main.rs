// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod models;
mod repositories;
mod services;
mod utils;

use crate::services::{CacheService, FileService};
use std::env;
use tauri::path::BaseDirectory;
use tauri::Manager;

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            let file_service = FileService::new();
            let cache_service = CacheService::new();
            let resource_path = app
                .path()
                .resolve("resources/server", BaseDirectory::Resource)?;
            println!("Resource path: {:?}", resource_path);
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
            services::share_file,
            services::save_edited_image,
            services::get_server_path,
            services::move_to_secure_folder,
            services::create_secure_folder,
            services::unlock_secure_folder,
            services::get_secure_media,
            services::remove_from_secure_folder,
            services::check_secure_folder_status,
            services::get_random_memories,
            services::open_folder,
            services::open_with,
            services::set_wallpaper,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
