use std::collections::HashMap;
use std::path::PathBuf;
use std::time::SystemTime;
use tauri::State;
mod cache_service;
mod file_service;
pub use cache_service::CacheService;
use chrono::{DateTime, Datelike, Utc};
pub use file_service::FileService;

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
    state: tauri::State<FileService>,
    cache_state: tauri::State<CacheService>,
    directories: Vec<String>,
) -> Result<HashMap<u32, HashMap<u32, Vec<String>>>, String> {
    let cached_images = cache_state.get_cached_images();

    let mut images_by_year_month = if let Some(cached) = cached_images {
        let mut map: HashMap<u32, HashMap<u32, Vec<String>>> = HashMap::new();
        for path in cached {
            if let Ok(metadata) = std::fs::metadata(&path) {
                let date = metadata
                    .created()
                    .or_else(|_| metadata.modified())
                    .unwrap_or_else(|_| SystemTime::now());

                let datetime: DateTime<Utc> = date.into();
                let year = datetime.year() as u32;
                let month = datetime.month();
                map.entry(year)
                    .or_insert_with(HashMap::new)
                    .entry(month)
                    .or_insert_with(Vec::new)
                    .push(path.to_str().unwrap_or_default().to_string());
            }
        }
        map
    } else {
        let mut map: HashMap<u32, HashMap<u32, Vec<String>>> = HashMap::new();
        let mut all_image_paths: Vec<PathBuf> = Vec::new();

        for directory in directories {
            let all_images = state.get_all_images(&directory);

            for path in all_images {
                if let Ok(metadata) = std::fs::metadata(&path) {
                    let date = metadata
                        .created()
                        .or_else(|_| metadata.modified())
                        .unwrap_or_else(|_| SystemTime::now());

                    let datetime: DateTime<Utc> = date.into();
                    let year = datetime.year() as u32;
                    let month = datetime.month();
                    map.entry(year)
                        .or_insert_with(HashMap::new)
                        .entry(month)
                        .or_insert_with(Vec::new)
                        .push(path.to_str().unwrap_or_default().to_string());

                    all_image_paths.push(path); // Collect all paths for caching
                }
            }
        }

        // Cache the flattened list of image paths
        if let Err(e) = cache_state.cache_images(&all_image_paths) {
            eprintln!("Failed to cache images: {}", e);
        }

        map
    };

    // Sort the images within each month
    for year_map in images_by_year_month.values_mut() {
        for month_vec in year_map.values_mut() {
            month_vec.sort();
        }
    }

    Ok(images_by_year_month)
}

#[tauri::command]
pub fn get_all_videos_with_cache(
    state: tauri::State<FileService>,
    cache_state: tauri::State<CacheService>,
    directories: Vec<String>, // Updated to take an array of directories
) -> Result<HashMap<u32, HashMap<u32, Vec<String>>>, String> {
    let cached_videos = cache_state.get_cached_videos();

    let mut videos_by_year_month: HashMap<u32, HashMap<u32, Vec<String>>> =
        if let Some(cached) = cached_videos {
            let mut map: HashMap<u32, HashMap<u32, Vec<String>>> = HashMap::new();
            for path in cached {
                if let Ok(metadata) = std::fs::metadata(&path) {
                    if let Ok(created) = metadata.created() {
                        let datetime: DateTime<Utc> = created.into();
                        let year = datetime.year() as u32;
                        let month = datetime.month();
                        map.entry(year)
                            .or_insert_with(HashMap::new)
                            .entry(month)
                            .or_insert_with(Vec::new)
                            .push(path.to_str().unwrap_or_default().to_string());
                    }
                }
            }
            map
        } else {
            let mut map: HashMap<u32, HashMap<u32, Vec<String>>> = HashMap::new();
            for directory in directories {
                let all_videos = state.get_all_videos(&directory);
                for path in all_videos {
                    if let Ok(metadata) = std::fs::metadata(&path) {
                        if let Ok(created) = metadata.created() {
                            let datetime: DateTime<Utc> = created.into();
                            let year = datetime.year() as u32;
                            let month = datetime.month();
                            map.entry(year)
                                .or_insert_with(HashMap::new)
                                .entry(month)
                                .or_insert_with(Vec::new)
                                .push(path.to_str().unwrap_or_default().to_string());
                        }
                    }
                }
            }

            // Cache the aggregated video paths
            let flattened: Vec<PathBuf> = map
                .values()
                .flat_map(|year_map| year_map.values())
                .flatten()
                .map(|s| PathBuf::from(s))
                .collect();
            if let Err(e) = cache_state.cache_videos(&flattened) {
                eprintln!("Failed to cache videos: {}", e);
            }

            map
        };

    // Sort the videos within each month
    for year_map in videos_by_year_month.values_mut() {
        for month_vec in year_map.values_mut() {
            month_vec.sort();
        }
    }

    Ok(videos_by_year_month)
}

#[tauri::command]
pub fn delete_cache(cache_service: State<'_, CacheService>) -> bool {
    cache_service.delete_all_caches()
}
