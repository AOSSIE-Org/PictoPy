use image::{DynamicImage, RgbImage};
use std::collections::HashMap;
use std::sync::atomic::Ordering;
use std::time::Instant;

use crate::cache::IMAGE_CACHE;
use crate::image_processing::{
    adjust_brightness_contrast, adjust_exposure, adjust_temperature, adjust_vibrance,
    apply_sharpening,
};

/// Creates a test image with a gradient pattern
fn create_test_image(width: u32, height: u32) -> DynamicImage {
    let mut img = RgbImage::new(width, height);
    for y in 0..height {
        for x in 0..width {
            let r = ((x * 255) / width) as u8;
            let g = ((y * 255) / height) as u8;
            let b = ((x + y) * 255 / (width + height)) as u8;
            img.put_pixel(x, y, image::Rgb([r, g, b]));
        }
    }
    DynamicImage::ImageRgb8(img)
}

/// Runs a comprehensive benchmark of the image processing system
pub fn run_comprehensive_benchmark() {
    // Reset cache for clean testing
    IMAGE_CACHE.clear();

    println!("\n===============================================");
    println!("IMAGE PROCESSING PERFORMANCE BENCHMARK");
    println!("===============================================\n");

    benchmark_performance_metrics();
    benchmark_memory_usage();
    benchmark_operation_comparison();
    benchmark_cache_efficiency();

    println!("\n===============================================");
    println!("BENCHMARK COMPLETE");
    println!("===============================================\n");
}

/// Benchmarks performance metrics across different image sizes
fn benchmark_performance_metrics() {
    // Test with multiple image sizes
    let sizes = [100, 500, 1000, 2000];

    println!("\n## PERFORMANCE METRICS ##");
    println!("Size | First Run (ms) | Cached Run (ms) | Improvement");
    println!("-----|---------------|-----------------|------------");

    for size in sizes {
        let img = create_test_image(size, size);

        // First run (cache miss)
        let start = Instant::now();
        let _ = adjust_brightness_contrast(&img, 20, 30);
        let first_time = start.elapsed();

        // Second run (cache hit)
        let start = Instant::now();
        let _ = adjust_brightness_contrast(&img, 20, 30);
        let second_time = start.elapsed();

        // Calculate improvement factor
        let improvement = first_time.as_millis() as f64 / second_time.as_millis().max(1) as f64;

        println!(
            "{}x{} | {:8.2} | {:14.2} | {:8.1}x",
            size,
            size,
            first_time.as_millis(),
            second_time.as_millis(),
            improvement
        );
    }
}

/// Benchmarks memory usage with multiple images
fn benchmark_memory_usage() {
    // Configure a small cache for testing
    IMAGE_CACHE.clear();

    println!("\n## MEMORY USAGE ANALYSIS ##");
    println!("Operation | Before (MB) | After (MB) | Images | Memory Efficiency");
    println!("----------|-------------|------------|--------|------------------");

    // Start with empty cache
    let initial_memory = IMAGE_CACHE.get_memory_usage();

    // Process 20 different images
    let mut all_images = Vec::new();
    for i in 0..20 {
        let size = 200 + (i * 20); // Varying sizes
        let img = create_test_image(size, size);
        all_images.push(img);

        // Apply different processing to each image - fix usize casting
        let idx = i as usize;
        let _ = adjust_brightness_contrast(&all_images[idx], 10, 20);
        let _ = adjust_vibrance(&all_images[idx], 15);
    }

    // Measure memory after processing
    let final_memory = IMAGE_CACHE.get_memory_usage();
    let memory_per_image = if !all_images.is_empty() {
        (final_memory - initial_memory) as f64 / all_images.len() as f64
    } else {
        0.0
    };

    println!(
        "Batch    | {:11.2} | {:10.2} | {:6} | {:8.2} MB/image",
        initial_memory as f64 / (1024.0 * 1024.0),
        final_memory as f64 / (1024.0 * 1024.0),
        all_images.len(),
        memory_per_image / (1024.0 * 1024.0)
    );
}

/// Compares performance of different image operations
fn benchmark_operation_comparison() {
    // Create a single test image
    let img = create_test_image(1000, 1000);
    IMAGE_CACHE.clear();

    println!("\n## OPERATION COMPARISON ##");
    println!("Operation    | First Run (ms) | Cached Run (ms) | Improvement");
    println!("-------------|---------------|-----------------|------------");

    // Test each operation - use Box<dyn Fn> to handle different closure types
    let operations: Vec<(&str, Box<dyn Fn(&DynamicImage) -> DynamicImage>)> = vec![
        (
            "Brightness",
            Box::new(|img: &DynamicImage| adjust_brightness_contrast(img, 20, 0)),
        ),
        (
            "Contrast",
            Box::new(|img: &DynamicImage| adjust_brightness_contrast(img, 0, 20)),
        ),
        (
            "Vibrance",
            Box::new(|img: &DynamicImage| adjust_vibrance(img, 20)),
        ),
        (
            "Exposure",
            Box::new(|img: &DynamicImage| adjust_exposure(img, 20)),
        ),
        (
            "Temperature",
            Box::new(|img: &DynamicImage| adjust_temperature(img, 20)),
        ),
        (
            "Sharpening",
            Box::new(|img: &DynamicImage| apply_sharpening(img, 20)),
        ),
    ];

    for (name, op) in operations {
        // First run (cache miss)
        let start = Instant::now();
        let _ = op(&img);
        let first_time = start.elapsed();

        // Second run (cache hit)
        let start = Instant::now();
        let _ = op(&img);
        let second_time = start.elapsed();

        // Calculate improvement
        let improvement = first_time.as_millis() as f64 / second_time.as_millis().max(1) as f64;

        println!(
            "{:12} | {:13.2} | {:15.2} | {:10.1}x",
            name,
            first_time.as_millis(),
            second_time.as_millis(),
            improvement
        );
    }
}

