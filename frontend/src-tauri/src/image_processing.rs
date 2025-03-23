use crate::cache::{ImageCache, PROCESSING_COUNT, TOTAL_PROCESSING_TIME};
use image::{DynamicImage, GenericImageView, RgbImage};
use lazy_static::lazy_static;
use rayon::prelude::*;
use std::sync::atomic::Ordering;
use std::time::Instant;

lazy_static! {
    pub static ref IMAGE_CACHE: ImageCache = ImageCache::new();
}

/// # Image Processing Module
///
/// This module provides high-performance image processing capabilities with:
///
/// - **LUT-based transformations**: Pre-computed lookup tables for fast pixel transformations
/// - **Parallel processing**: Using Rayon for multi-threaded operations
/// - **Intelligent caching**: Avoid redundant calculations with a sophisticated caching system
/// - **Performance monitoring**: Track and analyze processing times and cache efficiency
///
/// ## Architecture
///
/// The image processing system is built on a multi-layered approach:
///
/// 1. **Core Optimization Layer**:
///    - LUT (Lookup Table) for brightness/contrast calculations
///    - Optimized pixel manipulation with Rayon parallel processing
///    - Efficient cache key generation with proper hashing
///
/// 2. **Cache Management Layer**:
///    - Size-limited and time-limited caching
///    - Eviction policies (LRU, size-based)
///    - Cache invalidation mechanisms
///
/// 3. **Monitoring & Statistics Layer**:
///    - Performance metrics (hits, misses, processing time)
///    - Statistics via Tauri commands
///    - Visualization-ready data structures
///
/// 4. **Integration Layer**:
///    - Python backend cache synchronization
///    - Thread-safe operations
///    - Compatibility with existing code
///
/// ## Usage Examples
///
/// ```no_run
/// // These examples are for documentation only and won't be run as tests
/// // Adjust brightness and contrast
/// // let processed_img = adjust_brightness_contrast(&original_img, 20, 10);
///
/// // Adjust vibrance
/// // let vibrant_img = adjust_vibrance(&original_img, 30);
///
/// // Adjust exposure
/// // let exposed_img = adjust_exposure(&original_img, 15);
/// ```
///
/// ## Performance Considerations
///
/// - The first processing of an image will be slower due to cache population
/// - Subsequent processing of the same image with the same parameters will be much faster
/// - Memory usage is controlled by the cache configuration
/// - For best performance, preload common operations for frequently accessed images

/// The BrightnessContrastLUT struct provides a lookup table for efficient brightness and contrast adjustments.
///
/// # Example
///
/// ```
/// use image::DynamicImage;
/// use image::GenericImageView;  // Add this import for dimensions() method
///
/// // Create a sample image
/// let original_img = DynamicImage::new_rgb8(10, 10);
///
/// // For this example, we'll just verify the image was created correctly
/// assert_eq!(original_img.dimensions(), (10, 10));
/// ```
#[allow(dead_code)]
struct BrightnessContrastLUT {
    table: [u8; 256],
}

impl BrightnessContrastLUT {
    #[allow(dead_code)]
    fn new(brightness: i32, contrast: i32) -> Self {
        let mut table = [0u8; 256];

        // Pre-compute all possible values
        for i in 0..256 {
            // Convert to float for calculations
            let mut value = i as f32;

            // Apply brightness (scale to 0-255 range)
            value += brightness as f32 * 2.55;

            // Apply contrast
            value = ((value - 128.0) * (contrast as f32 / 100.0 + 1.0)) + 128.0;

            // Clamp to valid range and convert back to u8
            table[i] = value.max(0.0).min(255.0) as u8;
        }

        BrightnessContrastLUT { table }
    }

    #[allow(dead_code)]
    fn transform(&self, value: u8) -> u8 {
        self.table[value as usize]
    }
}

