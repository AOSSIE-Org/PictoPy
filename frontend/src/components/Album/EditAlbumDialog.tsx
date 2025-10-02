import {
  fetchAlbum,
  updateAlbum,
  UpdateAlbumRequest,
} from '@/api/api-functions/albums';
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
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { updateAlbum as updateAlbumInStore } from '@/features/albumSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { usePictoMutation, usePictoQuery } from '@/hooks/useQueryExtension';
import * as React from 'react';
import { useDispatch } from 'react-redux';

interface EditAlbumDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  albumId: string;
  onAlbumUpdated?: () => void;
}

export function EditAlbumDialog({
  open,
  onOpenChange,
  albumId,
  onAlbumUpdated,
}: EditAlbumDialogProps) {
  const dispatch = useDispatch();
  const [albumName, setAlbumName] = React.useState('');
  const [description, setDescription] = React.useState('');
  const [isHidden, setIsHidden] = React.useState(false);
  const [currentPassword, setCurrentPassword] = React.useState('');
  const [newPassword, setNewPassword] = React.useState('');
  const [errors, setErrors] = React.useState<Record<string, string>>({});
  const [isInitialized, setIsInitialized] = React.useState(false);

  // Fetch album details
  const { data: albumData, isLoading } = usePictoQuery({
    queryKey: ['album', albumId],
    queryFn: () => fetchAlbum(albumId),
    enabled: open && !!albumId,
  });

  // Initialize form when album data loads
  React.useEffect(() => {
    if (albumData?.data && !isInitialized) {
      setAlbumName(albumData.data.album_name);
      setDescription(albumData.data.description || '');
      setIsHidden(albumData.data.is_hidden);
      setIsInitialized(true);
    }
  }, [albumData, isInitialized]);

  // Reset form when dialog closes
  React.useEffect(() => {
    if (!open) {
      setIsInitialized(false);
      setCurrentPassword('');
      setNewPassword('');
      setErrors({});
    }
  }, [open]);

  const updateAlbumMutation = usePictoMutation({
    mutationFn: (data: UpdateAlbumRequest) => updateAlbum(albumId, data),
    onSuccess: (_data: any) => {
      // Update album in Redux store
      dispatch(
        updateAlbumInStore({
          albumId: albumId,
          updates: {
            album_name: albumName,
            description: description,
            is_hidden: isHidden,
          },
        }),
      );

      // Show success message
      dispatch(
        showInfoDialog({
          title: 'Success',
          message: `Album "${albumName}" updated successfully!`,
          variant: 'info',
        }),
      );

      // Call callback
      onAlbumUpdated?.();

      // Close dialog
      onOpenChange(false);
    },
    onError: (_error: any) => {
      dispatch(
        showInfoDialog({
          title: 'Error',
          message:
            'Failed to update album. Please check your password and try again.',
          variant: 'error',
        }),
      );
    },
  });

  // Use mutation feedback hook
  useMutationFeedback(updateAlbumMutation, {
    loadingMessage: 'Updating album...',
    showSuccess: false, // We handle success manually above
    errorTitle: 'Failed to Update Album',
  });

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!albumName.trim()) {
      newErrors.albumName = 'Album name is required';
    }

    // If album was hidden, require current password
    if (albumData?.data?.is_hidden && !currentPassword.trim()) {
      newErrors.currentPassword =
        'Current password is required for hidden albums';
    }

    // If making album hidden (or it was already hidden), need a password
    if (isHidden && !newPassword.trim() && !albumData?.data?.is_hidden) {
      newErrors.newPassword = 'Password is required for hidden albums';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const albumUpdateData: UpdateAlbumRequest = {
      name: albumName.trim(),
      description: description.trim(),
      is_hidden: isHidden,
    };

    // Add current password if album was hidden
    if (albumData?.data?.is_hidden) {
      albumUpdateData.current_password = currentPassword;
    }

    // Add new password if setting hidden or changing password
    if (isHidden && newPassword.trim()) {
      albumUpdateData.password = newPassword;
    }

    updateAlbumMutation.mutate(albumUpdateData);
  };

  const handleCancel = () => {
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] w-[95vw] overflow-y-auto sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Edit Album</DialogTitle>
          <DialogDescription>
            Update album details and settings.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="py-8 text-center">
            <p className="text-muted-foreground">Loading album details...</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Album Name */}
            <div className="space-y-2">
              <Label htmlFor="edit-album-name">Album Name</Label>
              <Input
                id="edit-album-name"
                placeholder="Enter album name"
                value={albumName}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setAlbumName(e.target.value)
                }
                className={errors.albumName ? 'border-red-500' : ''}
              />
              {errors.albumName && (
                <p className="text-sm text-red-600">{errors.albumName}</p>
              )}
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="edit-description">Description (Optional)</Label>
              <Textarea
                id="edit-description"
                placeholder="Enter album description"
                value={description}
                onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                  setDescription(e.target.value)
                }
                rows={3}
              />
            </div>

            {/* Hidden Album Toggle */}
            <div className="flex items-center justify-between rounded-lg border p-4">
              <div className="space-y-0.5">
                <Label htmlFor="edit-hidden-album">Hidden Album</Label>
                <p className="text-muted-foreground text-sm">
                  Hidden albums require a password to view
                </p>
              </div>
              <Switch
                id="edit-hidden-album"
                checked={isHidden}
                onCheckedChange={setIsHidden}
              />
            </div>

            {/* Current Password (only if album was hidden) */}
            {albumData?.data?.is_hidden && (
              <div className="space-y-2">
                <Label htmlFor="current-password">Current Password</Label>
                <Input
                  id="current-password"
                  type="password"
                  placeholder="Enter current password"
                  value={currentPassword}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setCurrentPassword(e.target.value)
                  }
                  className={errors.currentPassword ? 'border-red-500' : ''}
                />
                {errors.currentPassword && (
                  <p className="text-sm text-red-600">
                    {errors.currentPassword}
                  </p>
                )}
              </div>
            )}

            {/* New Password (only if hidden) */}
            {isHidden && (
              <div className="space-y-2">
                <Label htmlFor="new-password">
                  {albumData?.data?.is_hidden
                    ? 'New Password (leave blank to keep current)'
                    : 'Password'}
                </Label>
                <Input
                  id="new-password"
                  type="password"
                  placeholder={
                    albumData?.data?.is_hidden
                      ? 'Enter new password (optional)'
                      : 'Enter album password'
                  }
                  value={newPassword}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    setNewPassword(e.target.value)
                  }
                  className={errors.newPassword ? 'border-red-500' : ''}
                />
                {errors.newPassword && (
                  <p className="text-sm text-red-600">{errors.newPassword}</p>
                )}
              </div>
            )}

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={handleCancel}
                disabled={updateAlbumMutation.isPending}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={updateAlbumMutation.isPending || isLoading}
              >
                Update Album
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}
