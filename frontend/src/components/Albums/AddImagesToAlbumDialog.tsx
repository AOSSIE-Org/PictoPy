import React, { useState, useEffect } from 'react';
import { useDispatch } from 'react-redux';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AddImagesToAlbumDialogProps } from '@/types/Album';
import { usePictoMutation, usePictoQuery } from '@/hooks/useQueryExtension';
import { addImagesToAlbum, fetchAllImages } from '@/api/api-functions';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { hideLoader, showLoader } from '@/features/loaderSlice';
import { Image } from '@/types/Media';
import { convertFileSrc } from '@tauri-apps/api/core';
import { Search, Check } from 'lucide-react';

export const AddImagesToAlbumDialog: React.FC<AddImagesToAlbumDialogProps> = ({
  isOpen,
  onClose,
  albumId,
  albumName,
}) => {
  const dispatch = useDispatch();
  const [selectedImages, setSelectedImages] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [allImages, setAllImages] = useState<Image[]>([]);

  const { data: imagesData, isLoading } = usePictoQuery({
    queryKey: ['images'],
    queryFn: () => fetchAllImages(),
    enabled: isOpen,
  });

  useEffect(() => {
    if (imagesData?.data) {
      setAllImages(imagesData.data as Image[]);
    }
  }, [imagesData]);

  const { mutate: addImagesMutate, isPending } = usePictoMutation({
    mutationFn: (data: { image_ids: string[] }) =>
      addImagesToAlbum(albumId, data),
    onSuccess: () => {
      dispatch(hideLoader());
      dispatch(
        showInfoDialog({
          title: 'Success',
          message: `Added ${selectedImages.size} image${selectedImages.size > 1 ? 's' : ''} to album!`,
          variant: 'info',
        }),
      );
      handleClose();
    },
    onError: (error: any) => {
      dispatch(hideLoader());
      dispatch(
        showInfoDialog({
          title: 'Error',
          message: error?.message || 'Failed to add images. Please try again.',
          variant: 'error',
        }),
      );
    },
  });

  const handleImageToggle = (imageId: string) => {
    const newSelected = new Set(selectedImages);
    if (newSelected.has(imageId)) {
      newSelected.delete(imageId);
    } else {
      newSelected.add(imageId);
    }
    setSelectedImages(newSelected);
  };

  const handleSubmit = () => {
    if (selectedImages.size === 0) {
      dispatch(
        showInfoDialog({
          title: 'No Images Selected',
          message: 'Please select at least one image to add to the album.',
          variant: 'info',
        }),
      );
      return;
    }

    dispatch(showLoader('Adding images to album...'));
    addImagesMutate({ image_ids: Array.from(selectedImages) });
  };

  const handleClose = () => {
    setSelectedImages(new Set());
    setSearchQuery('');
    onClose();
  };

  const filteredImages = allImages.filter((image) => {
    const searchLower = searchQuery.toLowerCase();
    const fileName = image.path.split('/').pop()?.toLowerCase() || '';
    return fileName.includes(searchLower);
  });

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="flex max-h-[80vh] flex-col overflow-hidden p-0 sm:max-w-[700px]">
        <DialogHeader className="px-6 pt-6">
          <DialogTitle>Add Images to "{albumName}"</DialogTitle>
          <DialogDescription>
            Select images to add to this album. You can select multiple images.
          </DialogDescription>
        </DialogHeader>
        <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-hidden px-6 py-4">
          {/* Search Input */}
          <div className="relative shrink-0">
            <Search className="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
            <Input
              placeholder="Search images..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
          {/* Image Grid */}
          <ScrollArea className="flex-1 overflow-auto">
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <p className="text-muted-foreground">Loading images...</p>
              </div>
            ) : filteredImages.length === 0 ? (
              <div className="flex items-center justify-center py-8">
                <p className="text-muted-foreground">
                  {searchQuery
                    ? 'No images found matching your search'
                    : 'No images available'}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-4 gap-3 p-4">
                {filteredImages.map((image) => (
                  <div
                    key={image.id}
                    className="group hover:border-primary relative aspect-square cursor-pointer overflow-hidden rounded-md border-2 transition-all"
                    style={{
                      borderColor: selectedImages.has(image.id)
                        ? 'hsl(var(--primary))'
                        : 'transparent',
                    }}
                    onClick={() => handleImageToggle(image.id)}
                  >
                    <img
                      src={convertFileSrc(image.thumbnailPath)}
                      alt=""
                      className="h-full w-full object-cover"
                      onError={(e) => {
                        const img = e.target as HTMLImageElement;
                        img.onerror = null;
                        const placeholder = window.matchMedia(
                          '(prefers-color-scheme: dark)',
                        ).matches
                          ? '/placeholder-album.svg'
                          : '/placeholder-album-light.svg';
                        img.src = placeholder;
                      }}
                    />

                    {selectedImages.has(image.id) && (
                      <div className="bg-primary/20 absolute inset-0 flex items-center justify-center">
                        <div className="bg-primary flex h-8 w-8 items-center justify-center rounded-full">
                          <Check className="text-primary-foreground h-5 w-5" />
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </div>
        {/* Selected Count */}
        {selectedImages.size > 0 && (
          <div className="px-6 pb-2">
            <p className="text-muted-foreground text-sm">
              {selectedImages.size} image{selectedImages.size > 1 ? 's' : ''}{' '}
              selected
            </p>
          </div>
        )}
        <DialogFooter className="px-6 pb-6">
          <Button
            type="button"
            variant="outline"
            onClick={handleClose}
            disabled={isPending}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isPending || selectedImages.size === 0}
          >
            {isPending
              ? 'Adding...'
              : `Add ${selectedImages.size > 0 ? selectedImages.size : ''} Image${selectedImages.size !== 1 ? 's' : ''}`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