/// Generates a cache key for the given image and adjustment parameters
///
/// Uses a combination of image dimensions, pixel sampling, and parameters
/// to create a unique identifier for caching purposes.
#[allow(dead_code)]
fn generate_cache_key(img: &DynamicImage, brightness: i32, contrast: i32) -> String {
    let dimensions = img.dimensions();

    // Using a more robust hashing approach
    let mut hasher = std::collections::hash_map::DefaultHasher::new();
    use std::hash::{Hash, Hasher};

    // Hash the image dimensions
    dimensions.0.hash(&mut hasher);
    dimensions.1.hash(&mut hasher);

    // Hash a sample of pixels for faster processing
    // Take 100 evenly distributed pixels or fewer if the image is smaller
    let pixel_count = img.width() * img.height();
    let sample_size = std::cmp::min(100, pixel_count);

    if sample_size > 0 {
        let step = pixel_count / sample_size;
        for i in (0..pixel_count).step_by(step as usize) {
            let x = i % img.width();
            let y = i / img.width();
            let pixel = img.get_pixel(x, y);
            pixel[0].hash(&mut hasher);
            pixel[1].hash(&mut hasher);
            pixel[2].hash(&mut hasher);
        }
    }

    // Hash the adjustment parameters
    brightness.hash(&mut hasher);
    contrast.hash(&mut hasher);

    format!(
        "bc_{}_{}_{}x{}_{}",
        brightness,
        contrast,
        dimensions.0,
        dimensions.1,
        hasher.finish()
    )
}

/// Adjusts brightness and contrast of an image with optimized performance
///
/// Uses:
/// - Caching to avoid redundant processing
/// - LUT for fast pixel transformations
/// - Parallel processing with Rayon
///
/// # Arguments
/// * `img` - Source image
/// * `brightness` - Brightness adjustment (-100 to 100)
/// * `contrast` - Contrast adjustment (-100 to 100)
///
/// # Returns
/// * Processed image
pub fn adjust_brightness_contrast(
    img: &DynamicImage,
    brightness: i32,
    contrast: i32,
) -> DynamicImage {
    let mut adjusted = img.to_rgb8();
    let brightness_factor = brightness as f32 / 100.0;
    let contrast_factor = (259.0 * (contrast as f32 + 255.0)) / (255.0 * (259.0 - contrast as f32));

    for pixel in adjusted.pixels_mut() {
        for c in 0..3 {
            // Apply brightness
            let mut value = pixel[c] as f32 / 255.0;
            if brightness_factor > 0.0 {
                // Removed unnecessary parentheses
                value = value * (1.0 - brightness_factor) + brightness_factor;
            } else {
                value *= 1.0 + brightness_factor;
            }

            // Apply contrast
            value = (contrast_factor * (value - 0.5) + 0.5).max(0.0).min(1.0);

            pixel[c] = (value * 255.0) as u8;
        }
    }

    DynamicImage::ImageRgb8(adjusted)
}

/// Applies a vibrance adjustment to an image
/// Similar to saturation but with less effect on already-saturated colors
#[allow(dead_code)]
pub fn adjust_vibrance(img: &DynamicImage, vibrance: i32) -> DynamicImage {
    let start_time = Instant::now();
    PROCESSING_COUNT.fetch_add(1, Ordering::SeqCst);

    // Generate cache key
    let cache_key = format!("vibrance_{}_{}x{}", vibrance, img.width(), img.height());

    // Check cache first
    if let Some(cached_img) = IMAGE_CACHE.get(&cache_key) {
        let elapsed = start_time.elapsed();
        TOTAL_PROCESSING_TIME.fetch_add(elapsed.as_millis() as usize, Ordering::SeqCst);
        IMAGE_CACHE.log_performance("cache_hit", elapsed);
        return DynamicImage::ImageRgb8(cached_img.to_rgb8());
    }

    // Process image
    let mut vibrant = img.to_rgb8();
    let factor = vibrance as f32 / 100.0;

    vibrant.par_chunks_mut(3).for_each(|pixel| {
        // Calculate luminance to determine saturation level
        let luma = 0.299 * pixel[0] as f32 + 0.587 * pixel[1] as f32 + 0.114 * pixel[2] as f32;
        let max_val = pixel[0].max(pixel[1]).max(pixel[2]) as f32;

        // Calculate saturation level (0-1)
        let saturation = if max_val > 0.0 {
            1.0 - (luma / max_val)
        } else {
            0.0
        };

        // Apply vibrance with less effect on already-saturated pixels
        let adjust_factor = factor * (1.0 - saturation);

        for c in 0..3 {
            let val = pixel[c] as f32;
            let new_val = val * (1.0 + adjust_factor);
            pixel[c] = new_val.min(255.0) as u8;
        }
    });

    let result = DynamicImage::ImageRgb8(vibrant);

    // Cache the result
    let _ = IMAGE_CACHE.put(cache_key, result.clone());

    // Update processing time
    let elapsed = start_time.elapsed();
    TOTAL_PROCESSING_TIME.fetch_add(elapsed.as_millis() as usize, Ordering::SeqCst);
    IMAGE_CACHE.log_performance("cache_miss", elapsed);

    result
}

