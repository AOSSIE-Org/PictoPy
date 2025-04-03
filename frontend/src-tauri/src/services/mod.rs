use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant, SystemTime};
use tauri::State;
mod cache_service;
mod file_service;
pub use cache_service::CacheService;
use chrono::{DateTime, Datelike, Utc};
use data_encoding::BASE64;
use directories::ProjectDirs;
pub use file_service::FileService;
use image::{DynamicImage, RgbImage, Rgba, RgbaImage};
use rand::seq::SliceRandom;
use ring::aead::{Aad, LessSafeKey, Nonce, UnboundKey, AES_256_GCM};
use ring::digest;
use ring::pbkdf2;
use ring::rand::{SecureRandom, SystemRandom};
use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::fs;
use std::num::NonZeroU32;
use std::process::Command;
// Removed unused imports
// use tauri::path::BaseDirectory;
// use tauri::Manager;
use crate::cache::{CacheStats, IMAGE_CACHE};
use crate::image_processing::adjust_brightness_contrast;

pub const SECURE_FOLDER_NAME: &str = "secure_folder";
const SALT_LENGTH: usize = 16;
const NONCE_LENGTH: usize = 12;

#[derive(Serialize, Deserialize)]
pub struct SecureMedia {
    pub id: String,
    pub url: String,
    pub path: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct MemoryImage {
    path: String,
    #[serde(with = "chrono::serde::ts_seconds")]
    created_at: DateTime<Utc>,
}

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
                    .or_default()
                    .entry(month)
                    .or_default()
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
                        .or_default()
                        .entry(month)
                        .or_default()
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
                            .or_default()
                            .entry(month)
                            .or_default()
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
                                .or_default()
                                .entry(month)
                                .or_default()
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
                .map(PathBuf::from)
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
    save_path: String,
    filter: String,
    brightness: i32,
    contrast: i32,
    vibrance: i32,
    exposure: i32,
    temperature: i32,
    sharpness: i32,
    _vignette: i32,
    _highlights: i32,
) -> Result<(), String> {
    let mut img = image::load_from_memory(&image_data).map_err(|e| e.to_string())?;

    // Apply filter
    match filter.as_str() {
        "grayscale(100%)" => img = img.grayscale(),
        "sepia(100%)" => img = apply_sepia(&img),
        "invert(100%)" => {
            img.invert();
        }
        "saturate(200%)" => img = apply_saturation(&img, 2.0),
        _ => {}
    }

    // Apply adjustments using our optimized functions
    if brightness != 0 || contrast != 0 {
        img = adjust_brightness_contrast(&img, brightness, contrast);
    }

    if vibrance != 0 {
        img = apply_vibrance(&img, vibrance);
    }

    if exposure != 0 {
        img = apply_exposure(&img, exposure);
    }

    if temperature != 0 {
        img = apply_temperature(&img, temperature);
    }

    if sharpness != 0 {
        img = apply_sharpness(&img, sharpness);
    }

    // Save the image
    img.save(&save_path).map_err(|e| e.to_string())?;

    // Sync with Python cache
    sync_with_python_cache(&save_path)?;

    Ok(())
}

pub fn apply_sepia(img: &DynamicImage) -> DynamicImage {
    let mut sepia = img.to_rgb8();
    for pixel in sepia.pixels_mut() {
        let r = pixel[0] as f32;
        let g = pixel[1] as f32;
        let b = pixel[2] as f32;
        pixel[0] = ((r * 0.393) + (g * 0.769) + (b * 0.189)).min(255.0) as u8;
        pixel[1] = ((r * 0.349) + (g * 0.686) + (b * 0.168)).min(255.0) as u8;
        pixel[2] = ((r * 0.272) + (g * 0.534) + (b * 0.131)).min(255.0) as u8;
    }
    DynamicImage::ImageRgb8(sepia)
}

pub fn apply_saturation(img: &DynamicImage, factor: f32) -> DynamicImage {
    let mut saturated = img.to_rgb8();
    for pixel in saturated.pixels_mut() {
        let r = pixel[0] as f32 / 255.0;
        let g = pixel[1] as f32 / 255.0;
        let b = pixel[2] as f32 / 255.0;
        let max = r.max(g).max(b);
        let min = r.min(g).min(b);
        let delta = max - min;
        if delta != 0.0 {
            let sat = (delta / max) * factor;
            pixel[0] = (((r - 0.5) * sat + 0.5).max(0.0).min(1.0) * 255.0) as u8;
            pixel[1] = (((g - 0.5) * sat + 0.5).max(0.0).min(1.0) * 255.0) as u8;
            pixel[2] = (((b - 0.5) * sat + 0.5).max(0.0).min(1.0) * 255.0) as u8;
        }
    }
    DynamicImage::ImageRgb8(saturated)
}

