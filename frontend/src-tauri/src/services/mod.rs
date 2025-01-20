use std::collections::HashMap;
use std::path::PathBuf;
use std::time::SystemTime;
use tauri::State;
mod cache_service;
mod file_service;
pub use cache_service::CacheService;
use chrono::{DateTime, Datelike, Utc};
pub use file_service::FileService;
use image::{DynamicImage, GenericImageView, ImageBuffer, Rgba};
use tauri::path::BaseDirectory;
use tauri::Manager;

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
    directory: &str,
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
        let all_images = state.get_all_images(directory);
        let mut map: HashMap<u32, HashMap<u32, Vec<String>>> = HashMap::new();

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
            }
        }

        // Cache the flattened list of image paths
        let flattened: Vec<PathBuf> = map
            .values()
            .flat_map(|year_map| year_map.values())
            .flatten()
            .map(|s| PathBuf::from(s))
            .collect();
        if let Err(e) = cache_state.cache_images(&flattened) {
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
    directory: &str,
) -> Result<HashMap<u32, HashMap<u32, Vec<String>>>, String> {
    let cached_videos = cache_state.get_cached_videos();

    let mut videos_by_year_month = if let Some(cached) = cached_videos {
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
        let all_videos = state.get_all_videos(directory);
        let mut map: HashMap<u32, HashMap<u32, Vec<String>>> = HashMap::new();

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

    for year_map in videos_by_year_month.values_mut() {
        for month_vec in year_map.values_mut() {
            month_vec.sort();
        }
    }

    Ok(videos_by_year_month)
}

#[tauri::command]
pub async fn share_file(path: String) -> Result<(), String> {
    use std::process::Command;

    #[cfg(target_os = "windows")]
    {
        Command::new("explorer")
            .args(["/select,", &path])
            .spawn()
            .map_err(|e| e.to_string())?;
    }

    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .args(["-R", &path])
            .spawn()
            .map_err(|e| e.to_string())?;
    }

    #[cfg(target_os = "linux")]
    {
        Command::new("xdg-open")
            .arg(&path)
            .spawn()
            .map_err(|e| e.to_string())?;
    }

    Ok(())
}

#[tauri::command]
pub async fn save_edited_image(
    image_data: Vec<u8>,
    original_path: String,
    filter: String,
    brightness: i32,
    contrast: i32,
) -> Result<(), String> {
    let mut img = image::load_from_memory(&image_data).map_err(|e| e.to_string())?;

    // Apply filter
    match filter.as_str() {
        "grayscale(100%)" => img = img.grayscale(),
        "sepia(100%)" => img = apply_sepia(&img),
        "invert(100%)" => img.invert(),
        _ => {}
    }

    // Apply brightness and contrast
    img = adjust_brightness_contrast(&img, brightness, contrast);

    // Save the edited image
    let path = PathBuf::from(original_path);
    let file_stem = path.file_stem().unwrap_or_default();
    let extension = path.extension().unwrap_or_default();

    let mut edited_path = path.clone();
    edited_path.set_file_name(format!(
        "{}_edited.{}",
        file_stem.to_string_lossy(),
        extension.to_string_lossy()
    ));

    img.save(&edited_path).map_err(|e| e.to_string())?;

    Ok(())
}

fn apply_sepia(img: &DynamicImage) -> DynamicImage {
    let (width, height) = img.dimensions();
    let mut sepia_img = ImageBuffer::new(width, height);

    for (x, y, pixel) in img.pixels() {
        let r = pixel[0] as f32;
        let g = pixel[1] as f32;
        let b = pixel[2] as f32;

        let sepia_r = (0.393 * r + 0.769 * g + 0.189 * b).min(255.0) as u8;
        let sepia_g = (0.349 * r + 0.686 * g + 0.168 * b).min(255.0) as u8;
        let sepia_b = (0.272 * r + 0.534 * g + 0.131 * b).min(255.0) as u8;

        sepia_img.put_pixel(x, y, Rgba([sepia_r, sepia_g, sepia_b, pixel[3]]));
    }

    DynamicImage::ImageRgba8(sepia_img)
}

fn adjust_brightness_contrast(img: &DynamicImage, brightness: i32, contrast: i32) -> DynamicImage {
    let (width, height) = img.dimensions();
    let mut adjusted_img = ImageBuffer::new(width, height);

    let brightness_factor = brightness as f32 / 100.0;
    let contrast_factor = contrast as f32 / 100.0;

    for (x, y, pixel) in img.pixels() {
        let mut new_pixel = [0; 4];
        for c in 0..3 {
            let mut color = pixel[c] as f32;
            // Apply brightness
            color += 255.0 * (brightness_factor - 1.0);
            // Apply contrast
            color = (color - 128.0) * contrast_factor + 128.0;
            new_pixel[c] = color.max(0.0).min(255.0) as u8;
        }
        new_pixel[3] = pixel[3]; // Keep original alpha

        adjusted_img.put_pixel(x, y, Rgba(new_pixel));
    }

    DynamicImage::ImageRgba8(adjusted_img)
}

#[tauri::command]
pub fn delete_cache(cache_service: State<'_, CacheService>) -> bool {
    cache_service.delete_all_caches()
}

#[tauri::command]
pub fn get_server_path(handle: tauri::AppHandle) -> Result<String, String> {
    let resource_path = handle
        .path()
        .resolve("resources/server", BaseDirectory::Resource)
        .map_err(|e| e.to_string())?;
    Ok(resource_path.to_string_lossy().to_string())
}
