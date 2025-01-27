use fs2::FileExt;
use std::fs::{File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use fs2::FileExt;

pub struct CacheRepository;

impl CacheRepository {
    pub fn read_cache(cache_file_path: &str) -> Option<Vec<PathBuf>> {
        let file = File::open(cache_file_path).ok()?;
        let reader = BufReader::new(file);
        let paths: Vec<PathBuf> = reader
            .lines()
            .filter_map(|line| line.ok().map(PathBuf::from))
            .collect();
        Some(paths)
    }

    pub fn write_cache(cache_file_path: &str, paths: &[PathBuf]) -> std::io::Result<()> {
        let mut file = OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(true)
            .open(cache_file_path)?;
        
        file.lock_exclusive()?;

      
        file.lock_exclusive()?;

      
        for path in paths {
            if let Some(path_str) = path.to_str() {
                writeln!(file, "{}", path_str)?;
            }
        }

        fs2::FileExt::unlock(&file)?;
        Ok(())
    }

    pub fn delete_cache(cache_file_path: &str) -> std::io::Result<()> {
        std::fs::remove_file(cache_file_path)
    }
}