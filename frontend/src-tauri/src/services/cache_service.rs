use crate::repositories::CacheRepository;
use std::path::PathBuf;

const FOLDERS_CACHE_FILE_PATH: &str = "folders_cache.txt";
const IMAGES_CACHE_FILE_PATH: &str = "images_cache.txt";
const VIDEOS_CACHE_FILE_PATH: &str = "videos_cache.txt";

pub struct CacheService;

impl CacheService {
    pub fn new() -> Self {
        CacheService
    }

    pub fn get_cached_folders(&self) -> Option<Vec<PathBuf>> {
        CacheRepository::read_cache(FOLDERS_CACHE_FILE_PATH)
    }

    pub fn cache_folders(&self, folders: &[PathBuf]) -> std::io::Result<()> {
        CacheRepository::write_cache(FOLDERS_CACHE_FILE_PATH, folders)
    }

    pub fn get_cached_images(&self) -> Option<Vec<PathBuf>> {
        CacheRepository::read_cache(IMAGES_CACHE_FILE_PATH)
    }

    pub fn cache_images(&self, images: &[PathBuf]) -> std::io::Result<()> {
        CacheRepository::write_cache(IMAGES_CACHE_FILE_PATH, images)
    }

    pub fn get_cached_videos(&self) -> Option<Vec<PathBuf>> {
        CacheRepository::read_cache(VIDEOS_CACHE_FILE_PATH)
    }

    pub fn cache_videos(&self, videos: &[PathBuf]) -> std::io::Result<()> {
        CacheRepository::write_cache(VIDEOS_CACHE_FILE_PATH, videos)
    }

    pub fn delete_all_caches(&self) -> bool {
        let mut success = false;

        if CacheRepository::delete_cache(FOLDERS_CACHE_FILE_PATH).is_ok() {
            success = true;
        }

        if CacheRepository::delete_cache(IMAGES_CACHE_FILE_PATH).is_ok() {
            success = true;
        }

        if CacheRepository::delete_cache(VIDEOS_CACHE_FILE_PATH).is_ok() {
            success = true;
        }

        success
    }
}
