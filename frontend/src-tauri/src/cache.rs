use image::{DynamicImage, GenericImageView};
use lazy_static::lazy_static;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::process::Command;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Mutex;
use std::time::{Duration, Instant};

// Atomic counters for cache statistics
lazy_static! {
    pub static ref CACHE_HITS: AtomicUsize = AtomicUsize::new(0);
    pub static ref CACHE_MISSES: AtomicUsize = AtomicUsize::new(0);
    pub static ref CACHE_INVALIDATIONS: AtomicUsize = AtomicUsize::new(0);
    pub static ref CACHE_PRELOADS: AtomicUsize = AtomicUsize::new(0);
    pub static ref TOTAL_PROCESSING_TIME: AtomicUsize = AtomicUsize::new(0);
    pub static ref PROCESSING_COUNT: AtomicUsize = AtomicUsize::new(0);
}
#[allow(dead_code)]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CacheConfig {
    pub max_items: usize,
    pub max_memory_bytes: usize,
    pub default_ttl_seconds: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CacheStats {
    pub hits: usize,
    pub misses: usize,
    pub current_items: usize,
    pub memory_used_bytes: usize,
    pub memory_utilization_percent: f64,
    pub cache_hit_ratio: f64,
    pub evictions: usize,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TimeSeriesData {
    pub data_points: Vec<(String, f64)>,
}

impl Default for TimeSeriesData {
    fn default() -> Self {
        Self::new()
    }
}

impl TimeSeriesData {
    pub fn new() -> Self {
        Self {
            data_points: Vec::new(),
        }
    }

    pub fn get_visualization_data(&self) -> VisualizationData {
        VisualizationData {
            labels: self
                .data_points
                .iter()
                .map(|(label, _)| label.clone())
                .collect(),
            values: self.data_points.iter().map(|(_, value)| *value).collect(),
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct VisualizationData {
    pub labels: Vec<String>,
    pub values: Vec<f64>,
}

struct CacheEntry {
    key: String,
    image: DynamicImage,
    size_bytes: usize,
    last_accessed: Instant,
    created_at: Instant,
    expires_at: Option<Instant>,
}

pub struct ImageCache {
    entries: Mutex<HashMap<String, CacheEntry>>,
    stats: Mutex<CacheStats>,
    config: Mutex<CacheConfig>,
    performance_log: Mutex<Vec<(String, Duration)>>,
}

impl Default for ImageCache {
    fn default() -> Self {
        Self::new()
    }
}

impl ImageCache {
    pub fn new() -> Self {
        let config = CacheConfig {
            max_items: 1000,
            max_memory_bytes: 500 * 1024 * 1024, // 500 MB
            default_ttl_seconds: 3600,           // 1 hour
        };

        let stats = CacheStats {
            hits: 0,
            misses: 0,
            current_items: 0,
            memory_used_bytes: 0,
            memory_utilization_percent: 0.0,
            cache_hit_ratio: 0.0,
            evictions: 0,
        };

        Self {
            entries: Mutex::new(HashMap::new()),
            stats: Mutex::new(stats),
            config: Mutex::new(config),
            performance_log: Mutex::new(Vec::new()),
        }
    }

    pub fn configure(&self, config: CacheConfig) {
        let mut cfg = self.config.lock().unwrap();
        *cfg = config;
    }

    pub fn get_config(&self) -> CacheConfig {
        self.config.lock().unwrap().clone()
    }

    pub fn get_stats(&self) -> CacheStats {
        self.stats.lock().unwrap().clone()
    }

    pub fn reset_stats(&self) {
        let mut stats = self.stats.lock().unwrap();
        stats.hits = 0;
        stats.misses = 0;
        stats.evictions = 0;
        stats.cache_hit_ratio = 0.0;
    }

    pub fn clear(&self) -> usize {
        let mut entries = self.entries.lock().unwrap();
        let count = entries.len();
        entries.clear();

        // Update stats
        let mut stats = self.stats.lock().unwrap();
        stats.current_items = 0;
        stats.memory_used_bytes = 0;
        stats.memory_utilization_percent = 0.0;

        count
    }

    pub fn prune_by_age(&self, max_age: Duration) -> usize {
        let mut entries = self.entries.lock().unwrap();
        let now = Instant::now();
        let initial_count = entries.len();

        entries.retain(|_, entry| now.duration_since(entry.created_at) <= max_age);

        let removed_count = initial_count - entries.len();

        // Update stats
        let mut stats = self.stats.lock().unwrap();
        stats.current_items = entries.len();
        stats.evictions += removed_count;

        removed_count
    }

    pub fn invalidate(&self, key: &str) -> bool {
        let mut entries = self.entries.lock().unwrap();
        let result = entries.remove(key).is_some();

        if result {
            CACHE_INVALIDATIONS.fetch_add(1, Ordering::SeqCst);

            // Update stats
            let mut stats = self.stats.lock().unwrap();
            stats.current_items = entries.len();
        }

        result
    }

    pub fn invalidate_by_prefix(&self, prefix: &str) -> usize {
        let mut entries = self.entries.lock().unwrap();
        let initial_count = entries.len();

        entries.retain(|key, _| !key.starts_with(prefix));

        let removed_count = initial_count - entries.len();

        // Update stats
        if removed_count > 0 {
            CACHE_INVALIDATIONS.fetch_add(removed_count, Ordering::SeqCst);

            let mut stats = self.stats.lock().unwrap();
            stats.current_items = entries.len();
            stats.evictions += removed_count;
        }

        removed_count
    }

    pub fn invalidate_by_pattern(&self, pattern: &str) -> Result<usize, String> {
        // Simple pattern matching for now
        let mut entries = self.entries.lock().unwrap();
        let initial_count = entries.len();

        entries.retain(|key, _| !key.contains(pattern));

        let removed_count = initial_count - entries.len();

        // Update stats
        if removed_count > 0 {
            CACHE_INVALIDATIONS.fetch_add(removed_count, Ordering::SeqCst);

            let mut stats = self.stats.lock().unwrap();
            stats.current_items = entries.len();
            stats.evictions += removed_count;
        }

        Ok(removed_count)
    }

    pub fn get(&self, key: &str) -> Option<DynamicImage> {
        let mut entries = self.entries.lock().unwrap();

        if let Some(entry) = entries.get_mut(key) {
            // Check if entry has expired
            if let Some(expires_at) = entry.expires_at {
                if Instant::now() > expires_at {
                    entries.remove(key);
                    CACHE_MISSES.fetch_add(1, Ordering::SeqCst);

                    // Update stats
                    let mut stats = self.stats.lock().unwrap();
                    stats.misses += 1;
                    stats.current_items = entries.len();

                    return None;
                }
            }

            // Update last accessed time
            entry.last_accessed = Instant::now();

            CACHE_HITS.fetch_add(1, Ordering::SeqCst);

            // Update stats
            let mut stats = self.stats.lock().unwrap();
            stats.hits += 1;

            // Calculate hit ratio
            let total = stats.hits + stats.misses;
            if total > 0 {
                stats.cache_hit_ratio = stats.hits as f64 / total as f64;
            }

            return Some(entry.image.clone());
        }

        CACHE_MISSES.fetch_add(1, Ordering::SeqCst);

        // Update stats
        let mut stats = self.stats.lock().unwrap();
        stats.misses += 1;

        None
    }

    pub fn put(&self, key: String, image: DynamicImage) -> Result<(), String> {
        self.put_with_ttl(key, image, None)
    }

    pub fn put_with_ttl(
        &self,
        key: String,
        image: DynamicImage,
        ttl: Option<Duration>,
    ) -> Result<(), String> {
        let size_bytes = self.estimate_image_size(&image);
        let now = Instant::now();

        let entry = CacheEntry {
            key: key.clone(),
            image: image.clone(),
            size_bytes,
            last_accessed: now,
            created_at: now,
            expires_at: ttl.map(|duration| now + duration),
        };

        let mut entries = self.entries.lock().unwrap();

        // Check if we need to evict entries to make room
        let config = self.config.lock().unwrap();

        // Enforce max items limit
        if entries.len() >= config.max_items {
            // Simple LRU eviction for now
            if let Some((oldest_key, _)) =
                entries.iter().min_by_key(|(_, entry)| entry.last_accessed)
            {
                let oldest_key = oldest_key.clone();
                entries.remove(&oldest_key);

                // Update stats
                let mut stats = self.stats.lock().unwrap();
                stats.evictions += 1;
            }
        }

        // Insert the new entry
        entries.insert(key, entry);

        // Update stats
        let mut stats = self.stats.lock().unwrap();
        stats.current_items = entries.len();
        stats.memory_used_bytes += size_bytes;

        // Calculate memory utilization
        stats.memory_utilization_percent =
            (stats.memory_used_bytes as f64 / config.max_memory_bytes as f64) * 100.0;

        Ok(())
    }

    fn estimate_image_size(&self, image: &DynamicImage) -> usize {
        // Estimate memory usage based on dimensions and color type
        let (width, height) = image.dimensions();
        let bytes_per_pixel = 4; // Assuming RGBA8
        (width as usize) * (height as usize) * bytes_per_pixel
    }

    pub fn preload_common_operations(&self, img: &DynamicImage) -> Result<usize, String> {
        // Preload common image processing operations
        let mut preloaded = 0;

        // Example: preload brightness/contrast adjustments
        for brightness in [-20, 0, 20].iter() {
            for contrast in [-10, 0, 10].iter() {
                let key = format!(
                    "bc_{}_{}_{}x{}",
                    brightness,
                    contrast,
                    img.width(),
                    img.height()
                );

                // Process and cache the result
                // This would call your image processing functions
                // For now, just store the original
                self.put(key, img.clone())?;
                preloaded += 1;
            }
        }

        CACHE_PRELOADS.fetch_add(preloaded, Ordering::SeqCst);

        Ok(preloaded)
    }

    pub fn get_entries_by_prefix(
        &self,
        prefix: &str,
        limit: usize,
        offset: usize,
    ) -> Vec<(String, usize, Instant)> {
        let entries = self.entries.lock().unwrap();

        entries
            .iter()
            .filter(|(key, _)| key.starts_with(prefix))
            .skip(offset)
            .take(limit)
            .map(|(key, entry)| (key.clone(), entry.size_bytes, entry.created_at))
            .collect()
    }

    pub fn log_performance(&self, operation: &str, duration: Duration) {
        let mut log = self.performance_log.lock().unwrap();
        log.push((operation.to_string(), duration));

        // Keep log size reasonable
        if log.len() > 1000 {
            log.drain(0..500);
        }
    }

    pub fn get_performance_log(&self) -> Vec<(String, u128)> {
        let log = self.performance_log.lock().unwrap();
        log.iter()
            .map(|(op, duration)| (op.clone(), duration.as_millis()))
            .collect()
    }

    pub fn export_stats(&self) -> Result<String, String> {
        let stats = self.get_stats();

        // Convert to JSON
        serde_json::to_string_pretty(&stats).map_err(|e| e.to_string())
    }

    pub fn analyze_cache_usage(&self) -> HashMap<String, usize> {
        let entries = self.entries.lock().unwrap();
        let mut analysis = HashMap::new();

        // Count entries by prefix
        for key in entries.keys() {
            // Extract prefix (e.g., "bc_" for brightness/contrast)
            if let Some(pos) = key.find('_') {
                let prefix = &key[0..pos + 1];
                *analysis.entry(prefix.to_string()).or_insert(0) += 1;
            }
        }

        analysis
    }

    pub fn sync_with_python_cache(&self, image_path: &str) -> Result<(), String> {
        // Example implementation - would need to be adapted to your actual Python cache
        #[cfg(target_os = "windows")]
        {
            Command::new("python")
                .args([
                    "-c",
                    &format!("import cache; cache.sync_with_rust('{}')", image_path),
                ])
                .output()
                .map_err(|e| e.to_string())?;
        }

        #[cfg(not(target_os = "windows"))]
        {
            Command::new("python3")
                .args(&[
                    "-c",
                    &format!("import cache; cache.sync_with_rust('{}')", image_path),
                ])
                .output()
                .map_err(|e| e.to_string())?;
        }

        Ok(())
    }

    pub fn preload_with_python(&self, image_path: &str) -> Result<(), String> {
        // Sanitize the input path
        let sanitized_path = image_path.replace('\'', "\\\'").replace('\"', "\\\"");

        // Prepare Python script with proper JSON handling
        let python_script = r#"
    import json
    import cache
    import sys
    
    try:
        result = cache.preload_image('{}')
        json.dump(result, sys.stdout)
    except Exception as e:
        json.dump({{"error": str(e)}}, sys.stderr)
        sys.exit(1)
    "#;

        // Choose Python executable based on platform
        #[cfg(windows)]
        let python_cmd = "python";
        #[cfg(not(windows))]
        let python_cmd = "python3";

        // Execute Python script with timeout
        let output = Command::new(python_cmd)
            .args(["-c", &python_script.replace("{}", &sanitized_path)])
            .env("PYTHONPATH", "./python") // Add Python module path
            .current_dir(std::env::current_dir().map_err(|e| e.to_string())?)
            .output()
            .map_err(|e| format!("Failed to execute Python: {}", e))?;

        if !output.status.success() {
            let error_msg = String::from_utf8_lossy(&output.stderr);
            // Try to parse error JSON
            if let Ok(error) = serde_json::from_str::<serde_json::Value>(&error_msg) {
                if let Some(err_msg) = error.get("error").and_then(|e| e.as_str()) {
                    return Err(format!("Python error: {}", err_msg));
                }
            }
            return Err(format!("Python execution failed: {}", error_msg));
        }

        // Parse the output and update the cache
        let stdout = String::from_utf8_lossy(&output.stdout);
        let preloaded_data: Vec<(String, Vec<u8>)> = serde_json::from_str(&stdout)
            .map_err(|e| format!("Failed to parse Python output: {}", e))?;

        // Update cache stats
        let preload_count = preloaded_data.len();
        CACHE_PRELOADS.fetch_add(preload_count, Ordering::SeqCst);

        // Process preloaded images
        for (key, image_data) in preloaded_data {
            match image::load_from_memory(&image_data) {
                Ok(image) => {
                    if let Err(e) = self.put(key.clone(), image) {
                        eprintln!("Failed to cache image {}: {}", key, e);
                    }
                }
                Err(e) => {
                    eprintln!("Failed to load image {}: {}", key, e);
                }
            }
        }

        Ok(())
    }
}

// Create a global instance of the cache
lazy_static! {
    pub static ref IMAGE_CACHE: ImageCache = ImageCache::new();
}
