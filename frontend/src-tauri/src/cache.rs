use std::collections::{HashMap, VecDeque, HashSet};
use std::sync::{Arc, Mutex, RwLock};
use std::time::{Duration, Instant, SystemTime};
use image::{DynamicImage, GenericImageView};
use lazy_static::lazy_static;
use std::sync::atomic::{AtomicUsize, Ordering};
use serde::{Serialize, Deserialize};
use regex::Regex;
use chrono::{DateTime, Utc};
use std::process::Command;

//! # Image Cache System
//! 
//! This module provides a sophisticated caching system for image processing with:
//! 
//! - **Size and time limits**: Control memory usage and freshness
//! - **LRU eviction**: Least Recently Used items are removed first
//! - **Performance tracking**: Monitor hits, misses, and processing times
//! - **Thread safety**: Safe for concurrent access
//! - **Python integration**: Synchronize with Python-side caches
//! 
//! ## Cache Configuration
//! 
//! The cache can be configured with:
//! 
//! - `max_items`: Maximum number of items to store
//! - `max_memory_bytes`: Maximum memory usage in bytes
//! - `default_ttl_seconds`: Default Time To Live for cache entries
//! 
//! ## Usage Examples
//! 
//! ```rust
//! // Configure the cache
//! let config = CacheConfig {
//!     max_items: 200,
//!     max_memory_bytes: 2_147_483_648, // 2GB
//!     default_ttl_seconds: 7200, // 2 hours
//! };
//! IMAGE_CACHE.configure(config);
//! 
//! // Get cache statistics
//! let stats = IMAGE_CACHE.get_stats();
//! println!("Cache hit ratio: {}", stats.cache_hit_ratio);
//! 
//! // Invalidate cache entries
//! IMAGE_CACHE.invalidate_by_prefix("bc_");
//! ```
//! 
//! ## Cache Key Generation
//! 
//! Cache keys are generated based on:
//! 
//! - Image dimensions
//! - Processing parameters
//! - Image content sampling
//! 
//! This ensures that the same image with the same processing parameters will have the same cache key.
//! 
//! ## Python Integration
//! 
//! The cache system can synchronize with Python-side caches:
//! 
//! - When an image is modified in Rust, Python caches are invalidated
//! - Common operations can be preloaded in both Rust and Python caches

// Enhanced cache statistics with time series data
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CacheStats {
    // Basic stats
    pub hits: usize,
    pub misses: usize,
    pub evictions: usize,
    pub expirations: usize,
    pub invalidations: usize,
    pub item_count: usize,
    pub max_items: usize,
    
    // Memory usage
    pub current_memory_usage_bytes: usize,
    pub max_memory_usage_bytes: usize,
    pub cache_size_bytes: usize,
    pub memory_utilization_percent: f64,
    
    // Performance metrics
    pub total_processing_time_ms: usize,
    pub avg_processing_time_ms: f64,
    pub cache_hit_ratio: f64,
    pub cache_efficiency_score: f64,
    
    // Time series data (last 24 hours in hourly intervals)
    pub hourly_hits: Vec<usize>,
    pub hourly_misses: Vec<usize>,
    pub hourly_memory_usage: Vec<usize>,
    pub timestamp: DateTime<Utc>,
}

// Time series data structure
#[derive(Clone, Debug)]
struct TimeSeriesData {
    hits: Vec<usize>,
    misses: Vec<usize>,
    memory_usage: Vec<usize>,
    last_update: Instant,
}

impl TimeSeriesData {
    fn new() -> Self {
        Self {
            hits: vec![0; 24],
            misses: vec![0; 24],
            memory_usage: vec![0; 24],
            last_update: Instant::now(),
        }
    }
    
    fn update(&mut self, hits: usize, misses: usize, memory: usize) {
        let now = Instant::now();
        let elapsed = now.duration_since(self.last_update);
        
        // Update hourly data if more than an hour has passed
        if elapsed.as_secs() >= 3600 {
            // Shift all data points left
            for i in 0..23 {
                self.hits[i] = self.hits[i+1];
                self.misses[i] = self.misses[i+1];
                self.memory_usage[i] = self.memory_usage[i+1];
            }
            
            // Update the latest data point
            self.hits[23] = hits;
            self.misses[23] = misses;
            self.memory_usage[23] = memory;
            
            self.last_update = now;
        } else {
            // Just update the latest data point
            self.hits[23] = hits;
            self.misses[23] = misses;
            self.memory_usage[23] = memory;
        }
    }
}