pub fn apply_vibrance(img: &DynamicImage, vibrance: i32) -> DynamicImage {
    let mut vibrant = img.to_rgb8();
    let vibrance_factor = vibrance as f32 / 100.0;

    for pixel in vibrant.pixels_mut() {
        let r = pixel[0] as f32 / 255.0;
        let g = pixel[1] as f32 / 255.0;
        let b = pixel[2] as f32 / 255.0;

        let max = r.max(g).max(b);
        let avg = (r + g + b) / 3.0;

        let amt = (max - avg) * 2.0 * vibrance_factor;

        pixel[0] = ((r + (max - r) * amt) * 255.0).clamp(0.0, 255.0) as u8;
        pixel[1] = ((g + (max - g) * amt) * 255.0).clamp(0.0, 255.0) as u8;
        pixel[2] = ((b + (max - b) * amt) * 255.0).clamp(0.0, 255.0) as u8;
    }

    DynamicImage::ImageRgb8(vibrant)
}

pub fn apply_exposure(img: &DynamicImage, exposure: i32) -> DynamicImage {
    let mut exposed = img.to_rgb8();
    let factor = 2.0f32.powf(exposure as f32 / 100.0);

    for pixel in exposed.pixels_mut() {
        for c in 0..3 {
            pixel[c] = ((pixel[c] as f32 * factor).clamp(0.0, 255.0)) as u8;
        }
    }

    DynamicImage::ImageRgb8(exposed)
}

pub fn apply_temperature(img: &DynamicImage, temperature: i32) -> DynamicImage {
    let mut temp_adjusted = img.to_rgb8();
    let factor = temperature as f32 / 100.0;
    for pixel in temp_adjusted.pixels_mut() {
        let r = (pixel[0] as f32 * (1.0 + factor)).min(255.0) as u8;
        let b = (pixel[2] as f32 * (1.0 - factor)).max(0.0) as u8;
        pixel[0] = r;
        pixel[2] = b;
    }
    DynamicImage::ImageRgb8(temp_adjusted)
}

pub fn apply_sharpness(img: &DynamicImage, sharpness: i32) -> DynamicImage {
    let rgba_img = img.to_rgba8();
    let (width, height) = rgba_img.dimensions();
    let mut sharpened = RgbaImage::new(width, height);

    let kernel: [f32; 9] = [-1.0, -1.0, -1.0, -1.0, 9.0, -1.0, -1.0, -1.0, -1.0];

    let sharpness_factor = sharpness as f32 / 100.0;

    for y in 1..height - 1 {
        for x in 1..width - 1 {
            let mut new_pixel = [0.0; 4];
            for ky in 0..3 {
                for kx in 0..3 {
                    let pixel = rgba_img.get_pixel(x + kx - 1, y + ky - 1);
                    for c in 0..3 {
                        new_pixel[c] += pixel[c] as f32 * kernel[(ky * 3 + kx) as usize];
                    }
                }
            }
            let original = rgba_img.get_pixel(x, y);
            for c in 0..3 {
                new_pixel[c] =
                    original[c] as f32 * (1.0 - sharpness_factor) + new_pixel[c] * sharpness_factor;
                new_pixel[c] = new_pixel[c].max(0.0).min(255.0);
            }
            new_pixel[3] = original[3] as f32;
            sharpened.put_pixel(
                x,
                y,
                Rgba([
                    new_pixel[0] as u8,
                    new_pixel[1] as u8,
                    new_pixel[2] as u8,
                    new_pixel[3] as u8,
                ]),
            );
        }
    }

    DynamicImage::ImageRgba8(sharpened)
}