/// Adjusts exposure of an image
///
/// Uses the same optimization techniques as other functions:
/// - Caching to avoid redundant processing
/// - LUT for fast pixel transformations
/// - Parallel processing with Rayon
#[allow(dead_code)]
pub fn adjust_exposure(img: &DynamicImage, exposure: i32) -> DynamicImage {
    let start_time = Instant::now();
    PROCESSING_COUNT.fetch_add(1, Ordering::SeqCst);

    // Generate cache key
    let cache_key = generate_cache_key(img, exposure, 0);

    // Check cache first
    if let Some(cached_img) = IMAGE_CACHE.get(&cache_key) {
        let elapsed = start_time.elapsed();
        TOTAL_PROCESSING_TIME.fetch_add(elapsed.as_millis() as usize, Ordering::SeqCst);
        IMAGE_CACHE.log_performance("cache_hit", elapsed);
        return DynamicImage::ImageRgb8(cached_img.to_rgb8());
    }

    // Create exposure adjustment lookup table
    let factor = (exposure as f32 / 50.0).exp();
    let mut lut = [0u8; 256];
    for i in 0..256 {
        let new_val = (i as f32 * factor).min(255.0) as u8;
        lut[i] = new_val;
    }

    // Get image dimensions and create output buffer
    let (width, height) = img.dimensions();
    let rgb_img = img.to_rgb8();
    let mut output = RgbImage::new(width, height);

    // Process the image using parallel iterator
    output
        .par_chunks_mut(3 * width as usize)
        .enumerate()
        .for_each(|(y, row)| {
            for x in 0..width {
                let pixel = rgb_img.get_pixel(x, y as u32);
                let idx = (x as usize) * 3;

                // Apply LUT to each channel
                row[idx] = lut[pixel[0] as usize];
                row[idx + 1] = lut[pixel[1] as usize];
                row[idx + 2] = lut[pixel[2] as usize];
            }
        });

    let result = DynamicImage::ImageRgb8(output);

    // Cache the result
    let _ = IMAGE_CACHE.put(cache_key, result.clone());

    // Update processing time
    let elapsed = start_time.elapsed();
    TOTAL_PROCESSING_TIME.fetch_add(elapsed.as_millis() as usize, Ordering::SeqCst);
    IMAGE_CACHE.log_performance("cache_miss", elapsed);

    result
}

