import * as React from 'react';
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
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { usePictoMutation } from '@/hooks/useQueryExtension';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { createAlbum, CreateAlbumRequest } from '@/api/api-functions/albums';
import { addAlbum } from '@/features/albumSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';

interface CreateAlbumDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedImageIds?: string[];
  onAlbumCreated?: (albumId: string) => void;
}

export function CreateAlbumDialog({
  open,
  onOpenChange,
  selectedImageIds = [],
  onAlbumCreated,
}: CreateAlbumDialogProps) {
  const dispatch = useDispatch();
  const [albumName, setAlbumName] = React.useState('');
  const [description, setDescription] = React.useState('');
  const [isHidden, setIsHidden] = React.useState(false);
  const [password, setPassword] = React.useState('');
  const [errors, setErrors] = React.useState<Record<string, string>>({});

  const createAlbumMutation = usePictoMutation({
    mutationFn: (data: CreateAlbumRequest) => createAlbum(data),
    onSuccess: (data: any) => {
      if (data.success) {
        // Add album to Redux store
        dispatch(
          addAlbum({
            album_id: data.album_id,
            album_name: albumName,
            description: description,
            is_hidden: isHidden,
          }),
        );

        // Show success message
        dispatch(
          showInfoDialog({
            title: 'Success',
            message: `Album "${albumName}" created successfully!`,
            variant: 'info',
          }),
        );

        // Call callback with album ID
        onAlbumCreated?.(data.album_id);

        // Reset form and close dialog
        resetForm();
        onOpenChange(false);
      }
    },
    onError: (_error: any) => {
      dispatch(
        showInfoDialog({
          title: 'Error',
          message: 'Failed to create album. Please try again.',
          variant: 'error',
        }),
      );
    },
  });

  // Use mutation feedback hook
  useMutationFeedback(createAlbumMutation, {
    loadingMessage: 'Creating album...',
    showSuccess: false, // We handle success manually above
    errorTitle: 'Failed to Create Album',
  });

  const resetForm = () => {
    setAlbumName('');
    setDescription('');
    setIsHidden(false);
    setPassword('');
    setErrors({});
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!albumName.trim()) {
      newErrors.albumName = 'Album name is required';
    }

    if (isHidden && !password.trim()) {
      newErrors.password = 'Password is required for hidden albums';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const albumData: CreateAlbumRequest = {
      name: albumName.trim(),
      description: description.trim(),
      is_hidden: isHidden,
      password: isHidden ? password : undefined,
    };

    createAlbumMutation.mutate(albumData);
  };

  const handleCancel = () => {
    resetForm();
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md w-[95vw] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create New Album</DialogTitle>
          <DialogDescription>
            {selectedImageIds.length > 0
              ? `Create a new album with ${selectedImageIds.length} selected photo${
                  selectedImageIds.length > 1 ? 's' : ''
                }.`
              : 'Create a new album to organize your photos.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Album Name */}
          <div className="space-y-2">
            <Label htmlFor="album-name">Album Name</Label>
            <Input
              id="album-name"
              placeholder="Enter album name"
              value={albumName}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setAlbumName(e.target.value)}
              className={errors.albumName ? 'border-red-500' : ''}
            />
            {errors.albumName && (
              <p className="text-sm text-red-600">{errors.albumName}</p>
            )}
          </div>

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="description">Description (Optional)</Label>
            <Textarea
              id="description"
              placeholder="Enter album description"
              value={description}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setDescription(e.target.value)}
              rows={3}
            />
          </div>

          {/* Hidden Album Toggle */}
          <div className="flex items-center justify-between rounded-lg border p-4">
            <div className="space-y-0.5">
              <Label htmlFor="hidden-album">Hidden Album</Label>
              <p className="text-sm text-muted-foreground">
                Hidden albums require a password to view
              </p>
            </div>
            <Switch
              id="hidden-album"
              checked={isHidden}
              onCheckedChange={setIsHidden}
            />
          </div>

          {/* Password (only if hidden) */}
          {isHidden && (
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter album password"
                value={password}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
                className={errors.password ? 'border-red-500' : ''}
              />
              {errors.password && (
                <p className="text-sm text-red-600">{errors.password}</p>
              )}
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleCancel}
              disabled={createAlbumMutation.isPending}
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={createAlbumMutation.isPending}
            >
              Create Album
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}