#[allow(dead_code)]
pub fn apply_vignette(img: &DynamicImage, vignette: i32) -> DynamicImage {
    let mut vignetted = img.to_rgba8();
    let (width, height) = vignetted.dimensions();
    let center_x = width as f32 / 2.0;
    let center_y = height as f32 / 2.0;
    let max_dist = (center_x.powi(2) + center_y.powi(2)).sqrt();
    let factor = vignette as f32 / 100.0;

    for (x, y, pixel) in vignetted.enumerate_pixels_mut() {
        let dist = ((x as f32 - center_x).powi(2) + (y as f32 - center_y).powi(2)).sqrt();
        let vignette_factor = 1.0 - (dist / max_dist * factor).clamp(0.0, 1.0); // Smooth falloff

        for c in 0..3 {
            pixel[c] = ((pixel[c] as f32 * vignette_factor).clamp(0.0, 255.0)) as u8;
        }
    }

    DynamicImage::ImageRgba8(vignetted)
}

#[allow(dead_code)]
pub fn apply_highlights(img: &DynamicImage, highlights: i32) -> DynamicImage {
    let mut highlighted = img.to_rgb8();
    let factor = highlights as f32 / 100.0;

    for pixel in highlighted.pixels_mut() {
        for c in 0..3 {
            let value = pixel[c] as f32;
            if value > 128.0 {
                let alpha = ((value - 128.0) / 127.0) * factor;
                // Blend the original value with white (255) based on alpha
                let new_value = value * (1.0 - alpha) + 255.0 * alpha;
                pixel[c] = new_value.clamp(0.0, 255.0) as u8;
            }
        }
    }

    DynamicImage::ImageRgb8(highlighted)
}

pub fn get_secure_folder_path() -> Result<PathBuf, String> {
    let project_dirs = ProjectDirs::from("com", "AOSSIE", "Pictopy")
        .ok_or_else(|| "Failed to get project directories".to_string())?;
    let mut path = project_dirs.data_dir().to_path_buf();
    path.push(SECURE_FOLDER_NAME);
    Ok(path)
}

pub fn generate_salt() -> [u8; SALT_LENGTH] {
    let mut salt = [0u8; SALT_LENGTH];
    SystemRandom::new().fill(&mut salt).unwrap();
    salt
}

#[tauri::command]
pub async fn move_to_secure_folder(path: String, password: String) -> Result<(), String> {
    let secure_folder = get_secure_folder_path()?;
    let file_name = Path::new(&path).file_name().ok_or("Invalid file name")?;
    let dest_path = secure_folder.join(file_name);

    let content = fs::read(&path).map_err(|e| e.to_string())?;
    let ciphertext_length = content.len() + AES_256_GCM.tag_len();
    let _expected_length = SALT_LENGTH + NONCE_LENGTH + ciphertext_length + 16;
    let encrypted = encrypt_data(&content, &password).map_err(|e| e.to_string())?;
    println!("Encrypted file size: {}", encrypted.len());
    fs::write(&dest_path, encrypted).map_err(|e| e.to_string())?;
    println!("Encrypted file saved to: {:?}", secure_folder);
    fs::remove_file(&path).map_err(|e| e.to_string())?;

    let thumbnails_folder = Path::new(&path)
        .parent() // Get parent directory of the original file
        .and_then(|parent| parent.join("PictoPy.thumbnails").canonicalize().ok()) // Navigate to PictoPy.thumbnails
        .ok_or("Unable to locate thumbnails directory")?;
    let thumbnail_path = thumbnails_folder.join(file_name);

    if thumbnail_path.exists() {
        fs::remove_file(&thumbnail_path).map_err(|e| e.to_string())?;
        println!("Thumbnail deleted: {:?}", thumbnail_path);
    } else {
        println!("Thumbnail not found: {:?}", thumbnail_path);
    }

    // Store the original path
    let metadata_path = secure_folder.join("metadata.json");
    let mut metadata: HashMap<String, String> = if metadata_path.exists() {
        serde_json::from_str(&fs::read_to_string(&metadata_path).map_err(|e| e.to_string())?)
            .map_err(|e| e.to_string())?
    } else {
        HashMap::new()
    };
    metadata.insert(file_name.to_string_lossy().to_string(), path);
    fs::write(&metadata_path, serde_json::to_string(&metadata).unwrap())
        .map_err(|e| e.to_string())?;

    Ok(())
}

