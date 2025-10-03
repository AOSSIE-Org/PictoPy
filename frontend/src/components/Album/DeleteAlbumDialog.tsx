import { deleteAlbum, fetchAlbum } from '@/api/api-functions/albums';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { removeAlbum } from '@/features/albumSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { usePictoMutation, usePictoQuery } from '@/hooks/useQueryExtension';
import * as React from 'react';
import { useDispatch } from 'react-redux';

interface DeleteAlbumDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  albumId: string;
  albumName: string;
  onAlbumDeleted?: () => void;
}

export function DeleteAlbumDialog({
  open,
  onOpenChange,
  albumId,
  albumName,
  onAlbumDeleted,
}: DeleteAlbumDialogProps) {
  const dispatch = useDispatch();
  const [confirmText, setConfirmText] = React.useState('');
  const [error, setError] = React.useState('');

  // Fetch album details to check if it's hidden
  const { data: albumData } = usePictoQuery({
    queryKey: ['album', albumId],
    queryFn: () => fetchAlbum(albumId),
    enabled: open && !!albumId,
  });

  const deleteAlbumMutation = usePictoMutation({
    mutationFn: () => deleteAlbum(albumId),
    onSuccess: (_data: any) => {
      // Remove album from Redux store
      dispatch(removeAlbum(albumId));

      // Show success message
      dispatch(
        showInfoDialog({
          title: 'Success',
          message: `Album "${albumName}" has been deleted.`,
          variant: 'info',
        }),
      );

      // Call callback
      onAlbumDeleted?.();

      // Close dialog
      handleClose();
    },
    onError: (_error: any) => {
      dispatch(
        showInfoDialog({
          title: 'Error',
          message: 'Failed to delete album. Please try again.',
          variant: 'error',
        }),
      );
    },
  });

  // Use mutation feedback hook
  useMutationFeedback(deleteAlbumMutation, {
    loadingMessage: 'Deleting album...',
    showSuccess: false, // We handle success manually above
    showError: false, // We handle errors manually above
    errorTitle: 'Failed to Delete Album',
  });

  const handleClose = () => {
    setConfirmText('');
    setError('');
    onOpenChange(false);
  };

  const handleDelete = () => {
    // Validate confirmation text
    if (confirmText !== albumName) {
      setError(
        'Album name does not match. Please type the exact album name to confirm.',
      );
      return;
    }

    setError('');
    deleteAlbumMutation.mutate(undefined);
  };

  const isDeleteDisabled =
    confirmText !== albumName || deleteAlbumMutation.isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="w-[95vw] sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Delete Album</DialogTitle>
          <DialogDescription>
            This action cannot be undone. This will permanently delete the album{' '}
            <span className="text-foreground font-semibold">"{albumName}"</span>
            {albumData?.data?.is_hidden && (
              <span className="mt-2 block text-yellow-600 dark:text-yellow-500">
                Warning: This is a hidden album.
              </span>
            )}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="confirm-album-name">
              Type <span className="font-semibold">{albumName}</span> to
              confirm:
            </Label>
            <Input
              id="confirm-album-name"
              placeholder="Enter album name"
              value={confirmText}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                setConfirmText(e.target.value);
                setError('');
              }}
              onKeyDown={(e: any) => {
                if (e.key === 'Enter' && !isDeleteDisabled) {
                  handleDelete();
                }
              }}
              className={error ? 'border-red-500' : ''}
              disabled={deleteAlbumMutation.isPending}
            />
            {error && <p className="text-sm text-red-600">{error}</p>}
          </div>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={deleteAlbumMutation.isPending}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={handleDelete}
            disabled={isDeleteDisabled}
          >
            {deleteAlbumMutation.isPending ? 'Deleting...' : 'Delete Album'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
