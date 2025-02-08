use std::fs::{File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use lazy_static::lazy_static;
use std::collections::HashMap;
use std::sync::Mutex;

pub struct CacheRepository;

lazy_static! {
    static ref MEMORY_CACHE: Mutex<HashMap<String, Vec<PathBuf>>> = Mutex::new(HashMap::new());
}

impl CacheRepository {
    pub fn read_cache(cache_file_path: &str) -> Option<Vec<PathBuf>> {
        {
            let cache = MEMORY_CACHE.lock().unwrap();
            if let Some(data) = cache.get(cache_file_path) {
                return Some(data.clone()); // Return from memory cache
            }
        }
        let data = File::open(cache_file_path).ok().map(|file| {
            let reader = BufReader::new(file);
            reader.lines()
                .filter_map(|line| line.ok().map(PathBuf::from))
                .collect()
        })?;
        MEMORY_CACHE.lock().unwrap().insert(cache_file_path.to_string(), data.clone());
        Some(data)
    }

    pub fn write_cache(cache_file_path: &str, paths: &[PathBuf]) -> std::io::Result<()> {
        let mut file = OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .open(cache_file_path)?;

        for path in paths {
            if let Some(path_str) = path.to_str() {
                writeln!(file, "{}", path_str)?;
            }
        }
        let mut cache = MEMORY_CACHE.lock().unwrap();
        cache.insert(cache_file_path.to_string(), paths.to_vec());
        Ok(())
    }

    pub fn delete_cache(cache_file_path: &str) -> std::io::Result<()> {
        std::fs::remove_file(cache_file_path)
        let mut cache = MEMORY_CACHE.lock().unwrap();
        cache.remove(cache_file_path);

        Ok(())
    }
}