#[tauri::command]
pub async fn remove_from_secure_folder(file_name: String, password: String) -> Result<(), String> {
    let secure_folder = get_secure_folder_path()?;
    let file_path = secure_folder.join(&file_name);
    let metadata_path = secure_folder.join("metadata.json");

    // Read and decrypt the file
    let encrypted_content = fs::read(&file_path).map_err(|e| e.to_string())?;
    let decrypted_content =
        decrypt_data(&encrypted_content, &password).map_err(|e| e.to_string())?;

    // Get the original path
    let metadata: HashMap<String, String> =
        serde_json::from_str(&fs::read_to_string(&metadata_path).map_err(|e| e.to_string())?)
            .map_err(|e| e.to_string())?;
    let original_path = metadata.get(&file_name).ok_or("Original path not found")?;

    // Write the decrypted content back to the original path
    fs::write(original_path, decrypted_content).map_err(|e| e.to_string())?;

    // Remove the file from the secure folder and update metadata
    fs::remove_file(&file_path).map_err(|e| e.to_string())?;
    let mut updated_metadata = metadata;
    updated_metadata.remove(&file_name);
    fs::write(
        &metadata_path,
        serde_json::to_string(&updated_metadata).unwrap(),
    )
    .map_err(|e| e.to_string())?;

    Ok(())
}

#[tauri::command]
pub async fn create_secure_folder(password: String) -> Result<(), String> {
    let secure_folder = get_secure_folder_path()?;
    fs::create_dir_all(&secure_folder).map_err(|e| e.to_string())?;
    println!("Secure folder path: {:?}", secure_folder);

    let salt = generate_salt();
    let hashed_password = hash_password(&password, &salt);

    let config_path = secure_folder.join("config.json");
    let config = serde_json::json!({
        "salt": BASE64.encode(&salt),
        "hashed_password": BASE64.encode(&hashed_password),
    });
    fs::write(config_path, serde_json::to_string(&config).unwrap()).map_err(|e| e.to_string())?;

    let nomedia_path = secure_folder.join(".nomedia");
    fs::write(nomedia_path, "").map_err(|e| e.to_string())?;

    Ok(())
}

#[tauri::command]
pub async fn get_secure_media(password: String) -> Result<Vec<SecureMedia>, String> {
    let secure_folder = get_secure_folder_path()?;
    let mut secure_media = Vec::new();

    for entry in fs::read_dir(secure_folder).map_err(|e| e.to_string())? {
        let entry = entry.map_err(|e| e.to_string())?;
        let path = entry.path();

        if path.is_file()
            && path
                .extension()
                .map_or(false, |ext| ext == "jpg" || ext == "png")
        {
            let content = fs::read(&path).map_err(|e| e.to_string())?;
            let decrypted = decrypt_data(&content, &password).map_err(|e| e.to_string())?;

            let temp_dir = std::env::temp_dir();
            let temp_file = temp_dir.join(path.file_name().unwrap());
            fs::write(&temp_file, decrypted).map_err(|e| e.to_string())?;
            println!("SecureMedia: {:?}", path.to_string_lossy().to_string());
            println!("SecureMedia: {:?}", temp_file.to_string_lossy().to_string());

            secure_media.push(SecureMedia {
                id: path.file_name().unwrap().to_string_lossy().to_string(),
                url: format!("file://{}", temp_file.to_string_lossy()),
                path: path.to_string_lossy().to_string(),
            });
        }
    }

    println!("SECURE MEDIA: {:?}", secure_media.len());

    Ok(secure_media)
}

pub fn hash_password(password: &str, salt: &[u8]) -> Vec<u8> {
    let mut hash = [0u8; digest::SHA256_OUTPUT_LEN];
    pbkdf2::derive(
        pbkdf2::PBKDF2_HMAC_SHA256,
        NonZeroU32::new(100_000).unwrap(),
        salt,
        password.as_bytes(),
        &mut hash,
    );
    hash.to_vec()
}

pub fn encrypt_data(data: &[u8], password: &str) -> Result<Vec<u8>, ring::error::Unspecified> {
    let salt = generate_salt();
    let key = derive_key(password, &salt);
    let nonce = generate_nonce();

    let mut in_out = data.to_vec();
    let tag = key.seal_in_place_separate_tag(
        Nonce::assume_unique_for_key(nonce),
        Aad::empty(),
        &mut in_out,
    )?;

    let mut result = Vec::new();
    result.extend_from_slice(&salt);
    result.extend_from_slice(&nonce);
    result.extend_from_slice(&in_out);
    result.extend_from_slice(tag.as_ref());

    Ok(result)
}

