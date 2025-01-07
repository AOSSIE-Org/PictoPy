import { invoke } from '@tauri-apps/api/core';

interface CompressionOptions {
  max_width?: number;
  max_height?: number;
  quality?: number;
  maintain_aspect_ratio?: boolean;
}

export async function compressImage(
  imagePath: string, 
  options?: CompressionOptions
): Promise<string> {
  console.log('Starting image compression...', { imagePath, options });
  
  try {
    if (!imagePath) {
      throw new Error('Image path is required');
    }

    // Validate options
    if (options) {
      if (options.quality && (options.quality < 0 || options.quality > 100)) {
        options.quality = 80;
      }
      if (options.max_width && options.max_width <= 0) {
        delete options.max_width;
      }
      if (options.max_height && options.max_height <= 0) {
        delete options.max_height;
      }
    }

    console.log('Invoking Rust compress_image with:', {
      path: imagePath,
      options
    });

    const result = await invoke('compress_image', {
      path: imagePath,
      options
    });

    console.log('Compression result:', result);
    return result as string;
    
  } catch (error) {
    console.error('Detailed compression error:', {
      error,
      imagePath,
      options,
      errorMessage: error instanceof Error ? error.message : 'Unknown error'
    });
    throw error;
  }
} 