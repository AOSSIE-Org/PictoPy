use tauri::State;
use std::path::PathBuf;

mod file_service;
mod cache_service;

pub use file_service::FileService;
pub use cache_service::CacheService;

#[tauri::command]
pub fn get_folders_with_images(
    directory: &str,
    file_service: State<'_, FileService>,
    cache_service: State<'_, CacheService>,
) -> Vec<PathBuf> {
    if let Some(cached_folders) = cache_service.get_cached_folders() {
        return cached_folders;
    }

    let folders = file_service.get_folders_with_images(directory);
    let _ = cache_service.cache_folders(&folders);
    folders
}

#[tauri::command]
pub fn get_images_in_folder(
    folder_path: &str,
    file_service: State<'_, FileService>,
) -> Vec<PathBuf> {
    file_service.get_images_in_folder(folder_path)
}

#[tauri::command]
pub fn get_all_images_with_cache(
    directory: &str,
    file_service: State<'_, FileService>,
    cache_service: State<'_, CacheService>,
) -> Vec<PathBuf> {
    if let Some(cached_images) = cache_service.get_cached_images() {
        return cached_images;
    }

    let images = file_service.get_all_images(directory);
    let _ = cache_service.cache_images(&images);
    images
}

#[tauri::command]
pub fn get_all_videos_with_cache(
    directory: &str,
    file_service: State<'_, FileService>,
    cache_service: State<'_, CacheService>,
) -> Vec<PathBuf> {
    if let Some(cached_videos) = cache_service.get_cached_videos() {
        return cached_videos;
    }

    let videos = file_service.get_all_videos(directory);
    let _ = cache_service.cache_videos(&videos);
    videos
}

#[tauri::command]
pub fn delete_cache(cache_service: State<'_, CacheService>) -> bool {
    cache_service.delete_all_caches()
}