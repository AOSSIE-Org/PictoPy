import { X, Share2 } from 'lucide-react';
import {  useEffect } from 'react';

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  imagePath: string;
  imageUrl: string;
}

export function ShareModal({ isOpen, onClose, imagePath, imageUrl }: ShareModalProps) {
  // Close modal on ESC key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleNativeShare = async () => {
    try {
      const response = await fetch(imageUrl);
      const blob = await response.blob();
      const filename = imagePath.split(/[\\/]/).pop() || 'image.jpg';
      const fileExtension = filename.split('.').pop()?.toLowerCase() || 'jpg';
      
      const mimeTypes: Record<string, string> = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp',
        'bmp': 'image/bmp',
      };
      const mimeType = mimeTypes[fileExtension] || 'image/jpeg';
      const file = new File([blob], filename, { type: mimeType });

      if (navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) {
        await navigator.share({
          title: 'Share from PictoPy',
          files: [file],
        });
        onClose();
      } else {
        alert('Native share not supported on this device.');
      }
    } catch (error: any) {
      if (error.name !== 'AbortError') {
        console.error('Share failed:', error);
        alert('Failed to share image');
      }
    }
  };

  // Check if Web Share API is available
  const isShareSupported = typeof navigator !== 'undefined' && 'share' in navigator;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-white p-6 shadow-lg dark:bg-gray-900">
        {/* Header */}
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-xl font-semibold">Share Image</h2>
          <button
            onClick={onClose}
            className="rounded-full p-1 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="space-y-3">
          {/* Native Share */}
          {isShareSupported ? (
            <button
              onClick={handleNativeShare}
              className="flex w-full items-center gap-3 rounded-lg border p-3 text-left hover:bg-gray-50 dark:hover:bg-gray-800"
            >
              <Share2 className="h-5 w-5" />
              <span>Share to Apps (WhatsApp, Telegram, etc.)</span>
            </button>
          ) : (
            <div className="rounded-lg border border-yellow-300 bg-yellow-50 p-3 text-sm text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300">
              Native share is not supported on this device.
            </div>
          )}

          {/* Image Preview */}
          <div className="mt-4 rounded-lg border p-2">
            <img
              src={imageUrl}
              alt="Preview"
              className="h-32 w-full rounded object-cover"
            />
            <p className="mt-2 truncate text-xs text-gray-500">
              {imagePath.split(/[\\/]/).pop()}
            </p>
          </div>
        </div>
      </div>
    </>
  );
}