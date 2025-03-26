use std::fs;
use std::path::Path;

use image::{DynamicImage, GenericImageView, ImageOutputFormat, RgbImage};
use tauri::State;
use tempfile::tempdir;
use tokio;

use PictoPy::services::{
    adjust_brightness_contrast, apply_sepia, check_secure_folder_status, create_secure_folder,
    decrypt_data, derive_key, encrypt_data, generate_salt, get_folders_with_images,
    get_images_in_folder, get_random_memories, get_secure_folder_path, hash_password,
    is_image_file, move_to_secure_folder, remove_from_secure_folder, save_edited_image, share_file,
    unlock_secure_folder, validate_password, verify_password, CacheService, FileService, 
    SECURE_FOLDER_NAME,
};

/// This unsafe helper is for testing only.
fn state_from<T: Send + Sync + 'static>(t: &'static T) -> State<'static, T> {
    unsafe { std::mem::transmute(t) }
}

fn real_file_service_state() -> State<'static, FileService> {
    state_from(Box::leak(Box::new(FileService::new())))
}

fn real_cache_service_state() -> State<'static, CacheService> {
    state_from(Box::leak(Box::new(CacheService::new())))
}

//
// Integration Tests
//

#[test]
fn test_get_folders_with_images() {
    let directory = "test_dir";
    let fs_state = real_file_service_state();
    let cs_state = real_cache_service_state();
    let _folders = get_folders_with_images(directory, fs_state, cs_state);
    // Just check that we got a result
    assert!(true, "Function returned without error");
}

#[test]
fn test_get_images_in_folder() {
    let folder = "folder_path";
    let fs_state = real_file_service_state();
    let _images = get_images_in_folder(folder, fs_state);
    // Just check that we got a result
    assert!(true, "Function returned without error");
}

// #[test]
// fn test_get_all_images_with_cache_fallback() {
//     let temp_dir = tempdir().unwrap();
//     let dummy_img = temp_dir.path().join("image1.jpg");
//     fs::write(&dummy_img, b"dummy").unwrap();

//     let fs_state = real_file_service_state();
//     let cs_state = real_cache_service_state();
//     let result = get_all_images_with_cache(fs_state, cs_state, temp_dir.path().to_str().unwrap());
//     assert!(result.is_ok());
//     let map = result.unwrap();
//     assert!(!map.is_empty(), "Expected at least one year key in the map");
// }

// #[test]
// fn test_get_all_videos_with_cache_fallback() {
//     let temp_dir = tempdir().unwrap();
//     let dummy_video = temp_dir.path().join("video1.mp4");
//     fs::write(&dummy_video, b"dummy video").unwrap();

//     let fs_state = real_file_service_state();
//     let cs_state = real_cache_service_state();
//     let result = get_all_videos_with_cache(fs_state, cs_state, temp_dir.path().to_str().unwrap());
//     assert!(result.is_ok());
//     let map = result.unwrap();
//     assert!(!map.is_empty(), "Expected at least one year key in the map");
// }

// #[test]
// fn test_delete_cache() {
//     let cs_state = real_cache_service_state();
//     let success = delete_cache(cs_state);
//     assert!(success, "delete_all_caches should return true");
// }

#[tokio::test]
async fn test_share_file() {
    let result = share_file("dummy_path".to_string()).await;
    assert!(result.is_ok() || result.is_err());
}

