import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
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
import { Label } from '@/components/ui/label';
import { ROUTES } from '@/constants/routes';
import { usePictoMutation } from '@/hooks/useQueryExtension';
import { createAlbumFromMemory } from '@/api/api-functions';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import type { MemoryCard } from '@/api/api-functions/memories';
import { formatPhotoCount } from '@/utils/memories';

interface ConvertMemoryToAlbumDialogProps {
  memory: MemoryCard | null;
  isOpen: boolean;
  onClose: () => void;
}

/**
 * Copies a memory's photos into a new album. The name is pre-filled from the
 * memory's title; everything else about the album is edited afterwards.
 */
export const ConvertMemoryToAlbumDialog: React.FC<
  ConvertMemoryToAlbumDialogProps
> = ({ memory, isOpen, onClose }) => {
  const navigate = useNavigate();
  const [name, setName] = useState('');
  const [error, setError] = useState('');

  // One mounted dialog serves every tile, so the name follows the selected
  // memory rather than the first render.
  useEffect(() => {
    if (memory) {
      setName(memory.title);
      setError('');
    }
  }, [memory]);

  const convertMutation = usePictoMutation({
    mutationFn: createAlbumFromMemory,
    autoInvalidateTags: ['albums'],
  });

  useMutationFeedback(convertMutation, {
    loadingMessage: 'Creating album...',
    successTitle: 'Success',
    successMessage: 'Album created from memory!',
    errorTitle: 'Error',
    // A duplicate name comes back as a 409 and getErrorMessage surfaces the
    // backend's own wording, so the dialog stays open to be renamed.
    errorMessage: 'Failed to create the album. Please try again.',
    onSuccess: () => {
      const albumId = convertMutation.successData?.album_id;
      onClose();
      if (albumId) {
        navigate(`/${ROUTES.ALBUMS}/${albumId}`);
      }
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!memory) return;

    if (!name.trim()) {
      setError('Album name is required');
      return;
    }

    setError('');
    convertMutation.mutate({ memory_id: memory.memory_id, name: name.trim() });
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Convert to Album</DialogTitle>
            <DialogDescription>
              Creates an album from this memory's{' '}
              {formatPhotoCount(memory?.image_count ?? 0)}. The memory itself is
              kept.
              {memory !== null &&
                memory.video_count > 0 &&
                ' Videos are left out — albums hold photos only.'}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="album-name">
                Album Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="album-name"
                placeholder="Enter album name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className={error ? 'border-destructive' : ''}
              />
              {error && <p className="text-destructive text-sm">{error}</p>}
            </div>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={onClose}
              disabled={convertMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={convertMutation.isPending}>
              {convertMutation.isPending ? 'Creating...' : 'Create Album'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
