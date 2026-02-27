import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { open } from '@tauri-apps/plugin-shell';
import {
  X,
  ImageIcon as ImageLucide,
  Calendar,
  MapPin,
  Tag,
  Info,
  SquareArrowOutUpRight,
} from 'lucide-react';
import { Image } from '@/types/Media';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { renameImage as renameImageApi } from '@/api/api-functions';

interface MediaInfoPanelProps {
  show: boolean;
  onClose: () => void;
  currentImage: Image | null;
  currentIndex: number;
  totalImages: number;
}

export const MediaInfoPanel: React.FC<MediaInfoPanelProps> = ({
  show,
  onClose,
  currentImage,
  currentIndex,
  totalImages,
}) => {
  const [isRenaming, setIsRenaming] = useState(false);
  const [newName, setNewName] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
   const [renamedName, setRenamedName] = useState<string | null>(null);

  useEffect(() => {
    // Reset rename state when the current image changes
    setIsRenaming(false);
    setNewName('');
    setError(null);
    setIsSaving(false);
    setRenamedName(null);
  }, [currentImage?.id]);

  const getFormattedDate = () => {
    if (currentImage?.metadata?.date_created) {
      return new Date(currentImage.metadata.date_created).toLocaleDateString(
        'en-US',
        {
          year: 'numeric',
          month: 'long',
          day: 'numeric',
        },
      );
    }
    return 'Date not available';
  };

  const getFileName = useCallback(() => {
    if (!currentImage) return 'Image';
    return currentImage.path?.split(/[/\\]/).pop() || 'Image';
  }, [currentImage]);

  const getBaseName = useCallback(() => {
    const fileName = renamedName || getFileName();
    const lastDotIndex = fileName.lastIndexOf('.');
    if (lastDotIndex <= 0) return fileName;
    return fileName.substring(0, lastDotIndex);
  }, [getFileName]);

  const getExtension = useCallback(() => {
    const fileName = renamedName || getFileName();
    const lastDotIndex = fileName.lastIndexOf('.');
    if (lastDotIndex === -1 || lastDotIndex === fileName.length - 1) return '';
    return fileName.substring(lastDotIndex);
  }, [getFileName]);

  const displayName = useMemo(
    () => renamedName || getFileName(),
    [renamedName, getFileName],
  );

  const handleLocationClick = async () => {
    if (currentImage?.metadata?.latitude && currentImage?.metadata?.longitude) {
      const { latitude, longitude } = currentImage.metadata;
      try {
        await open(`https://maps.google.com/?q=${latitude},${longitude}`);
      } catch (error) {
        console.error('Failed to open map URL:', error);
      }
    }
  };

  const startRenaming = () => {
    setError(null);
    setNewName(getBaseName());
    setIsRenaming(true);
  };

  const cancelRenaming = () => {
    setIsRenaming(false);
    setError(null);
  };

  const handleRenameSubmit = async () => {
    if (!currentImage || !newName.trim()) {
      setError('Name cannot be empty.');
      return;
    }

    try {
      setIsSaving(true);
      setError(null);
      const trimmed = newName.trim();
      await renameImageApi(currentImage.id, trimmed);
      const fullName = `${trimmed}${getExtension()}`;
      setRenamedName(fullName);
      setIsRenaming(false);
    } catch (e: unknown) {
      const maybeAxiosError = e as {
        response?: { data?: { detail?: { message?: string }; message?: string } };
      };
      const message =
        maybeAxiosError.response?.data?.detail?.message ||
        maybeAxiosError.response?.data?.message ||
        (e instanceof Error ? e.message : 'Failed to rename image.');
      setError(message);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ type: 'spring', stiffness: 260, damping: 25 }}
          className="absolute top-10 left-6 z-50 w-[350px] rounded-xl border border-white/10 bg-black/60 p-6 shadow-xl backdrop-blur-lg"
        >
          <div className="mb-4 flex items-center justify-between border-b border-white/10 pb-3">
            <h3 className="text-xl font-medium text-white">Image Details</h3>
            <button
              onClick={onClose}
              className="text-white/70 hover:text-white"
              aria-label="Close info panel"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="space-y-4 text-sm">
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-white/10 p-2">
                <ImageLucide className="h-5 w-5 text-blue-400" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs text-white/50">Name</p>
                  {!isRenaming && (
                    <button
                      type="button"
                      onClick={startRenaming}
                      className="text-xs text-blue-300 hover:text-blue-200"
                    >
                      Rename
                    </button>
                  )}
                </div>
                {isRenaming ? (
                  <div className="mt-1 flex items-center gap-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-1">
                        <Input
                          autoFocus
                          value={newName}
                          onChange={(e) => setNewName(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              e.preventDefault();
                              handleRenameSubmit();
                            } else if (e.key === 'Escape') {
                              e.preventDefault();
                              cancelRenaming();
                            }
                          }}
                          className="h-8 text-sm"
                          placeholder="Enter new name"
                        />
                        <span className="text-sm text-white/70">
                          {getExtension()}
                        </span>
                      </div>
                      {error && (
                        <p className="mt-1 text-xs text-red-400">{error}</p>
                      )}
                    </div>
                    <div className="flex items-center gap-1">
                      <Button
                        size="sm"
                        variant="outline"
                        className="h-8 cursor-pointer px-2 text-xs"
                        onClick={handleRenameSubmit}
                        disabled={isSaving}
                      >
                        Save
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="h-8 cursor-pointer px-2 text-xs text-white/70 hover:text-white"
                        onClick={cancelRenaming}
                        disabled={isSaving}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  <p
                    className="truncate font-medium text-white"
                    title={displayName}
                  >
                    {displayName}
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-white/10 p-2">
                <Calendar className="h-5 w-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-xs text-white/50">Date</p>
                <p className="font-medium text-white">{getFormattedDate()}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-white/10 p-2">
                <MapPin className="h-5 w-5 text-red-400" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-xs text-white/50">Location</p>
                {currentImage?.metadata?.latitude &&
                currentImage?.metadata?.longitude ? (
                  <button
                    type="button"
                    onClick={handleLocationClick}
                    className="flex w-full items-center truncate text-left font-medium text-white hover:underline"
                  >
                    {`Lat: ${currentImage.metadata.latitude.toFixed(4)}, Lon: ${currentImage.metadata.longitude.toFixed(4)}`}
                    <SquareArrowOutUpRight className="ml-1 h-[14px] w-[14px]" />
                  </button>
                ) : (
                  <p className="font-medium text-white">
                    Location not available
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-white/10 p-2">
                <Tag className="h-5 w-5 text-purple-400" />
              </div>
              <div className="flex-1">
                <p className="mb-1 text-xs text-white/50">Tags</p>
                {currentImage?.tags?.length ? (
                  <div className="flex flex-wrap gap-2">
                    {currentImage.tags.map((tag, i) => (
                      <span
                        key={i}
                        className="rounded-full border border-blue-500/30 bg-blue-500/20 px-2 py-1 text-xs text-blue-300"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-white/60">No tags available</p>
                )}
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-white/10 p-2">
                <Info className="h-5 w-5 text-amber-400" />
              </div>
              <div>
                <p className="text-xs text-white/50">Position</p>
                <p className="font-medium text-white">
                  {currentIndex + 1} of {totalImages}
                </p>
              </div>
            </div>

            <div className="mt-4 border-t border-white/10 pt-3">
              <button
                className="w-full rounded-lg bg-white/10 py-2 text-white hover:bg-white/20"
                onClick={(e) => {
                  e.preventDefault();
                  // Button disabled - does nothing
                }}
              >
                Open Original File
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