/// Tests cache efficiency under load
fn benchmark_cache_efficiency() {
    IMAGE_CACHE.clear();

    println!("\n## CACHE EFFICIENCY ##");
    println!("Operations | Hit Ratio | Evictions | Memory Used (MB)");
    println!("-----------|-----------|-----------|----------------");

    let img = create_test_image(800, 800);

    // Run multiple operations with different parameters
    let iterations = [10, 50, 100, 200];

    for &iter in &iterations {
        // Run operations
        for i in 0..iter {
            let brightness = (i % 20) - 10;
            let contrast = (i % 30) - 15;
            let _ = adjust_brightness_contrast(&img, brightness, contrast);
        }

        // Get stats
        let hits = IMAGE_CACHE.get_hits();
        let misses = IMAGE_CACHE.get_misses();
        let hit_ratio = if hits + misses > 0 {
            hits as f64 / (hits + misses) as f64 * 100.0
        } else {
            0.0
        };
        // Use the atomic counter directly since get_evictions() doesn't exist
        let evictions = crate::cache::CACHE_EVICTIONS.load(Ordering::SeqCst);
        let memory = IMAGE_CACHE.get_memory_usage() as f64 / (1024.0 * 1024.0);

        println!(
            "{:11} | {:8.1}% | {:9} | {:16.2}",
            iter, hit_ratio, evictions, memory
        );
    }
}

// Helper extension methods for the IMAGE_CACHE
trait CacheStats {
    fn get_hits(&self) -> usize;
    fn get_misses(&self) -> usize;
    fn get_evictions(&self) -> usize;
    fn get_memory_usage(&self) -> usize;
}

impl CacheStats for crate::cache::ImageCache {
    fn get_hits(&self) -> usize {
        // Access the atomic counter for hits
        crate::cache::CACHE_HITS.load(Ordering::SeqCst)
    }

    fn get_misses(&self) -> usize {
        // Access the atomic counter for misses
        crate::cache::CACHE_MISSES.load(Ordering::SeqCst)
    }

    fn get_evictions(&self) -> usize {
        // Access the atomic counter for evictions
        crate::cache::CACHE_EVICTIONS.load(Ordering::SeqCst)
    }

    fn get_memory_usage(&self) -> usize {
        // Estimate memory usage based on cache size
        let stats = self.get_stats();
        stats.memory_used_bytes
    }
}

// Add a Tauri command to run the benchmark from the UI
#[tauri::command]
pub fn run_benchmark() -> HashMap<String, serde_json::Value> {
    // Reset metrics for a clean test
    IMAGE_CACHE.clear();

    // Create results container
    let mut results = HashMap::new();

    // Image size benchmarks
    let sizes = [500, 1000, 2000];
    let mut size_metrics = Vec::new();

    for size in sizes {
        let img = create_test_image(size, size);

        // First run (cache miss)
        let start = Instant::now();
        let _ = adjust_brightness_contrast(&img, 20, 30);
        let first_time = start.elapsed().as_millis() as f64;

        // Second run (cache hit)
        let start = Instant::now();
        let _ = adjust_brightness_contrast(&img, 20, 30);
        let second_time = start.elapsed().as_millis() as f64;

        // Calculate improvement factor
        let improvement = if second_time > 0.0 {
            first_time / second_time
        } else {
            0.0
        };

        size_metrics.push(serde_json::json!({
            "size": size,
            "first_run_ms": first_time,
            "cached_run_ms": second_time,
            "improvement_factor": improvement
        }));
    }
    results.insert(
        "size_comparison".to_string(),
        serde_json::json!(size_metrics),
    );

    // Memory usage
    let stats = IMAGE_CACHE.get_stats();
    results.insert(
        "memory_stats".to_string(),
        serde_json::json!({
            "items_count": stats.current_items,
            "memory_used_mb": stats.memory_used_bytes as f64 / (1024.0 * 1024.0),
            "memory_utilization": stats.memory_utilization_percent,
            "evictions": IMAGE_CACHE.get_evictions()
        }),
    );

    // Cache performance
    results.insert("cache_stats".to_string(), serde_json::json!({
        "hits": IMAGE_CACHE.get_hits(),
        "misses": IMAGE_CACHE.get_misses(),
        "hit_ratio": if IMAGE_CACHE.get_hits() + IMAGE_CACHE.get_misses() > 0 {
            IMAGE_CACHE.get_hits() as f64 / (IMAGE_CACHE.get_hits() + IMAGE_CACHE.get_misses()) as f64 * 100.0
        } else {
            0.0
        },
        "memory_efficiency": stats.memory_utilization_percent
    }));

    // Run the console output version too
    run_comprehensive_benchmark();

    results
}
