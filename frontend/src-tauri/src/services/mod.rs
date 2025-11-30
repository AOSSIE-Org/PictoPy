use tauri::path::BaseDirectory;
use tauri::Manager;
use std::fs::File;
use std::io::{Read, Write};
use std::path::Path;
use zip::write::FileOptions;
use zip::ZipWriter;
use std::process::Command;

#[tauri::command]
pub fn get_server_path(handle: tauri::AppHandle) -> Result<String, String> {
    let resource_path = handle
        .path()
        .resolve("resources/backend", BaseDirectory::Resource)
        .map_err(|e| e.to_string())?;
    Ok(resource_path.to_string_lossy().to_string())
}

#[tauri::command]
pub fn open_file_location(file_path: String) -> Result<(), String> {
    let path = Path::new(&file_path);
    let folder_path = path.parent()
        .ok_or("Failed to get parent directory")?;

    #[cfg(target_os = "windows")]
    {
        Command::new("explorer")
            .arg(folder_path)
            .spawn()
            .map_err(|e| format!("Failed to open folder: {}", e))?;
    }

    #[cfg(target_os = "macos")]
    {
        Command::new("open")
            .arg(folder_path)
            .spawn()
            .map_err(|e| format!("Failed to open folder: {}", e))?;
    }

    #[cfg(target_os = "linux")]
    {
        Command::new("xdg-open")
            .arg(folder_path)
            .spawn()
            .map_err(|e| format!("Failed to open folder: {}", e))?;
    }

    Ok(())
}

#[tauri::command]
pub async fn create_zip_from_images(
    image_paths: Vec<String>,
    output_path: String,
) -> Result<String, String> {
    let file = File::create(&output_path).map_err(|e| format!("Failed to create zip file: {}", e))?;
    let mut zip = ZipWriter::new(file);
    
    let options = FileOptions::default()
        .compression_method(zip::CompressionMethod::Deflated)
        .unix_permissions(0o755);

    for (index, image_path) in image_paths.iter().enumerate() {
        let path = Path::new(image_path);
        
        let default_name = format!("image_{}.jpg", index);
        let file_name = path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or(&default_name);

        let mut file = File::open(image_path)
            .map_err(|e| format!("Failed to open image {}: {}", image_path, e))?;
        
        let mut buffer = Vec::new();
        file.read_to_end(&mut buffer)
            .map_err(|e| format!("Failed to read image {}: {}", image_path, e))?;

        zip.start_file(file_name, options)
            .map_err(|e| format!("Failed to add file to zip: {}", e))?;
        zip.write_all(&buffer)
            .map_err(|e| format!("Failed to write file to zip: {}", e))?;
    }

    zip.finish().map_err(|e| format!("Failed to finalize zip: {}", e))?;

    Ok(output_path)
}
