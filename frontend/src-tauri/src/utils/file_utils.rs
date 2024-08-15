pub fn is_image_extension(extension: &str) -> bool {
    matches!(extension.to_lowercase().as_str(),
        "jpg" | "jpeg" | "png" | "gif" | "bmp" | "tiff" | "webp"
    )
}

pub fn is_video_extension(extension: &str) -> bool {
    matches!(extension.to_lowercase().as_str(),
        "mp4" | "avi" | "mkv" | "mov" | "flv"  | "m4v"
    )
}
