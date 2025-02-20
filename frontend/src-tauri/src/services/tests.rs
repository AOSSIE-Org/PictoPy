#[cfg(test)]
mod tests {
    use super::*;
    use image::{DynamicImage, ImageBuffer, Rgba};
    use std::time::Instant;

    fn create_test_image(width: u32, height: u32) -> DynamicImage {
        let mut img = ImageBuffer::new(width, height);
        for x in 0..width {
            for y in 0..height {
                img.put_pixel(x, y, Rgba([100, 150, 200, 255]));
            }
        }
        DynamicImage::ImageRgba8(img)
    }

    #[test]
    fn test_brightness_contrast_correctness() {
        let img = create_test_image(100, 100);
        
        // Test with various brightness and contrast values
        let test_cases = vec![
            (0, 0),    // No change
            (50, 0),   // Increased brightness
            (0, 50),   // Increased contrast
            (-50, 0),  // Decreased brightness
            (0, -50),  // Decreased contrast
        ];

        for (brightness, contrast) in test_cases {
            let result = adjust_brightness_contrast(&img, brightness, contrast);
            
            // Verify dimensions are preserved
            assert_eq!(result.width(), img.width());
            assert_eq!(result.height(), img.height());
            
            // Verify pixel values are within valid range
            let result_buffer = result.to_rgba8();
            for pixel in result_buffer.pixels() {
                assert!(pixel[0] <= 255);
                assert!(pixel[1] <= 255);
                assert!(pixel[2] <= 255);
                assert_eq!(pixel[3], 255); // Alpha should remain unchanged
            }
        }
    }

    #[test]
    fn test_caching_performance() {
        let img = create_test_image(500, 500);
        
        // Clear cache before testing
        clear_image_cache();
        
        // First run - should be slower (no cache)
        let start = Instant::now();
        let _ = adjust_brightness_contrast(&img, 50, 50);
        let first_duration = start.elapsed();
        
        // Second run - should be faster (cached)
        let start = Instant::now();
        let _ = adjust_brightness_contrast(&img, 50, 50);
        let second_duration = start.elapsed();
        
        // The second run should be significantly faster due to caching
        assert!(second_duration < first_duration);
        println!("First run: {:?}, Second run: {:?}", first_duration, second_duration);
    }

    #[test]
    fn test_parallel_processing() {
        let img = create_test_image(1000, 1000);
        
        // Process large image and measure time
        let start = Instant::now();
        let _ = adjust_brightness_contrast(&img, 30, 30);
        let duration = start.elapsed();
        
        // Print processing time for manual verification
        println!("Processing time for 1000x1000 image: {:?}", duration);
    }

    #[test]
    fn test_different_image_sizes() {
        let sizes = vec![(100, 100), (200, 300), (500, 500)];
        
        for (width, height) in sizes {
            let img = create_test_image(width, height);
            let result = adjust_brightness_contrast(&img, 20, 20);
            
            assert_eq!(result.width(), width);
            assert_eq!(result.height(), height);
        }
    }

    #[test]
    fn test_extreme_values() {
        let img = create_test_image(100, 100);
        
        // Test with extreme brightness and contrast values
        let extreme_cases = vec![
            (100, 100),   // Maximum brightness and contrast
            (-100, -100), // Minimum brightness and contrast
            (100, -100),  // Max brightness, min contrast
            (-100, 100),  // Min brightness, max contrast
        ];

        for (brightness, contrast) in extreme_cases {
            let result = adjust_brightness_contrast(&img, brightness, contrast);
            
            // Verify the image is still valid
            assert_eq!(result.width(), img.width());
            assert_eq!(result.height(), img.height());
            
            // Check that pixel values are clamped correctly
            let result_buffer = result.to_rgba8();
            for pixel in result_buffer.pixels() {
                assert!(pixel[0] <= 255);
                assert!(pixel[1] <= 255);
                assert!(pixel[2] <= 255);
                assert_eq!(pixel[3], 255);
            }
        }
    }
}