pub fn decrypt_data(encrypted: &[u8], password: &str) -> Result<Vec<u8>, String> {
    println!("Decrypting data...");

    if encrypted.len() < SALT_LENGTH + NONCE_LENGTH + 16 {
        return Err(format!(
            "Encrypted data too short: {} bytes",
            encrypted.len()
        ));
    }

    let salt = &encrypted[..SALT_LENGTH];
    let nonce = &encrypted[SALT_LENGTH..SALT_LENGTH + NONCE_LENGTH];
    let tag_len = 16;
    let (ciphertext, tag) = encrypted[SALT_LENGTH + NONCE_LENGTH..]
        .split_at(encrypted.len() - SALT_LENGTH - NONCE_LENGTH - tag_len);

    let key = derive_key(password, salt);
    let nonce = match Nonce::try_assume_unique_for_key(nonce) {
        Ok(n) => n,
        Err(e) => return Err(format!("Nonce error: {:?}", e)),
    };

    let mut plaintext = ciphertext.to_vec();
    plaintext.extend_from_slice(tag);

    match key.open_in_place(nonce, Aad::empty(), &mut plaintext) {
        Ok(decrypted) => {
            println!(
                "Decryption successful! Decrypted length: {}",
                decrypted.len()
            );
            Ok(decrypted.to_vec())
        }
        Err(e) => Err(format!("Decryption error: {:?}", e)),
    }
}

#[tauri::command]
pub async fn unlock_secure_folder(password: String) -> Result<bool, String> {
    let secure_folder = get_secure_folder_path()?;
    let config_path = secure_folder.join("config.json");

    if !config_path.exists() {
        return Err("Secure folder not set up".to_string());
    }

    let config: serde_json::Value =
        serde_json::from_str(&fs::read_to_string(config_path).map_err(|e| e.to_string())?)
            .map_err(|e| e.to_string())?;

    let salt = BASE64
        .decode(config["salt"].as_str().ok_or("Invalid salt")?.as_bytes())
        .map_err(|e| e.to_string())?;
    let stored_hash = BASE64
        .decode(
            config["hashed_password"]
                .as_str()
                .ok_or("Invalid hash")?
                .as_bytes(),
        )
        .map_err(|e| e.to_string())?;

    let input_hash = hash_password(&password, &salt);

    Ok(input_hash == stored_hash)
}

pub fn derive_key(password: &str, salt: &[u8]) -> LessSafeKey {
    let mut key_bytes = [0u8; 32];
    pbkdf2::derive(
        pbkdf2::PBKDF2_HMAC_SHA256,
        NonZeroU32::new(100_000).unwrap(),
        salt,
        password.as_bytes(),
        &mut key_bytes,
    );

    let unbound_key = UnboundKey::new(&AES_256_GCM, &key_bytes).unwrap();
    LessSafeKey::new(unbound_key)
}

#[tauri::command]
pub async fn check_secure_folder_status() -> Result<bool, String> {
    let secure_folder = get_secure_folder_path()?;
    let config_path = secure_folder.join("config.json");
    Ok(config_path.exists())
}

pub fn generate_nonce() -> [u8; NONCE_LENGTH] {
    let mut nonce = [0u8; NONCE_LENGTH];
    SystemRandom::new().fill(&mut nonce).unwrap();
    nonce
}

#[tauri::command]
pub fn get_random_memories(
    directories: Vec<String>,
    count: usize,
) -> Result<Vec<MemoryImage>, String> {
    let mut all_images = Vec::new();
    let mut used_paths = HashSet::new();

    for dir in directories {
        let images = get_images_from_directory(&dir)?;
        all_images.extend(images);
    }

    let mut rng = rand::thread_rng();
    all_images.shuffle(&mut rng);

    let selected_images = all_images
        .into_iter()
        .filter(|img| used_paths.insert(img.path.clone()))
        .take(count)
        .collect();

    Ok(selected_images)
}

