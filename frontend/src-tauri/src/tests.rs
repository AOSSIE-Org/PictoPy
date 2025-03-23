#[cfg(test)]
mod tests {
    use super::*;
    use crate::cache::{ImageCache, TimeSeriesData, VisualizationData};
    use crate::image_processing::adjust_brightness_contrast;
    use image::{DynamicImage, GenericImageView, RgbImage};
    use std::time::{Duration, Instant};

    // Test SIMD operations
    #[test]
    fn test_brightness_contrast_adjustment() {
        // Create a simple test image
        let width = 100;
        let height = 100;
        let mut img = RgbImage::new(width, height);
        
        // Fill with a gradient
        for y in 0..height {
            for x in 0..width {
                let pixel = image::Rgb([x as u8, y as u8, 128]);
                img.put_pixel(x, y, pixel);
            }
        }
        
        let dynamic_img = DynamicImage::ImageRgb8(img);
        
        // Test with different brightness/contrast values
        let start = Instant::now();
        let result = adjust_brightness_contrast(&dynamic_img, 10, 20);
        let duration = start.elapsed();
        
        // Verify dimensions are preserved
        assert_eq!(result.dimensions(), dynamic_img.dimensions());
        
        // Print performance info
        println!("Brightness/contrast adjustment took: {:?}", duration);
        
        // Test with different values
        let result2 = adjust_brightness_contrast(&dynamic_img, -10, -20);
        assert_eq!(result2.dimensions(), dynamic_img.dimensions());
    }
    
    // Test TimeSeriesData implementation
    #[test]
    fn test_time_series_data() {
        // Create a new time series with custom config
        let mut ts = TimeSeriesData::with_config(5, 10); // 5-minute intervals, 10 data points
        
        // Update with some test data
        ts.update(100, 20, 1024 * 1024); // 1MB
        
        // Get visualization data
        let viz_data = ts.get_visualization_data();
        
        // Verify data
        assert_eq!(viz_data.hits.len(), 10);
        assert_eq!(viz_data.misses.len(), 10);
        assert_eq!(viz_data.memory_usage_mb.len(), 10);
        assert_eq!(viz_data.labels.len(), 10);
        
        // Test last data point
        let last_idx = viz_data.hits.len() - 1;
        assert_eq!(viz_data.hits[last_idx], 100);
        assert_eq!(viz_data.misses[last_idx], 20);
        assert_eq!(viz_data.memory_usage_mb[last_idx], 1); // 1MB
        
        // Test resize
        ts.resize(10, 5); // 10-minute intervals, 5 data points
        assert_eq!(ts.hits.len(), 5);
        assert_eq!(ts.interval_minutes, 10);
    }
}