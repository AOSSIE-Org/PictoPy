use std::collections::HashMap;
use std::path::{PathBuf, Path};
use std::time::SystemTime;
use tauri::State;
mod cache_service;
mod file_service;
pub use cache_service::CacheService;
use chrono::{DateTime, Datelike, Utc};
use data_encoding::BASE64;
use serde::{Serialize, Deserialize};
use std::num::NonZeroU32;
use ring::rand::{SystemRandom, SecureRandom};
use ring::digest;
use ring::pbkdf2;
use ring::aead::{self, Aad, LessSafeKey, Nonce, UnboundKey, AES_256_GCM};
pub use file_service::FileService;
use image::{DynamicImage, GenericImageView, ImageBuffer, Rgba};
use std::fs;  
use directories::ProjectDirs; 
 
const SECURE_FOLDER_NAME: &str = "secure_folder";
const SALT_LENGTH: usize = 16;
const NONCE_LENGTH: usize = 12;

#[derive(Serialize, Deserialize)]
pub struct SecureMedia {
    pub id: String,
    pub url: String,
    pub path: String,
    // pub base64_image: BASE64,
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

fn get_secure_folder_path() -> Result<PathBuf, String> {
    let project_dirs = ProjectDirs::from("com", "AOSSIE", "Pictopy")
        .ok_or_else(|| "Failed to get project directories".to_string())?;
    let mut path = project_dirs.data_dir().to_path_buf();
    path.push(SECURE_FOLDER_NAME);
    Ok(path)
}

fn generate_salt() -> [u8; SALT_LENGTH] {
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
    let expected_length = SALT_LENGTH + NONCE_LENGTH + ciphertext_length + 16;
    let encrypted = encrypt_data(&content, &password).map_err(|e| e.to_string())?;
    println!("Encrypted file size: {}", encrypted.len());
    fs::write(&dest_path, encrypted).map_err(|e| e.to_string())?;
    println!("Encrypted file saved to: {:?}", secure_folder);
    fs::remove_file(&path).map_err(|e| e.to_string())?;

    // Store the original path
    let metadata_path = secure_folder.join("metadata.json");
    let mut metadata: HashMap<String, String> = if metadata_path.exists() {
        serde_json::from_str(&fs::read_to_string(&metadata_path).map_err(|e| e.to_string())?).map_err(|e| e.to_string())?
    } else {
        HashMap::new()
    };
    metadata.insert(file_name.to_string_lossy().to_string(), path);
    fs::write(&metadata_path, serde_json::to_string(&metadata).unwrap()).map_err(|e| e.to_string())?;

    Ok(())
}

#[tauri::command]
pub async fn remove_from_secure_folder(file_name: String, password: String) -> Result<(), String> {
    let secure_folder = get_secure_folder_path()?;
    let file_path = secure_folder.join(&file_name);
    let metadata_path = secure_folder.join("metadata.json");

    // Read and decrypt the file
    let encrypted_content = fs::read(&file_path).map_err(|e| e.to_string())?;
    let decrypted_content = decrypt_data(&encrypted_content, &password).map_err(|e| e.to_string())?;

    // Get the original path
    let metadata: HashMap<String, String> = serde_json::from_str(&fs::read_to_string(&metadata_path).map_err(|e| e.to_string())?).map_err(|e| e.to_string())?;
    let original_path = metadata.get(&file_name).ok_or("Original path not found")?;

    // Write the decrypted content back to the original path
    fs::write(original_path, decrypted_content).map_err(|e| e.to_string())?;

    // Remove the file from the secure folder and update metadata
    fs::remove_file(&file_path).map_err(|e| e.to_string())?;
    let mut updated_metadata = metadata;
    updated_metadata.remove(&file_name);
    fs::write(&metadata_path, serde_json::to_string(&updated_metadata).unwrap()).map_err(|e| e.to_string())?;

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

        if path.is_file() && path.extension().map_or(false, |ext| ext == "jpg" || ext == "png") {
            let content = fs::read(&path).map_err(|e| e.to_string())?;
            let decrypted = decrypt_data(&content, &password).map_err(|e| e.to_string())?;

            let temp_dir = std::env::temp_dir();
            let temp_file = temp_dir.join(path.file_name().unwrap());
            fs::write(&temp_file, decrypted).map_err(|e| e.to_string())?;
            println!("SecureMedia: {:?}", path.to_string_lossy().to_string());
            println!("SecureMedia: {:?}", temp_file.to_string_lossy().to_string());
            
            secure_media.push(SecureMedia {
                id: path.file_name().unwrap().to_string_lossy().to_string(),
                url: format!("file://{}" , temp_file.to_string_lossy().to_string()),
                path: path.to_string_lossy().to_string(),
            });
        }
    }

