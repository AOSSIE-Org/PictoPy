// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod cache;
mod image_processing;
mod models;
mod repositories;
mod services;
mod utils;

use services::{
    analyze_cache_usage, check_secure_folder_status, clear_image_cache, configure_image_cache,
    create_secure_folder, delete_cache, export_cache_stats, get_all_images_with_cache,
    get_all_videos_with_cache, get_cache_entries_by_prefix, get_cache_performance_log,
    get_cache_stats, get_detailed_cache_stats, get_folders_with_images, get_image_cache_config,
    get_image_processing_documentation, get_images_in_folder, get_random_memories,
    get_secure_media, invalidate_cache_by_pattern, invalidate_cache_by_prefix,
    invalidate_cache_entry, move_to_secure_folder, open_folder, open_with, optimize_cache_config,
    preload_common_operations, preload_with_python, prune_image_cache_by_age, put_image_with_ttl,
    remove_from_secure_folder, reset_cache_stats, run_diagnostics, save_edited_image,
    set_wallpaper, share_file, sync_with_python_cache, unlock_secure_folder, CacheService,
    FileService,
};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(FileService::new())
        .manage(CacheService::new())
        .invoke_handler(tauri::generate_handler![
            get_folders_with_images,
            get_images_in_folder,
            get_all_images_with_cache,
            get_all_videos_with_cache,
            share_file,
            save_edited_image,
            move_to_secure_folder,
            remove_from_secure_folder,
            create_secure_folder,
            get_secure_media,
            unlock_secure_folder,
            check_secure_folder_status,
            get_random_memories,
            delete_cache,
            set_wallpaper,
            open_folder,
            open_with,
            get_cache_stats,
            reset_cache_stats,
            clear_image_cache,
            prune_image_cache_by_age,
            configure_image_cache,
            get_image_cache_config,
            invalidate_cache_entry,
            invalidate_cache_by_prefix,
            put_image_with_ttl,
            invalidate_cache_by_pattern,
            preload_common_operations,
            get_cache_entries_by_prefix,
            get_detailed_cache_stats,
            export_cache_stats,
            get_cache_performance_log,
            analyze_cache_usage,
            optimize_cache_config,
            get_image_processing_documentation,
            sync_with_python_cache,
            preload_with_python,
            run_diagnostics
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
fn main() {
    run();
}
