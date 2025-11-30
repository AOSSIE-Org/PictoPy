import { useState } from 'react';
import { invoke } from '@tauri-apps/api/core';
import { save } from '@tauri-apps/plugin-dialog';
import { Image } from '@/types/Media';
import { toast } from 'sonner';

export const useImageShare = () => {
  const [isSharing, setIsSharing] = useState(false);

  const exportAsZip = async (images: Image | Image[]) => {
    try {
      setIsSharing(true);
      const imageArray = Array.isArray(images) ? images : [images];
      const imagePaths = imageArray.map((img) => img.path);

      const defaultName =
        imageArray.length === 1
          ? `${imageArray[0].name?.replace(/\.[^/.]+$/, '') || 'image'}.zip`
          : `PictoPy_Export_${Date.now()}.zip`;

      const zipPath = await save({
        defaultPath: defaultName,
        filters: [
          {
            name: 'ZIP Archive',
            extensions: ['zip'],
          },
        ],
      });

      if (!zipPath) {
        setIsSharing(false);
        toast.info('Export cancelled');
        return;
      }

      await invoke('create_zip_from_images', {
        imagePaths,
        outputPath: zipPath,
      });

      toast.success(`Successfully exported image to ZIP`);
    } catch (error) {
      console.error('Failed to export as ZIP:', error);
      toast.error(`Failed to export ZIP file: ${error}`);
    } finally {
      setIsSharing(false);
    }
  };

  const copyPathToClipboard = async (image: Image) => {
    try {
      await navigator.clipboard.writeText(image.path);
      toast.success('Path copied to clipboard');
    } catch (error) {
      console.error('Failed to copy path:', error);
      toast.error(`Failed to copy path: ${error}`);
    }
  };

  const openFileLocation = async (image: Image) => {
    try {
      await invoke('open_file_location', { filePath: image.path });
      toast.success('Opening file location');
    } catch (error) {
      console.error('Failed to open file location:', error);
      toast.error(`Failed to open file location: ${error}`);
    }
  };

  return {
    exportAsZip,
    copyPathToClipboard,
    openFileLocation,
    isSharing,
  };
};