pub fn get_images_from_directory(dir: &str) -> Result<Vec<MemoryImage>, String> {
    let path = Path::new(dir);
    if !path.is_dir() {
        return Err(format!("{} is not a directory", dir));
    }

    let mut images = Vec::new();

    for entry in std::fs::read_dir(path).map_err(|e| e.to_string())? {
        let entry = entry.map_err(|e| e.to_string())?;
        let path = entry.path();

        if path.is_dir() {
            // Recursively call get_images_from_directory for subdirectories
            let sub_images = get_images_from_directory(path.to_str().unwrap())?;
            images.extend(sub_images);
        } else if path.is_file() && is_image_file(&path) {
            if let Ok(metadata) = std::fs::metadata(&path) {
                if let Ok(created) = metadata.created() {
                    let created_at: DateTime<Utc> = created.into();
                    images.push(MemoryImage {
                        path: path.to_string_lossy().into_owned(),
                        created_at,
                    });
                }
            }
        }
    }

    Ok(images)
}

pub fn is_image_file(path: &Path) -> bool {
    let extensions = ["jpg", "jpeg", "png", "gif"];
    path.extension()
        .and_then(|ext| ext.to_str())
        .map(|ext| extensions.contains(&ext.to_lowercase().as_str()))
        .unwrap_or(false)
}

#[tauri::command]
pub fn delete_cache(cache_service: State<'_, CacheService>) -> bool {
    cache_service.delete_all_caches()
}

#[tauri::command]
pub async fn set_wallpaper(path: String) -> Result<(), String> {
    let uri = format!("file://{}", path);
    println!("Setting wallpaper to: {}", uri);
    #[cfg(target_os = "windows")]
    {
        use std::ffi::OsStr;
        use std::os::windows::ffi::OsStrExt;
        use winapi::um::winuser::{
            SystemParametersInfoW, SPIF_SENDCHANGE, SPIF_UPDATEINIFILE, SPI_SETDESKWALLPAPER,
        };

        let wide: Vec<u16> = OsStr::new(&path).encode_wide().chain(Some(0)).collect();
        let result = unsafe {
            SystemParametersInfoW(
                SPI_SETDESKWALLPAPER,
                0,
                wide.as_ptr() as *mut _,
                SPIF_UPDATEINIFILE | SPIF_SENDCHANGE,
            )
        };

        if result == 0 {
            return Err("Failed to set wallpaper".to_string());
        }
    }

    #[cfg(target_os = "macos")]
    {
        let script = format!(
            r#"tell application "Finder" to set desktop picture to POSIX file "{}""#,
            path
        );
        let output = Command::new("osascript")
            .arg("-e")
            .arg(&script)
            .output()
            .map_err(|e| e.to_string())?;

        if !output.status.success() {
            return Err(String::from_utf8_lossy(&output.stderr).to_string());
        }
    }

    #[cfg(target_os = "linux")]
    {
        // This assumes a GNOME-based desktop environment
        let desktop_env = std::env::var("XDG_CURRENT_DESKTOP")
            .unwrap_or_default()
            .to_lowercase();

        if desktop_env.contains("gnome") {
            let output = Command::new("gsettings")
                .args(&[
                    "set",
                    "org.gnome.desktop.background",
                    "picture-uri",
                    &format!("file://{}", path),
                ])
                .output()
                .map_err(|e| e.to_string())?;

            if !output.status.success() {
                return Err(String::from_utf8_lossy(&output.stderr).to_string());
            }
        } else if desktop_env.contains("kde") {
            let script = format!(
                r#"qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript 'var allDesktops = desktops(); for (i=0; i<allDesktops.length; i++) {{ allDesktops[i].wallpaperPlugin = "org.kde.image"; allDesktops[i].currentConfigGroup = Array("Wallpaper", "org.kde.image", "General"); allDesktops[i].writeConfig("Image", "file://{}"); }}'"#,
                path
            );
            let output = Command::new("sh")
                .arg("-c")
                .arg(&script)
                .output()
                .map_err(|e| e.to_string())?;

            if !output.status.success() {
                return Err(String::from_utf8_lossy(&output.stderr).to_string());
            }
        } else {
            return Err("Unsupported desktop environment".to_string());
        }
    }

    Ok(())
}

#[tauri::command]
pub async fn open_folder(path: String) -> Result<(), String> {
    let parent = std::path::Path::new(&path)
        .parent()
        .ok_or_else(|| "Unable to get parent directory".to_string())?;

    #[cfg(target_os = "windows")]
    {
        Command::new("explorer")
            .arg(parent)
            .spawn()
            .map_err(|e| e.to_string())?;
    }

    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(parent)
            .spawn()
            .map_err(|e| e.to_string())?;
    }

    #[cfg(target_os = "linux")]
    {
        Command::new("xdg-open")
            .arg(parent)
            .spawn()
            .map_err(|e| e.to_string())?;
    }

    Ok(())
}