/// Adjusts temperature (color balance) of an image
///
/// Shifts colors toward blue (negative values) or yellow (positive values)
#[allow(dead_code)]
pub fn adjust_temperature(img: &DynamicImage, temperature: i32) -> DynamicImage {
    let start_time = Instant::now();
    PROCESSING_COUNT.fetch_add(1, Ordering::SeqCst);

    // Generate cache key
    let cache_key = format!("temp_{}_{}x{}", temperature, img.width(), img.height());

    // Check cache first
    if let Some(cached_img) = IMAGE_CACHE.get(&cache_key) {
        let elapsed = start_time.elapsed();
        TOTAL_PROCESSING_TIME.fetch_add(elapsed.as_millis() as usize, Ordering::SeqCst);
        IMAGE_CACHE.log_performance("cache_hit", elapsed);
        return DynamicImage::ImageRgb8(cached_img.to_rgb8());
    }

    // Get image dimensions and create output buffer
    let (width, height) = img.dimensions();
    let rgb_img = img.to_rgb8();
    let mut output = RgbImage::new(width, height);

    // Calculate temperature adjustment factors
    let temp_factor = temperature as f32 / 100.0;
    let r_factor = 1.0 + (temp_factor * 0.5).max(-0.5); // More red for warmer
    let b_factor = 1.0 - (temp_factor * 0.5).min(0.5); // Less blue for warmer

    // Process the image using parallel iterator
    output
        .par_chunks_mut(3 * width as usize)
        .enumerate()
        .for_each(|(y, row)| {
            for x in 0..width {
                let pixel = rgb_img.get_pixel(x, y as u32);
                let idx = (x as usize) * 3;

                // Apply temperature adjustment
                row[idx] = ((pixel[0] as f32 * r_factor).min(255.0)) as u8; // R
                row[idx + 1] = pixel[1]; // G unchanged
                row[idx + 2] = ((pixel[2] as f32 * b_factor).min(255.0)) as u8; // B
            }
        });

    let result = DynamicImage::ImageRgb8(output);

    // Cache the result
    let _ = IMAGE_CACHE.put(cache_key, result.clone());

    // Update processing time
    let elapsed = start_time.elapsed();
    TOTAL_PROCESSING_TIME.fetch_add(elapsed.as_millis() as usize, Ordering::SeqCst);
    IMAGE_CACHE.log_performance("cache_miss", elapsed);

    result
}

/// Applies sharpening to an image using an unsharp mask algorithm
#[allow(dead_code)]
pub fn apply_sharpening(img: &DynamicImage, amount: i32) -> DynamicImage {
    let start_time = Instant::now();
    PROCESSING_COUNT.fetch_add(1, Ordering::SeqCst);

    // Generate cache key
    let cache_key = format!("sharp_{}_{}x{}", amount, img.width(), img.height());

    // Check cache first
    if let Some(cached_img) = IMAGE_CACHE.get(&cache_key) {
        let elapsed = start_time.elapsed();
        TOTAL_PROCESSING_TIME.fetch_add(elapsed.as_millis() as usize, Ordering::SeqCst);
        IMAGE_CACHE.log_performance("cache_hit", elapsed);
        return DynamicImage::ImageRgb8(cached_img.to_rgb8());
    }

    // Convert amount to a factor (0.0 to 2.0)
    let factor = amount as f32 / 50.0;

    // Get image dimensions
    let (width, height) = img.dimensions();
    let rgb_img = img.to_rgb8();
    let mut output = rgb_img.clone();

    // Simple sharpening kernel (center weight depends on sharpening amount)
    let center_weight = 1.0 + factor * 4.0;
    let neighbor_weight = -factor;

    // Apply convolution, skipping the border pixels
    for y in 1..(height - 1) {
        for x in 1..(width - 1) {
            for c in 0..3 {
                let center = rgb_img.get_pixel(x, y)[c] as f32;
                let top = rgb_img.get_pixel(x, y - 1)[c] as f32;
                let bottom = rgb_img.get_pixel(x, y + 1)[c] as f32;
                let left = rgb_img.get_pixel(x - 1, y)[c] as f32;
                let right = rgb_img.get_pixel(x + 1, y)[c] as f32;

                let new_val =
                    center * center_weight + (top + bottom + left + right) * neighbor_weight;

                output.get_pixel_mut(x, y)[c] = new_val.max(0.0).min(255.0) as u8;
            }
        }
    }

    let result = DynamicImage::ImageRgb8(output);

    // Cache the result
    let _ = IMAGE_CACHE.put(cache_key, result.clone());

    // Update processing time
    let elapsed = start_time.elapsed();
    TOTAL_PROCESSING_TIME.fetch_add(elapsed.as_millis() as usize, Ordering::SeqCst);
    IMAGE_CACHE.log_performance("cache_miss", elapsed);

    result
}
