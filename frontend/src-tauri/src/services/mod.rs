use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::time::SystemTime;
use tauri::State;
mod cache_service;
mod file_service;
pub use cache_service::CacheService;
use chrono::{DateTime, Datelike, Utc};
use data_encoding::BASE64;
use directories::ProjectDirs;
pub use file_service::FileService;
use image::{DynamicImage, GenericImageView, ImageBuffer, Rgba};
use rand::seq::SliceRandom;
use ring::aead::{Aad, LessSafeKey, Nonce, UnboundKey, AES_256_GCM};
use ring::digest;
use ring::pbkdf2;
use ring::rand::{SecureRandom, SystemRandom};
use serde::{Deserialize, Serialize};
use std::collections::HashSet;
use std::fs;
use std::num::NonZeroU32;
use tauri::path::BaseDirectory;
use tauri::Manager;
use rayon::prelude::*;
use std::sync::Mutex;
use std::collections::HashMap;
use std::hash::{Hash, Hasher};
use std::collections::hash_map::DefaultHasher;
use lazy_static::lazy_static;
use lru::LruCache;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::num::NonZeroUsize;

// Constants for cache configuration
const MAX_CACHE_SIZE: usize = 100;  // Maximum number of cached images
const MAX_IMAGE_DIM: u32 = 4096;    // Maximum cached image dimension
const MAX_CACHE_MEMORY: usize = 1024 * 1024 * 1024;  // 1GB max cache size

pub const SECURE_FOLDER_NAME: &str = "secure_folder";
const SALT_LENGTH: usize = 16;
const NONCE_LENGTH: usize = 12;

#[derive(Clone)]
struct ImageAdjustment {
    brightness: i32,
    contrast: i32,
}

impl Hash for ImageAdjustment {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.brightness.hash(state);
        self.contrast.hash(state);
    }
}

lazy_static! {
    static ref IMAGE_CACHE: Mutex<LruCache<u64, DynamicImage>> = Mutex::new(
        LruCache::new(NonZeroUsize::new(MAX_CACHE_SIZE).unwrap())
    );
    static ref CURRENT_CACHE_MEMORY: AtomicUsize = AtomicUsize::new(0);
    static ref CACHE_HITS: AtomicUsize = AtomicUsize::new(0);
    static ref CACHE_MISSES: AtomicUsize = AtomicUsize::new(0);
    static ref CACHE_EVICTIONS: AtomicUsize = AtomicUsize::new(0);
    static ref TOTAL_PROCESSING_TIME: AtomicUsize = AtomicUsize::new(0);
}

fn calculate_image_memory_size(img: &DynamicImage) -> usize {
    img.width() as usize * img.height() as usize * 4  // 4 bytes per pixel (RGBA)
}

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