#[tauri::command]
pub async fn open_with(path: String) -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        Command::new("rundll32.exe")
            .args(["shell32.dll,OpenAs_RunDLL", &path])
            .spawn()
            .map_err(|e| e.to_string())?;
    }

    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .args(&["-a", &path])
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
pub fn get_cache_stats() -> CacheStats {
    IMAGE_CACHE.get_stats()
}

#[tauri::command]
pub fn reset_cache_stats() -> bool {
    IMAGE_CACHE.reset_stats();
    true
}

#[tauri::command]
pub fn clear_image_cache() -> usize {
    IMAGE_CACHE.clear()
}

#[tauri::command]
pub fn prune_image_cache_by_age(hours: u64) -> usize {
    let max_age = Duration::from_secs(hours * 3600);
    IMAGE_CACHE.prune_by_age(max_age)
}

#[tauri::command]
pub fn configure_image_cache(
    max_items: usize,
    max_memory_mb: usize,
    default_ttl_seconds: u64,
) -> bool {
    let config = crate::cache::CacheConfig {
        max_items,
        max_memory_bytes: max_memory_mb * 1024 * 1024,
        default_ttl_seconds,
    };

    IMAGE_CACHE.configure(config);
    true
}

#[tauri::command]
pub fn get_image_cache_config() -> crate::cache::CacheConfig {
    IMAGE_CACHE.get_config()
}

#[tauri::command]
pub fn invalidate_cache_entry(key: &str) -> bool {
    IMAGE_CACHE.invalidate(key)
}

#[tauri::command]
pub fn invalidate_cache_by_prefix(prefix: &str) -> usize {
    IMAGE_CACHE.invalidate_by_prefix(prefix)
}

#[tauri::command]
pub fn put_image_with_ttl(
    key: String,
    image_data: Vec<u8>,
    ttl_seconds: u64,
) -> Result<(), String> {
    let img = image::load_from_memory(&image_data).map_err(|e| e.to_string())?;
    let ttl = Some(std::time::Duration::from_secs(ttl_seconds));
    IMAGE_CACHE.put_with_ttl(key, img, ttl)
}

#[tauri::command]
pub fn invalidate_cache_by_pattern(pattern: &str) -> Result<usize, String> {
    IMAGE_CACHE.invalidate_by_pattern(pattern)
}

#[tauri::command]
pub fn preload_common_operations(image_data: Vec<u8>) -> Result<usize, String> {
    let img = image::load_from_memory(&image_data).map_err(|e| e.to_string())?;
    IMAGE_CACHE.preload_common_operations(&img)
}

#[tauri::command]
pub fn get_cache_entries_by_prefix(
    prefix: &str,
    limit: usize,
    offset: usize,
) -> Vec<(String, usize, u64)> {
    IMAGE_CACHE
        .get_entries_by_prefix(prefix, limit, offset)
        .into_iter()
        .map(|(key, size, time)| (key, size, time.elapsed().as_secs()))
        .collect()
}

// Add new Tauri commands for monitoring and statistics

#[tauri::command]
pub fn get_detailed_cache_stats() -> CacheStats {
    IMAGE_CACHE.get_stats()
}

#[tauri::command]
pub fn export_cache_stats() -> Result<String, String> {
    IMAGE_CACHE.export_stats()
}

#[tauri::command]
pub fn get_cache_performance_log() -> Vec<(String, u128)> {
    IMAGE_CACHE.get_performance_log()
}

#[tauri::command]
pub fn analyze_cache_usage() -> HashMap<String, usize> {
    IMAGE_CACHE.analyze_cache_usage()
}

