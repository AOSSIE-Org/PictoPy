use image::{ImageFormat, imageops::FilterType};
use std::path::Path;
use tauri::command;
use urlencoding::decode;

#[derive(serde::Deserialize)]
pub struct CompressionOptions {
    max_width: Option<u32>,
    max_height: Option<u32>,
    quality: Option<u8>,
    maintain_aspect_ratio: Option<bool>,
}

#[command]
pub async fn compress_image(
    path: String, 
    options: Option<CompressionOptions>
) -> Result<String, String> {
    println!("Starting compression for path: {}", path);

    // Use default options if none provided
    let options = options.unwrap_or(CompressionOptions {
        max_width: Some(1920),
        max_height: Some(1080),
        quality: Some(80),
        maintain_aspect_ratio: Some(true),
    });

    // Decode the URL-encoded path and remove the asset:// protocol
    let decoded_path = decode(&path)
        .map_err(|e| format!("Failed to decode path: {}", e))?
        .into_owned()
        .replace("asset://localhost", "");

    println!("Decoded path: {}", decoded_path);

    // Validate input path
    let input_path = Path::new(&decoded_path);
    if !input_path.exists() {
        return Err(format!("File not found: {}", decoded_path));
    }

    // Get file components
    let file_stem = input_path
        .file_stem()
        .and_then(|s| s.to_str())
        .ok_or_else(|| "Invalid filename".to_string())?;
    
    let extension = input_path
        .extension()
        .and_then(|s| s.to_str())
        .map(|s| s.to_lowercase())
        .ok_or_else(|| "Invalid file extension".to_string())?;

    // Create output path in the same directory
    let output_path = input_path.with_file_name(format!("{}_compressed.{}", file_stem, extension));
    println!("Output path: {}", output_path.display());

    // Load image
    let img = image::open(&decoded_path)
        .map_err(|e| format!("Failed to open image: {}", e))?;

    println!("Original dimensions: {}x{}", img.width(), img.height());

    // Calculate new dimensions
    let (new_width, new_height) = if options.maintain_aspect_ratio.unwrap_or(true) {
        let aspect_ratio = img.width() as f32 / img.height() as f32;
        let max_width = options.max_width.unwrap_or(1920) as f32;
        let max_height = options.max_height.unwrap_or(1080) as f32;

        if img.width() > options.max_width.unwrap_or(1920) || 
           img.height() > options.max_height.unwrap_or(1080) {
            if aspect_ratio > max_width / max_height {
                let new_width = max_width;
                let new_height = new_width / aspect_ratio;
                (new_width as u32, new_height as u32)
            } else {
                let new_height = max_height;
                let new_width = new_height * aspect_ratio;
                (new_width as u32, new_height as u32)
            }
        } else {
            (img.width(), img.height())
        }
    } else {
        (
            options.max_width.unwrap_or(img.width()),
            options.max_height.unwrap_or(img.height())
        )
    };

    // Resize image if needed
    let resized = if new_width != img.width() || new_height != img.height() {
        println!("Resizing to: {}x{}", new_width, new_height);
        img.resize_exact(new_width, new_height, FilterType::Lanczos3)
    } else {
        println!("No resizing needed");
        img
    };

    // Save with format-specific handling
    let output_path_str = output_path
        .to_str()
        .ok_or_else(|| "Invalid output path".to_string())?
        .to_string();

    match extension.as_str() {
        "jpg" | "jpeg" => {
            let mut output = resized.into_rgb8();
            let mut encoder = image::codecs::jpeg::JpegEncoder::new_with_quality(
                std::fs::File::create(&output_path)
                    .map_err(|e| format!("Failed to create output file: {}", e))?,
                options.quality.unwrap_or(80)
            );
            encoder.encode(
                output.as_raw(),
                new_width,
                new_height,
                image::ColorType::Rgb8
            ).map_err(|e| format!("Failed to encode JPEG: {}", e))?;
        }
        "png" => {
            resized
                .save_with_format(&output_path, ImageFormat::Png)
                .map_err(|e| format!("Failed to save PNG: {}", e))?;
        }
        "webp" => {
            resized
                .save_with_format(&output_path, ImageFormat::WebP)
                .map_err(|e| format!("Failed to save WebP: {}", e))?;
        }
        _ => return Err(format!("Unsupported format: {}", extension)),
    }

    println!("Image successfully compressed and saved to: {}", output_path_str);
    Ok(output_path_str)
}