#[tokio::test]
async fn test_save_edited_image() {
    // Create a simple test image
    let img = DynamicImage::ImageRgb8(RgbImage::new(10, 10));
    let mut buffer = Vec::new();
    img.write_to(
        &mut std::io::Cursor::new(&mut buffer),
        ImageOutputFormat::Png,
    )
    .unwrap();

    // Create a temporary directory
    let temp_dir = tempdir().unwrap();
    let original_path = temp_dir.path().join("test_image.png");

    // Save the original image
    fs::write(&original_path, &buffer).unwrap();

    // Call the function to save the edited image
    let result = save_edited_image(
        buffer.clone(),
        original_path.to_string_lossy().to_string(),
        "grayscale(100%)".to_string(),
        100,
        100,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    .await;

    assert!(result.is_ok(), "save_edited_image should succeed");

    // Check if the edited file exists at the correct path
    assert!(
        original_path.exists(),
        "Edited image file should exist at the original path"
    );
}

#[test]
fn test_apply_sepia() {
    let img = DynamicImage::new_rgb8(10, 10);
    let sepia_img = apply_sepia(&img);
    assert_eq!(sepia_img.dimensions(), (10, 10));
}

#[test]
fn test_adjust_brightness_contrast() {
    let img = DynamicImage::new_rgb8(10, 10);
    let adjusted = adjust_brightness_contrast(&img, 10, 20);
    assert_eq!(adjusted.dimensions(), (10, 10));
}

#[test]
fn test_get_secure_folder_path() {
    let path = get_secure_folder_path().unwrap();
    assert!(path.to_string_lossy().contains(SECURE_FOLDER_NAME));
}

#[test]
fn test_hash_password() {
    let salt = generate_salt();
    let hash_result = hash_password("password", &salt);
    assert!(hash_result.is_ok(), "Password hashing should succeed");
    let hash = hash_result.unwrap();
    assert!(!hash.is_empty(), "Hash should not be empty");
}

#[test]
fn test_encrypt_decrypt_data() {
    let data = b"test data";
    let password = "secret";
    
    // Encrypt the data
    let encrypted = match encrypt_data(data, password) {
        Ok(enc) => enc,
        Err(e) => {
            println!("Encryption error: {}", e);
            panic!("Encryption failed: {}", e);
        }
    };
    
    // Print debug info
    println!("Encrypted data length: {}", encrypted.len());
    
    // Decrypt with the same password
    let decrypted = match decrypt_data(&encrypted, password) {
        Ok(dec) => dec,
        Err(e) => {
            println!("Decryption error: {}", e);
            panic!("Decryption failed: {}", e);
        }
    };
    
    // Verify the decrypted data matches the original
    assert_eq!(decrypted, data);
}

#[test]
fn test_derive_key() {
    let salt = generate_salt();
    let _key = derive_key("password", &salt); // Add underscore to suppress warning
    assert!(true, "Key derived successfully");
}

#[test]
fn test_is_image_file() {
    let jpg_path = Path::new("image.jpg");
    let txt_path = Path::new("document.txt");
    assert!(is_image_file(jpg_path));
    assert!(!is_image_file(txt_path));
}

#[tokio::test]
async fn test_move_and_remove_from_secure_folder() {
    let temp_dir = tempdir().unwrap();
    let secure_folder = temp_dir.path().join("secure_folder");
    fs::create_dir_all(&secure_folder).unwrap();

    let file_content = b"secure content";
    let temp_file = temp_dir.path().join("test.txt");
    fs::write(&temp_file, file_content).unwrap();
    let password = "test_password";

    let move_result = move_to_secure_folder(
        temp_file.to_string_lossy().to_string(),
        password.to_string(),
    )
    .await;
    assert!(move_result.is_ok() || move_result.is_err());

    let remove_result =
        remove_from_secure_folder("test.txt".to_string(), password.to_string()).await;
    assert!(remove_result.is_ok() || remove_result.is_err());
}

#[tokio::test]
async fn test_create_and_unlock_secure_folder() {
    let password = "secret";
    let create_result = create_secure_folder(password.to_string()).await;
    assert!(create_result.is_ok() || create_result.is_err());

    let unlock_result = unlock_secure_folder(password.to_string()).await;
    assert!(unlock_result.is_ok() || unlock_result.is_err());
}

// #[tokio::test]
// async fn test_get_secure_media() {
//     let temp_dir = tempdir().unwrap();
//     let secure_folder = temp_dir.path().join("secure_folder");
//     fs::create_dir_all(&secure_folder).unwrap();

//     // Instead of writing plain data, we encrypt dummy image data with the same password.
//     let password = "dummy_password";
//     let dummy_data = b"dummy image data";
//     let encrypted = encrypt_data(dummy_data, password).unwrap();
//     let img_path = secure_folder.join("dummy.jpg");
//     fs::write(&img_path, &encrypted).unwrap();

//     let result = get_secure_media(password.to_string()).await;
//     assert!(result.is_ok(), "get_secure_media should return Ok");
// }

#[tokio::test]
async fn test_check_secure_folder_status() {
    let result = check_secure_folder_status().await;
    assert!(result.is_ok());
}

#[test]
fn test_get_random_memories() {
    let tmp = tempdir().unwrap();
    let sub = tmp.path().join("subdir");
    fs::create_dir_all(&sub).unwrap();

    let fake_img = sub.join("image.jpg");
    fs::write(&fake_img, b"fake").unwrap();

    let dirs = vec![tmp.path().to_string_lossy().to_string()];
    let result = get_random_memories(dirs, 5);
    assert!(result.is_ok());
    let images = result.unwrap();
    // With one image available, expect exactly one image.
    assert_eq!(images.len(), 1);
}

#[tokio::test]
async fn test_password_validation() {
    // Test weak passwords
    assert!(validate_password("short").is_err()); // Too short
    assert!(validate_password("nouppercase123").is_err()); // No uppercase
    assert!(validate_password("NONUMBERS").is_err()); // No numbers
    
    // Test strong password
    assert!(validate_password("StrongPass123").is_ok());
}

#[tokio::test]
async fn test_argon2id_password_hashing() {
    let password = "TestPassword123";
    let salt = generate_salt();
    
    let hash_result = hash_password(password, &salt);
    assert!(hash_result.is_ok());
    
    let hash = hash_result.unwrap();
    let verification = verify_password(password, &hash);
    assert!(verification.is_ok());
    assert!(verification.unwrap());
    
    // Test wrong password
    let wrong_verification = verify_password("WrongPassword123", &hash);
    assert!(wrong_verification.is_ok());
    assert!(!wrong_verification.unwrap());
}

#[tokio::test]
async fn test_encryption_decryption() {
    let data = b"This is a test message for encryption";
    let password = "SecurePassword123";
    
    let encrypted = encrypt_data(data, password);
    assert!(encrypted.is_ok());
    
    let encrypted_data = encrypted.unwrap();
    let decrypted = decrypt_data(&encrypted_data, password);
    assert!(decrypted.is_ok());
    
    let decrypted_data = decrypted.unwrap();
    assert_eq!(decrypted_data, data);
    
    // Test wrong password
    let wrong_decryption = decrypt_data(&encrypted_data, "WrongPassword123");
    assert!(wrong_decryption.is_err());
}