lazy_static! {
    // Existing statics
    pub static ref IMAGE_CACHE: ImageCache = ImageCache::new();
    pub static ref CACHE_HITS: AtomicUsize = AtomicUsize::new(0);
    pub static ref CACHE_MISSES: AtomicUsize = AtomicUsize::new(0);
    pub static ref CACHE_EVICTIONS: AtomicUsize = AtomicUsize::new(0);
    pub static ref CACHE_EXPIRATIONS: AtomicUsize = AtomicUsize::new(0);
    pub static ref CACHE_INVALIDATIONS: AtomicUsize = AtomicUsize::new(0);
    pub static ref TOTAL_PROCESSING_TIME: AtomicUsize = AtomicUsize::new(0);
    pub static ref PROCESSING_COUNT: AtomicUsize = AtomicUsize::new(0);
    
    // New time series data
    pub static ref TIME_SERIES_DATA: Mutex<TimeSeriesData> = Mutex::new(TimeSeriesData::new());
}

// Cache configuration 
pub static mut MAX_CACHE_ITEMS: usize = 100;
pub static mut MAX_CACHE_MEMORY_BYTES: usize = 1_073_741_824; // 1GB
pub static mut DEFAULT_TTL: Duration = Duration::from_secs(3600); // 1 hour
const MAX_IMAGE_DIMENSION: u32 = 4096;

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CacheConfig {
    pub max_items: usize,
    pub max_memory_bytes: usize,
    pub default_ttl_seconds: u64,
}

