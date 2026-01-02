import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  fetchDeletedImages,
  permanentDeleteImages,
  restoreImages,
} from '@/api/api-functions';
import { Image } from '@/types/Media';
import { RefreshCw, RotateCcw, Trash2 } from 'lucide-react';
import { HistoryToolbar } from '@/components/Gallery/HistoryToolbar';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { Button } from '@/components/ui/button';
import { ImageCard } from '@/components/Media/ImageCard';

export function History() {
  const [selectedImages, setSelectedImages] = useState<string[]>([]);

  // ---------------- Queries ----------------
  const {
    data: deletedImagesData,
    isLoading: isLoadingDeleted,
    refetch: refetchDeleted,
  } = useQuery({
    queryKey: ['deleted-images'],
    queryFn: fetchDeletedImages,
  });



  // ---------------- Mutations ----------------

  const permanentDeleteMutation = useMutation({
    mutationFn: permanentDeleteImages,
    onSuccess: () => {
      setSelectedImages([]);
      refetchDeleted();
    },
  });

  useMutationFeedback(permanentDeleteMutation, {
    loadingMessage: 'Permanently deleting images...',
    successMessage: `${selectedImages.length} images permanently deleted`,
    showSuccess: true,
  });

  const restoreMutation = useMutation({
    mutationFn: restoreImages,
    onSuccess: () => {
      setSelectedImages([]);
      refetchDeleted();
    },
  });

  useMutationFeedback(restoreMutation, {
    loadingMessage: 'Restoring images...',
    successMessage: 'Image restored successfully',
    showSuccess: true,
  });

  // ---------------- Data ----------------

  const deletedImages = (deletedImagesData?.data ?? []) as Image[];

  // ---------------- Handlers ----------------

  const handleSelectImage = (imageId: string) => {
    setSelectedImages((prev) =>
      prev.includes(imageId)
        ? prev.filter((id) => id !== imageId)
        : [...prev, imageId],
    );
  };

  const handleSelectAll = () => {
    if (selectedImages.length === deletedImages.length) {
      setSelectedImages([]);
    } else {
      setSelectedImages(deletedImages.map((img) => img.id));
    }
  };

  const handlePermanentDelete = () => {
    if (selectedImages.length > 0) {
      permanentDeleteMutation.mutate(selectedImages);
    }
  };

  const handleRestoreSingle = (imageId: string) => {
    restoreMutation.mutate([imageId]);
  };

  // ---------------- UI ----------------

  return (
    <div className="flex h-full flex-col">
      <HistoryToolbar
        selectedCount={selectedImages.length}
        totalCount={deletedImages.length}
        onSelectAll={handleSelectAll}
        onDelete={handlePermanentDelete}
        isDeleting={permanentDeleteMutation.isPending}
      />

      <div className="flex-1 overflow-y-auto p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold">Recently Deleted</h1>
          <p className="text-muted-foreground">
            Images are automatically permanently deleted after 30 days
          </p>
        </div>

        {isLoadingDeleted ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="h-8 w-8 animate-spin" />
          </div>
        ) : deletedImages.length > 0 ? (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {deletedImages.map((image) => (
              <div
                key={image.id}
                className={`relative ${
                  selectedImages.includes(image.id)
                    ? 'ring-2 ring-blue-500 rounded-lg'
                    : ''
                }`}
              >
                {/* Checkbox */}
                <input
                  type="checkbox"
                  checked={selectedImages.includes(image.id)}
                  onChange={() => handleSelectImage(image.id)}
                  className="absolute top-2 left-2 z-10"
                />

                {/* Image Card */}
                <ImageCard
                  image={image}
                  showTags={false}
                />

                {/* Actions */}
                <div className="absolute bottom-2 right-2 flex gap-2">
                  <Button
                    size="icon"
                    variant="secondary"
                    onClick={() => handleRestoreSingle(image.id)}
                  >
                    <RotateCcw className="h-4 w-4" />
                  </Button>

                  <Button
                    size="icon"
                    variant="destructive"
                    onClick={() =>
                      permanentDeleteMutation.mutate([image.id])
                    }
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <p className="text-muted-foreground">
              No recently deleted images
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
         