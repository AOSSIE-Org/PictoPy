// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::env;

#[tauri::command]
pub fn get_server_path() -> String {
    match env::var("SERVER_URL") {
        Ok(val) => val,
        Err(_) => String::from("http://127.0.0.1:8000"),
    }
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![get_server_path])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_process::init())
        .setup(|app| {
            let file_service = FileService::new();
            let cache_service = CacheService::new();
            let resource_path = app
                .path()
                .resolve("resources/backend", BaseDirectory::Resource)?;
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
