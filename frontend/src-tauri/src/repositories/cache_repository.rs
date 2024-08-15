use std::fs::{File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;

pub struct CacheRepository;

impl CacheRepository {
    pub fn read_cache(cache_file_path: &str) -> Option<Vec<PathBuf>> {
        File::open(cache_file_path).ok().map(|file| {
            let reader = BufReader::new(file);
            reader.lines()
                .filter_map(|line| line.ok().map(PathBuf::from))
                .collect()
        })
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
        Ok(())
    }

    pub fn delete_cache(cache_file_path: &str) -> std::io::Result<()> {
        std::fs::remove_file(cache_file_path)
    }
}
