use crate::models::{FileInfo, FileType};
use crate::utils::file_utils::{is_image_extension, is_video_extension};
use walkdir::WalkDir;

pub struct FileRepository;

impl FileRepository {
    pub fn get_files_in_directory(directory: &str) -> Vec<FileInfo> {
        WalkDir::new(directory)
            .into_iter()
            .filter_map(|e| e.ok())
            .filter(|e| {
                // Exclude the PictoPy.thumbnails directory
                !e.path()
                    .to_str()
                    .map_or(false, |path| path.contains("PictoPy.thumbnails"))
            })
            .filter(|e| e.file_type().is_file())
            .filter_map(|e| {
                e.path()
                    .extension()
                    .and_then(|ext| ext.to_str())
                    .map(|ext| {
                        let file_type = if is_image_extension(ext) {
                            FileType::Image
                        } else if is_video_extension(ext) {
                            FileType::Video
                        } else {
                            FileType::Other
                        };
                        FileInfo {
                            path: e.path().to_owned(),
                            file_type,
                        }
                    })
            })
            .collect()
    }
}