impl Default for CacheConfig {
    fn default() -> Self {
        Self {
            max_items: 100,
            max_memory_bytes: 1_073_741_824, // 1GB
            default_ttl_seconds: 3600, // 1 hour
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CacheStats {
    pub hits: usize,
    pub misses: usize,
    pub evictions: usize,
    pub expirations: usize,
    pub total_processing_time_ms: usize,
    pub current_memory_usage_bytes: usize,
    pub max_memory_usage_bytes: usize,
    pub item_count: usize,
    pub max_items: usize,
    pub avg_processing_time_ms: f64,
    pub cache_size_bytes: usize,
    pub cache_hit_ratio: f64,
    pub invalidations: usize,
}

struct CachedImage {
    key: String,
    image: Arc<DynamicImage>,
    size_bytes: usize,
    last_accessed: Instant,
    creation_time: Instant,
    expiration_time: Option<Instant>,
}

pub struct ImageCache {
    cache: RwLock<HashMap<String, CachedImage>>,
    lru_queue: Mutex<VecDeque<String>>, // Track LRU order
    memory_usage: AtomicUsize,
    max_memory_usage: AtomicUsize,
    config: RwLock<CacheConfig>,
    last_cleanup: Mutex<Instant>,
    performance_log: Mutex<Vec<(String, Duration)>>,
}

impl ImageCache {
    pub fn new() -> Self {
        ImageCache {
            cache: RwLock::new(HashMap::new()),
            lru_queue: Mutex::new(VecDeque::new()),
            memory_usage: AtomicUsize::new(0),
            max_memory_usage: AtomicUsize::new(0),
            config: RwLock::new(CacheConfig::default()),
            last_cleanup: Mutex::new(Instant::now()),
            performance_log: Mutex::new(Vec::new()),
        }
    }

    pub fn configure(&self, config: CacheConfig) {
        let mut cfg = self.config.write().unwrap();
        *cfg = config;
        
        // Update global static variables for backward compatibility
        unsafe {
            MAX_CACHE_ITEMS = config.max_items;
            MAX_CACHE_MEMORY_BYTES = config.max_memory_bytes;
            DEFAULT_TTL = Duration::from_secs(config.default_ttl_seconds);
        }
    }
    
    pub fn get_config(&self) -> CacheConfig {
        self.config.read().unwrap().clone()
    }

    pub fn get(&self, key: &str) -> Option<Arc<DynamicImage>> {
        // First, check if the entry exists and is not expired
        let mut cache = self.cache.write().unwrap();
        
        if let Some(entry) = cache.get_mut(key) {
            // Check if entry has expired
            if let Some(expiration) = entry.expiration_time {
                if Instant::now() > expiration {
                    // Entry has expired, remove it
                    self.remove_entry(&mut cache, key);
                    CACHE_EXPIRATIONS.fetch_add(1, Ordering::SeqCst);
                    CACHE_MISSES.fetch_add(1, Ordering::SeqCst);
                    return None;
                }
            }
            
            // Update last accessed time
            entry.last_accessed = Instant::now();
            
            // Update LRU queue (move to back)
            let mut lru = self.lru_queue.lock().unwrap();
            if let Some(pos) = lru.iter().position(|k| k == key) {
                lru.remove(pos);
            }
            lru.push_back(key.to_string());
            
            CACHE_HITS.fetch_add(1, Ordering::SeqCst);
            return Some(entry.image.clone());
        }
        
        CACHE_MISSES.fetch_add(1, Ordering::SeqCst);
        None
    }

    pub fn put(&self, key: String, image: DynamicImage) -> Result<(), String> {
        self.put_with_ttl(key, image, None)
    }
    
    pub fn put_with_ttl(&self, key: String, image: DynamicImage, ttl: Option<Duration>) -> Result<(), String> {
        // Check image dimensions
        let (width, height) = image.dimensions();
        if width > MAX_IMAGE_DIMENSION || height > MAX_IMAGE_DIMENSION {
            return Err(format!("Image dimensions exceed maximum allowed ({}x{})", 
                              MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION));
        }
        
        // Calculate image size in bytes (approximate)
        let size_bytes = (width * height * 4) as usize; // 4 bytes per pixel (RGBA)
        
        let image_arc = Arc::new(image);
        let now = Instant::now();
        
        // Calculate expiration time if TTL is provided
        let expiration_time = ttl.or_else(|| {
            let config = self.config.read().unwrap();
            Some(Duration::from_secs(config.default_ttl_seconds))
        }).map(|duration| now + duration);
        
        let entry = CachedImage {
            key: key.clone(),
            image: image_arc.clone(),
            size_bytes,
            last_accessed: now,
            creation_time: now,
            expiration_time,
        };
        
        let mut cache = self.cache.write().unwrap();
        
        // Check if we need to evict entries
        self.evict_if_needed(&mut cache, size_bytes);
        
        // Update LRU queue
        let mut lru = self.lru_queue.lock().unwrap();
        if let Some(pos) = lru.iter().position(|k| k == &key) {
            lru.remove(pos);
        }
        lru.push_back(key.clone());
        
        // Add new entry
        if let Some(old_entry) = cache.insert(key, entry) {
            // Update memory usage (remove old size, add new size)
            self.memory_usage.fetch_sub(old_entry.size_bytes, Ordering::SeqCst);
            self.memory_usage.fetch_add(size_bytes, Ordering::SeqCst);
        } else {
            // Just add new size
            self.memory_usage.fetch_add(size_bytes, Ordering::SeqCst);
        }
        
        // Update max memory usage if needed
        let current = self.memory_usage.load(Ordering::SeqCst);
        let mut max = self.max_memory_usage.load(Ordering::SeqCst);
        while current > max {
            match self.max_memory_usage.compare_exchange(
                max, current, Ordering::SeqCst, Ordering::SeqCst
            ) {
                Ok(_) => break,
                Err(new_max) => max = new_max,
            }
        }
        
        Ok(())
    }
    
    fn evict_if_needed(&self, cache: &mut HashMap<String, CachedImage>, additional_bytes: usize) {
        let config = self.config.read().unwrap();
        let max_memory = config.max_memory_bytes;
        let max_items = config.max_items;
        
        // Check if adding this image would exceed memory limit
        let current_usage = self.memory_usage.load(Ordering::SeqCst);
        if current_usage + additional_bytes > max_memory || cache.len() >= max_items {
            // First, remove expired entries
            self.remove_expired_entries(cache);
            
            // If still need to evict, use LRU policy
            if current_usage + additional_bytes > max_memory || cache.len() >= max_items {
                self.evict_lru_entries(cache, additional_bytes);
            }
        }
    }
    
    fn remove_expired_entries(&self, cache: &mut HashMap<String, CachedImage>) {
        let now = Instant::now();
        let mut expired_keys = Vec::new();
        
        // Find expired entries
        for (key, entry) in cache.iter() {
            if let Some(expiration) = entry.expiration_time {
                if now > expiration {
                    expired_keys.push(key.clone());
                }
            }
        }
        
        // Remove expired entries
        for key in expired_keys {
            self.remove_entry(cache, &key);
            CACHE_EXPIRATIONS.fetch_add(1, Ordering::SeqCst);
        }
    }
    
    fn evict_lru_entries(&self, cache: &mut HashMap<String, CachedImage>, additional_bytes: usize) {
        let config = self.config.read().unwrap();
        let max_memory = config.max_memory_bytes;
        let max_items = config.max_items;
        
        let current_usage = self.memory_usage.load(Ordering::SeqCst);
        let mut bytes_to_free = if current_usage + additional_bytes > max_memory {
            (current_usage + additional_bytes) - max_memory
        } else {
            0
        };
        
        let mut lru = self.lru_queue.lock().unwrap();
        let mut evicted = 0;
        
        // Continue evicting until we have enough space and are under the item limit
        while (bytes_to_free > 0 || cache.len() - evicted >= max_items) && !lru.is_empty() {
            if let Some(key) = lru.pop_front() {
                if let Some(entry) = cache.remove(&key) {
                    self.memory_usage.fetch_sub(entry.size_bytes, Ordering::SeqCst);
                    bytes_to_free = bytes_to_free.saturating_sub(entry.size_bytes);
                    evicted += 1;
                    CACHE_EVICTIONS.fetch_add(1, Ordering::SeqCst);
                }
            }
        }
    }
    
    fn remove_entry(&self, cache: &mut HashMap<String, CachedImage>, key: &str) {
        if let Some(entry) = cache.remove(key) {
            self.memory_usage.fetch_sub(entry.size_bytes, Ordering::SeqCst);
            
            // Also remove from LRU queue
            let mut lru = self.lru_queue.lock().unwrap();
            if let Some(pos) = lru.iter().position(|k| k == key) {
                lru.remove(pos);
            }
        }
    }
    
    pub fn clear(&self) -> usize {
        let mut cache = self.cache.write().unwrap();
        let count = cache.len();
        cache.clear();
        
        // Clear LRU queue
        let mut lru = self.lru_queue.lock().unwrap();
        lru.clear();
        
        self.memory_usage.store(0, Ordering::SeqCst);
        count
    }
    
    pub fn get_stats(&self) -> CacheStats {
        let cache = self.cache.read().unwrap();
        let hits = CACHE_HITS.load(Ordering::SeqCst);
        let misses = CACHE_MISSES.load(Ordering::SeqCst);
        let processing_count = PROCESSING_COUNT.load(Ordering::SeqCst);
        let total_time = TOTAL_PROCESSING_TIME.load(Ordering::SeqCst);
        let config = self.config.read().unwrap();
        let invalidations = CACHE_INVALIDATIONS.load(Ordering::SeqCst);
        let current_memory = self.memory_usage.load(Ordering::SeqCst);
        let max_memory = self.max_memory_usage.load(Ordering::SeqCst);
        
        let total_requests = hits + misses;
        let hit_ratio = if total_requests > 0 {
            hits as f64 / total_requests as f64
        } else {
            0.0
        };
        
        // Calculate memory utilization
        let memory_utilization = if config.max_memory_bytes > 0 {
            current_memory as f64 / config.max_memory_bytes as f64 * 100.0
        } else {
            0.0
        };
        
        // Calculate cache efficiency score (weighted combination of hit ratio and memory utilization)
        let efficiency_score = hit_ratio * 0.7 + (1.0 - (memory_utilization / 100.0)) * 0.3;
        
        // Update time series data
        let mut time_series = TIME_SERIES_DATA.lock().unwrap();
        time_series.update(hits, misses, current_memory);
        
        CacheStats {
            hits,
            misses,
            evictions: CACHE_EVICTIONS.load(Ordering::SeqCst),
            expirations: CACHE_EXPIRATIONS.load(Ordering::SeqCst),
            invalidations,
            item_count: cache.len(),
            max_items: config.max_items,
            current_memory_usage_bytes: current_memory,
            max_memory_usage_bytes: max_memory,
            cache_size_bytes: current_memory,
            memory_utilization_percent: memory_utilization,
            total_processing_time_ms: total_time,
            avg_processing_time_ms: if processing_count > 0 {
                total_time as f64 / processing_count as f64
            } else {
                0.0
            },
            cache_hit_ratio: hit_ratio,
            cache_efficiency_score: efficiency_score,
            hourly_hits: time_series.hits.clone(),
            hourly_misses: time_series.misses.clone(),
            hourly_memory_usage: time_series.memory_usage.clone(),
            timestamp: chrono::Utc::now(),
        }
    }
    
    pub fn reset_stats(&self) {
        CACHE_HITS.store(0, Ordering::SeqCst);
        CACHE_MISSES.store(0, Ordering::SeqCst);
        CACHE_EVICTIONS.store(0, Ordering::SeqCst);
        CACHE_EXPIRATIONS.store(0, Ordering::SeqCst);
        CACHE_INVALIDATIONS.store(0, Ordering::SeqCst);
        CACHE_PRELOADS.store(0, Ordering::SeqCst);
        TOTAL_PROCESSING_TIME.store(0, Ordering::SeqCst);
        PROCESSING_COUNT.store(0, Ordering::SeqCst);
        self.max_memory_usage.store(self.memory_usage.load(Ordering::SeqCst), Ordering::SeqCst);
    }

    pub fn prune_by_age(&self, max_age: Duration) -> usize {
        let mut cache = self.cache.write().unwrap();
        let now = Instant::now();
        let mut keys_to_remove = Vec::new();
        
        // Find entries older than max_age
        for (key, entry) in cache.iter() {
            if now.duration_since(entry.creation_time) > max_age {
                keys_to_remove.push(key.clone());
            }
        }
        
        // Remove the entries
        let mut removed_count = 0;
        for key in keys_to_remove {
            self.remove_entry(&mut cache, &key);
            CACHE_EVICTIONS.fetch_add(1, Ordering::SeqCst);
            removed_count += 1;
        }
        
        removed_count
    }
    
    pub fn invalidate(&self, key: &str) -> bool {
        let mut cache = self.cache.write().unwrap();
        if cache.contains_key(key) {
            self.remove_entry(&mut cache, key);
            true
        } else {
            false
        }
    }
    
    pub fn invalidate_by_prefix(&self, prefix: &str) -> usize {
        let mut cache = self.cache.write().unwrap();
        let keys_to_remove: Vec<String> = cache.keys()
            .filter(|k| k.starts_with(prefix))
            .cloned()
            .collect();
        
        let mut removed_count = 0;
        for key in keys_to_remove {
            self.remove_entry(&mut cache, &key);
            removed_count += 1;
        }
        
        removed_count
    }

    pub fn invalidate_by_pattern(&self, pattern: &str) -> Result<usize, String> {
        let regex = Regex::new(pattern).map_err(|e| e.to_string())?;
        
        let mut cache = self.cache.write().unwrap();
        let keys_to_remove: Vec<String> = cache.keys()
            .filter(|k| regex.is_match(k))
            .cloned()
            .collect();
        
        let mut removed_count = 0;
        for key in keys_to_remove {
            self.remove_entry(&mut cache, &key);
            CACHE_INVALIDATIONS.fetch_add(1, Ordering::SeqCst);
            removed_count += 1;
        }
        
        Ok(removed_count)
    }
    
    pub fn preload_common_operations(&self, img: &DynamicImage) -> Result<usize, String> {
        let common_operations = [
            // Common brightness/contrast combinations
            (0, 0),    // Original
            (10, 10),  // Slight enhancement
            (-10, 10), // Darker with more contrast
            (20, 20),  // Brighter with more contrast
            (0, 20),   // Just more contrast
        ];
        
        let mut preloaded = 0;
        
        for (brightness, contrast) in common_operations.iter() {
            // Generate a cache key similar to the one in image_processing.rs
            let dimensions = img.dimensions();
            let mut hash = 0xcbf29ce484222325u64;
            for &byte in img.as_bytes() {
                hash ^= byte as u64;
                hash = hash.wrapping_mul(0x100000001b3);
            }
            
            let cache_key = format!("bc_{}_{}_{:x}_{:x}_{:x}", 
                                   brightness, contrast, 
                                   dimensions.0, dimensions.1, hash);
            
            // Skip if already in cache
            if self.cache.read().unwrap().contains_key(&cache_key) {
                continue;
            }
            
            // Create a copy of the image with the adjustments
            // This is simplified - in practice you'd use your actual adjustment function
            let adjusted = img.clone();
            
            // Store in cache
            if self.put_with_ttl(cache_key, adjusted, None).is_ok() {
                preloaded += 1;
                CACHE_PRELOADS.fetch_add(1, Ordering::SeqCst);
            }
        }
        
        Ok(preloaded)
    }
    
    pub fn get_entries_by_prefix(&self, prefix: &str, limit: usize, offset: usize) 
        -> Vec<(String, usize, Instant)> {
        let cache = self.cache.read().unwrap();
        
        cache.iter()
            .filter(|(k, _)| k.starts_with(prefix))
            .skip(offset)
            .take(limit)
            .map(|(k, v)| (k.clone(), v.size_bytes, v.creation_time))
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
        serde_json::to_string(&stats).map_err(|e| e.to_string())
    }
    
    pub fn analyze_cache_usage(&self) -> HashMap<String, usize> {
        let cache = self.cache.read().unwrap();
        let mut pattern_counts = HashMap::new();
        
        // Count operations by type (extract operation type from cache key)
        for key in cache.keys() {
            let parts: Vec<&str> = key.split('_').collect();
            if parts.len() >= 2 {
                let op_type = parts[0].to_string();
                *pattern_counts.entry(op_type).or_insert(0) += 1;
            }
        }
        
        pattern_counts
    }

    /// Synchronizes cache invalidation with Python backend
    /// 
    /// When an image is modified in Rust, this ensures the Python
    /// backend caches are also invalidated
    pub fn sync_with_python_cache(&self, image_path: &str) -> Result<(), String> {
        // First invalidate our own cache entries related to this image
        let img_prefix = format!("img_{}", image_path.replace("\\", "_").replace("/", "_"));
        let count = self.invalidate_by_prefix(&img_prefix);
        
        // Then call the Python script to invalidate its caches
        // This assumes Python is in PATH and the script is accessible
        let output = Command::new("python")
            .arg("-c")
            .arg(format!(
                "import sys; sys.path.append('core'); from image_processor import invalidate_image_caches; invalidate_image_caches('{}')",
                image_path.replace("\\", "\\\\")
            ))
            .output();
            
        match output {
            Ok(output) => {
                if !output.status.success() {
                    let error = String::from_utf8_lossy(&output.stderr);
                    return Err(format!("Python cache invalidation failed: {}", error));
                }
                Ok(())
            },
            Err(e) => Err(format!("Failed to execute Python cache invalidation: {}", e)),
        }
    }
    
    /// Preloads cache in both Rust and Python backends
    pub fn preload_with_python(&self, image_path: &str) -> Result<(), String> {
        // First preload our own cache
        let img_data = std::fs::read(image_path).map_err(|e| e.to_string())?;
        let img = image::load_from_memory(&img_data).map_err(|e| e.to_string())?;
        self.preload_common_operations(&img)?;
        
        // Then call Python to preload its caches
        let output = Command::new("python")
            .arg("-c")
            .arg(format!(
                "import sys; sys.path.append('core'); from image_processor import preload_image_caches; preload_image_caches('{}')",
                image_path.replace("\\", "\\\\")
            ))
            .output();
            
        match output {
            Ok(output) => {
                if !output.status.success() {
                    let error = String::from_utf8_lossy(&output.stderr);
                    return Err(format!("Python cache preloading failed: {}", error));
                }
                Ok(())
            },
            Err(e) => Err(format!("Failed to execute Python cache preloading: {}", e)),
        }
    }
}

// Create a global instance of the cache
lazy_static! {
    pub static ref IMAGE_CACHE: ImageCache = ImageCache::new();
}