pub fn apply_sepia(img: &DynamicImage) -> DynamicImage {
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

pub fn adjust_brightness_contrast(img: &DynamicImage, brightness: i32, contrast: i32) -> DynamicImage {
    // Skip processing for extreme dimensions
    if img.width() > MAX_IMAGE_DIM || img.height() > MAX_IMAGE_DIM {
        return img.clone();
    }

    // Generate more robust cache key
    let mut hasher = DefaultHasher::new();
    let img_dimensions = format!("{}x{}", img.width(), img.height());
    let first_pixel = img.get_pixel(0, 0);
    format!("{}{:?}{}_{}", img_dimensions, first_pixel, brightness, contrast).hash(&mut hasher);
    let cache_key = hasher.finish();

    // Try cache first
    {
        let cache = IMAGE_CACHE.lock().unwrap();
        if let Some(cached_img) = cache.get(&cache_key) {
            return cached_img.clone();
        }
    }

    let (width, height) = img.dimensions();
    let mut adjusted_img = ImageBuffer::new(width, height);

    // Pre-calculate LUT using SIMD-friendly approach
    let brightness_factor = brightness as f32 / 100.0;
    let contrast_factor = (contrast as f32 + 100.0) / 100.0;
    let contrast_offset = 128.0 * (1.0 - contrast_factor);

    let lut: Vec<u8> = (0..256)
        .into_par_iter()
        .map(|i| {
            let color = i as f32;
            let adjusted = color * contrast_factor + contrast_offset;
            let with_brightness = adjusted + (255.0 * brightness_factor);
            with_brightness.max(0.0).min(255.0) as u8
        })
        .collect();

    // Process image in parallel chunks
    let chunk_size = (width * height / rayon::current_num_threads() as u32) as usize;
    adjusted_img
        .chunks_mut(chunk_size * 4)
        .enumerate()
        .par_bridge()
        .for_each(|(chunk_idx, chunk)| {
            let start_idx = chunk_idx * chunk_size;
            chunk
                .chunks_mut(4)
                .enumerate()
                .for_each(|(i, pixel_chunk)| {
                    let abs_idx = start_idx + i;
                    let x = (abs_idx as u32) % width;
                    let y = (abs_idx as u32) / width;
                    
                    if y < height {
                        let pixel = img.get_pixel(x, y);
                        pixel_chunk[0] = lut[pixel[0] as usize];
                        pixel_chunk[1] = lut[pixel[1] as usize];
                        pixel_chunk[2] = lut[pixel[2] as usize];
                        pixel_chunk[3] = pixel[3];
                    }
                });
        });

    let result = DynamicImage::ImageRgba8(adjusted_img);
    
    // Cache management
    let img_size = calculate_image_memory_size(&result);
    let mut cache = IMAGE_CACHE.lock().unwrap();
    
    // Check if we need to make space
    while CURRENT_CACHE_MEMORY.load(Ordering::Relaxed) + img_size > MAX_CACHE_MEMORY {
        if let Some((_, removed_img)) = cache.pop_lru() {
            let removed_size = calculate_image_memory_size(&removed_img);
            CURRENT_CACHE_MEMORY.fetch_sub(removed_size, Ordering::Relaxed);
        } else {
            break;
        }
    }
    
    // Add to cache if there's space
    if img_size <= MAX_CACHE_MEMORY {
        cache.put(cache_key, result.clone());
        CURRENT_CACHE_MEMORY.fetch_add(img_size, Ordering::Relaxed);
    }
    
    result
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
                url: format!("file://{}", temp_file.to_string_lossy().to_string()),
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
pub fn get_server_path(handle: tauri::AppHandle) -> Result<String, String> {
    let resource_path = handle
        .path()
        .resolve("resources/server", BaseDirectory::Resource)
        .map_err(|e| e.to_string())?;
    Ok(resource_path.to_string_lossy().to_string())
}

#[tauri::command]
pub fn clear_image_cache() {
    let mut cache = IMAGE_CACHE.lock().unwrap();
    cache.clear();
    CURRENT_CACHE_MEMORY.store(0, Ordering::Relaxed);
}

#[tauri::command]
pub fn get_cache_stats() -> Result<CacheStats, String> {
    let cache = IMAGE_CACHE.lock().map_err(|e| {
        error!("Failed to acquire cache lock for stats: {}", e);
        format!("Cache lock error: {}", e)
    })?;

    let current_memory = CURRENT_CACHE_MEMORY.load(Ordering::Relaxed);
    let hits = CACHE_HITS.load(Ordering::Relaxed);
    let misses = CACHE_MISSES.load(Ordering::Relaxed);
    let total_requests = hits + misses;
    let hit_rate = if total_requests > 0 {
        (hits as f64 / total_requests as f64) * 100.0
    } else {
        0.0
    };

    let stats = CacheStats {
        current_memory_bytes: current_memory,
        max_memory_bytes: MAX_CACHE_MEMORY,
        current_items: cache.len(),
        max_items: MAX_CACHE_SIZE,
        cache_hits: hits,
        cache_misses: misses,
        cache_evictions: CACHE_EVICTIONS.load(Ordering::Relaxed),
        hit_rate_percentage: hit_rate,
        memory_usage_percentage: (current_memory as f64 / MAX_CACHE_MEMORY as f64) * 100.0,
        average_processing_time_ms: if total_requests > 0 {
            TOTAL_PROCESSING_TIME.load(Ordering::Relaxed) as f64 / total_requests as f64
        } else {
            0.0
        },
    };

    debug!("Cache stats retrieved: {:?}", stats);
    Ok(stats)
}

#[tauri::command]
pub fn reset_cache_stats() -> Result<(), String> {
    CACHE_HITS.store(0, Ordering::Relaxed);
    CACHE_MISSES.store(0, Ordering::Relaxed);
    CACHE_EVICTIONS.store(0, Ordering::Relaxed);
    TOTAL_PROCESSING_TIME.store(0, Ordering::Relaxed);
    
    info!("Cache statistics reset");
    Ok(())
}

#[derive(Serialize)]
pub struct CacheStats {
    current_memory_bytes: usize,
    max_memory_bytes: usize,
    current_items: usize,
    max_items: usize,
    cache_hits: usize,
    cache_misses: usize,
    cache_evictions: usize,
    hit_rate_percentage: f64,
    memory_usage_percentage: f64,
    average_processing_time_ms: f64,
}

#[cfg(test)]
mod tests;