#[tauri::command]
pub fn optimize_cache_config() -> crate::cache::CacheConfig {
    // Analyze current usage and suggest optimal configuration
    let stats = IMAGE_CACHE.get_stats();
    let current_config = IMAGE_CACHE.get_config();

    // Simple heuristic: if hit ratio is low, increase cache size
    // if memory utilization is low, decrease max memory
    let mut optimal_config = current_config.clone();

    if stats.cache_hit_ratio < 0.7 && stats.memory_utilization_percent > 90.0 {
        // Hit ratio is low and memory is nearly full - increase cache size
        optimal_config.max_memory_bytes = (current_config.max_memory_bytes as f64 * 1.5) as usize;
        optimal_config.max_items = (current_config.max_items as f64 * 1.5) as usize;
    } else if stats.cache_hit_ratio > 0.9 && stats.memory_utilization_percent < 50.0 {
        // High hit ratio with low memory utilization - decrease cache size
        optimal_config.max_memory_bytes = (current_config.max_memory_bytes as f64 * 0.8) as usize;
    }

    // Ensure reasonable limits
    optimal_config.max_memory_bytes = optimal_config.max_memory_bytes.max(10 * 1024 * 1024); // Min 10MB
    optimal_config.max_items = optimal_config.max_items.max(100); // Min 100 items

    optimal_config
}

// Add documentation for the image processing system
#[tauri::command]
pub fn get_image_processing_documentation() -> HashMap<String, String> {
    let mut docs = HashMap::new();

    docs.insert("overview".to_string(), 
        "The image processing system uses a multi-layered approach with LUT-based transformations, \
        parallel processing with Rayon, and an intelligent caching system to optimize performance.".to_string());

    docs.insert(
        "cache_usage".to_string(),
        "The cache system stores processed images to avoid redundant calculations. \
        It uses LRU eviction policy, size limits, and time-based expiration."
            .to_string(),
    );

    docs.insert(
        "performance_tips".to_string(),
        "For best performance: 1) Use the same image dimensions when possible, \
        2) Preload common operations for frequently used images, \
        3) Configure cache size based on available memory."
            .to_string(),
    );

    docs.insert(
        "commands".to_string(),
        "Available commands: configure_image_cache, get_image_cache_config, \
        clear_image_cache, prune_image_cache_by_age, invalidate_cache_entry, \
        invalidate_cache_by_pattern, get_cache_stats, reset_cache_stats, \
        get_detailed_cache_stats, export_cache_stats, analyze_cache_usage, \
        optimize_cache_config."
            .to_string(),
    );

    docs
}

#[tauri::command]
pub fn sync_with_python_cache(image_path: &str) -> Result<(), String> {
    IMAGE_CACHE.sync_with_python_cache(image_path)
}

#[tauri::command]
pub fn preload_with_python(image_path: &str) -> Result<(), String> {
    IMAGE_CACHE.preload_with_python(image_path)
}

#[tauri::command]
pub fn run_diagnostics() -> HashMap<String, String> {
    let mut results = HashMap::new();

    // Test SIMD capabilities
    #[cfg(target_arch = "x86_64")]
    {
        results.insert("cpu_architecture".to_string(), "x86_64".to_string());
        results.insert(
            "avx2_support".to_string(),
            is_x86_feature_detected!("avx2").to_string(),
        );
    }

    #[cfg(not(target_arch = "x86_64"))]
    {
        results.insert("cpu_architecture".to_string(), "non-x86_64".to_string());
        results.insert("avx2_support".to_string(), "false".to_string());
    }

    // Test image processing performance
    let width = 500;
    let height = 500;
    let mut img = RgbImage::new(width, height);

    // Fill with a gradient
    for y in 0..height {
        for x in 0..width {
            let pixel = image::Rgb([x as u8 % 255, y as u8 % 255, 128]);
            img.put_pixel(x, y, pixel);
        }
    }

    let dynamic_img = DynamicImage::ImageRgb8(img);

    // Measure performance
    let start = Instant::now();
    let _ = crate::image_processing::adjust_brightness_contrast(&dynamic_img, 10, 20);
    let duration = start.elapsed();

    results.insert(
        "processing_time_ms".to_string(),
        duration.as_millis().to_string(),
    );

    // Test TimeSeriesData
    let ts = crate::cache::TimeSeriesData::new();
    let viz_data = ts.get_visualization_data();

    results.insert(
        "time_series_points".to_string(),
        viz_data.labels.len().to_string(),
    );

    // Test cache configuration
    let cache_config = IMAGE_CACHE.get_config();
    results.insert(
        "cache_max_items".to_string(),
        cache_config.max_items.to_string(),
    );
    results.insert(
        "cache_max_memory_mb".to_string(),
        (cache_config.max_memory_bytes / (1024 * 1024)).to_string(),
    );

    results
}