    println!("SECURE MEDIA: {:?}" , secure_media.len());

    Ok(secure_media)
}

fn hash_password(password: &str, salt: &[u8]) -> Vec<u8> {
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

fn encrypt_data(data: &[u8], password: &str) -> Result<Vec<u8>, ring::error::Unspecified> {
    let salt = generate_salt();
    let key = derive_key(password, &salt);
    let nonce = generate_nonce();

    let mut in_out = data.to_vec();
    let tag = key.seal_in_place_separate_tag(
        Nonce::assume_unique_for_key(nonce),
        Aad::empty(),
        &mut in_out
    )?;

    let mut result = Vec::new();
    result.extend_from_slice(&salt);
    result.extend_from_slice(&nonce);
    result.extend_from_slice(&in_out);
    result.extend_from_slice(tag.as_ref());

    Ok(result)
}

fn decrypt_data(encrypted: &[u8], password: &str) -> Result<Vec<u8>, String> {
    println!("Decrypting data...");
    
    if encrypted.len() < SALT_LENGTH + NONCE_LENGTH + 16 {
        return Err(format!("Encrypted data too short: {} bytes", encrypted.len()));
    }

    let salt = &encrypted[..SALT_LENGTH];
    let nonce = &encrypted[SALT_LENGTH..SALT_LENGTH + NONCE_LENGTH];
    let tag_len = 16;
    let (ciphertext, tag) = encrypted[SALT_LENGTH + NONCE_LENGTH..].split_at(encrypted.len() - SALT_LENGTH - NONCE_LENGTH - tag_len);

    let key = derive_key(password, salt);
    let nonce = match Nonce::try_assume_unique_for_key(nonce) {
        Ok(n) => n,
        Err(e) => return Err(format!("Nonce error: {:?}", e)),
    };

    let mut plaintext = ciphertext.to_vec();
    plaintext.extend_from_slice(tag);

    match key.open_in_place(nonce, Aad::empty(), &mut plaintext) {
        Ok(decrypted) => {
            println!("Decryption successful! Decrypted length: {}", decrypted.len());
            Ok(decrypted.to_vec())
        },
        Err(e) => {
            Err(format!("Decryption error: {:?}", e))
        }
    }
}

#[tauri::command]
pub async fn unlock_secure_folder(password: String) -> Result<bool, String> {
    let secure_folder = get_secure_folder_path()?;
    let config_path = secure_folder.join("config.json");

    if !config_path.exists() {
        return Err("Secure folder not set up".to_string());
    }

    let config: serde_json::Value = serde_json::from_str(&fs::read_to_string(config_path).map_err(|e| e.to_string())?).map_err(|e| e.to_string())?;

    let salt = BASE64.decode(config["salt"].as_str().ok_or("Invalid salt")?.as_bytes()).map_err(|e| e.to_string())?;
    let stored_hash = BASE64.decode(config["hashed_password"].as_str().ok_or("Invalid hash")?.as_bytes()).map_err(|e| e.to_string())?;

    let input_hash = hash_password(&password, &salt);

    Ok(input_hash == stored_hash)
}

fn derive_key(password: &str, salt: &[u8]) -> LessSafeKey {
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

fn generate_nonce() -> [u8; NONCE_LENGTH] {
    let mut nonce = [0u8; NONCE_LENGTH];
    SystemRandom::new().fill(&mut nonce).unwrap();
    nonce
}

#[tauri::command]
pub fn delete_cache(cache_service: State<'_, CacheService>) -> bool {
    cache_service.delete_all_caches()
}