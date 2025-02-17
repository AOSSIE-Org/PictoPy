use crate::models::FileType;
use crate::repositories::FileRepository;
use std::path::PathBuf;

pub struct FileService;

impl FileService {
    pub fn new() -> Self {
        FileService
    }

    pub fn get_folders_with_images(&self, directory: &str) -> Vec<PathBuf> {
        FileRepository::get_files_in_directory(directory)
            .into_iter()
            .filter(|file| matches!(file.file_type, FileType::Image))
            .map(|file| file.path.parent().unwrap().to_owned())
            .collect::<std::collections::HashSet<_>>()
            .into_iter()
            .collect()
    }

    pub fn get_images_in_folder(&self, folder_path: &str) -> Vec<PathBuf> {
        FileRepository::get_files_in_directory(folder_path)
            .into_iter()
            .filter(|file| matches!(file.file_type, FileType::Image))
            .map(|file| file.path)
            .collect()
    }

    pub fn get_all_images(&self, directory: &str) -> Vec<PathBuf> {
        FileRepository::get_files_in_directory(directory)
            .into_iter()
            .filter(|file| matches!(file.file_type, FileType::Image))
            .map(|file| file.path)
            .collect()
    }

    pub fn get_all_videos(&self, directory: &str) -> Vec<PathBuf> {
        FileRepository::get_files_in_directory(directory)
            .into_iter()
            .filter(|file| matches!(file.file_type, FileType::Video))
            .map(|file| file.path)
            .collect()
    }
}
