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
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Switch } from '@/components/ui/switch';
import { EditAlbumDialogProps } from '@/types/Album';
import { usePictoMutation } from '@/hooks/useQueryExtension';
import { updateAlbum } from '@/api/api-functions';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { hideLoader, showLoader } from '@/features/loaderSlice';

export const EditAlbumDialog: React.FC<EditAlbumDialogProps> = ({
  album,
  isOpen,
  onClose,
  onSuccess,
}) => {
  const dispatch = useDispatch();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    is_locked: false,
    current_password: '',
    password: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const { mutate: updateAlbumMutate, isPending } = usePictoMutation({
    mutationFn: ({ albumId, data }: { albumId: string; data: any }) =>
      updateAlbum(albumId, data),
    onSuccess: () => {
      dispatch(hideLoader());
      dispatch(
        showInfoDialog({
          title: 'Success',
          message: 'Album updated successfully!',
          variant: 'info',
        }),
      );

      // Trigger refetch to update the albums list
      if (onSuccess) {
        onSuccess();
      }

      handleClose();
    },
    onError: (error: any) => {
      dispatch(hideLoader());

      // Extract detailed error message from backend response
      let errorMessage = 'Failed to update album. Please try again.';

      if (error?.response?.data?.detail?.message) {
        errorMessage = error.response.data.detail.message;
      } else if (error?.message) {
        errorMessage = error.message;
      }

      dispatch(
        showInfoDialog({
          title: 'Error',
          message: errorMessage,
          variant: 'error',
        }),
      );
    },
  });

  useEffect(() => {
    if (album) {
      setFormData({
        name: album.name,
        description: album.description,
        is_locked: album.is_locked,
        current_password: '',
        password: '',
      });
    }
  }, [album]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Album name is required';
    }

    // If album was locked originally, require current password for any changes (including unlocking)
    if (album?.is_locked && !formData.current_password.trim()) {
      newErrors.current_password =
        'Current password is required to modify locked album';
    }

    // If making album locked (and it wasn't before), require new password
    if (formData.is_locked && !album?.is_locked && !formData.password.trim()) {
      newErrors.password = 'Password is required for locked albums';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!album || !validateForm()) {
      return;
    }

    dispatch(showLoader('Updating album...'));

    const requestData: any = {
      name: formData.name.trim(),
      ...(formData.description.trim() && {
        description: formData.description.trim(),
      }),
      is_locked: formData.is_locked,
    };

    // Add current password if album was originally locked (required by backend)
    if (album.is_locked) {
      requestData.current_password = formData.current_password.trim();
    }

    // Add new password if provided (for locking or changing password)
    if (formData.password.trim()) {
      requestData.password = formData.password.trim();
    }

    updateAlbumMutate({ albumId: album.id, data: requestData });
  };

  const handleClose = () => {
    setFormData({
      name: '',
      description: '',
      is_locked: false,
      current_password: '',
      password: '',
    });
    setErrors({});
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Edit Album</DialogTitle>
            <DialogDescription>
              Update album details. Changes will be saved immediately.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            {/* Album Name */}
            <div className="grid gap-2">
              <Label htmlFor="name">
                Album Name <span className="text-destructive">*</span>
              </Label>
              <Input
                id="name"
                placeholder="Enter album name"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                className={errors.name ? 'border-destructive' : ''}
              />
              {errors.name && (
                <p className="text-destructive text-sm">{errors.name}</p>
              )}
            </div>

            {/* Album Description */}
            <div className="grid gap-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                placeholder="Enter album description"
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                rows={3}
                className={errors.description ? 'border-destructive' : ''}
              />
              {errors.description && (
                <p className="text-destructive text-sm">{errors.description}</p>
              )}
            </div>

            {/* Current Password (shown if album was originally locked) */}
            {album?.is_locked && (
              <div className="grid gap-2">
                <Label htmlFor="current_password">
                  Current Password <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="current_password"
                  type="password"
                  placeholder="Enter current password"
                  value={formData.current_password}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      current_password: e.target.value,
                    })
                  }
                  className={
                    errors.current_password ? 'border-destructive' : ''
                  }
                />
                {errors.current_password && (
                  <p className="text-destructive text-sm">
                    {errors.current_password}
                  </p>
                )}
                <p className="text-muted-foreground text-sm">
                  Required to make changes to this locked album
                </p>
              </div>
            )}

            {/* Lock Album Toggle */}
            <div className="flex items-center justify-between space-x-2">
              <div className="space-y-0.5">
                <Label htmlFor="locked">Lock Album</Label>
                <p className="text-muted-foreground text-sm">
                  Protect your album with a password
                </p>
              </div>
              <Switch
                id="locked"
                checked={formData.is_locked}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, is_locked: checked })
                }
              />
            </div>

            {/* New Password Field */}
            {formData.is_locked && (
              <div className="grid gap-2">
                <Label htmlFor="password">
                  {album?.is_locked ? 'New Password (optional)' : 'Password'}
                  {!album?.is_locked && (
                    <span className="text-destructive"> *</span>
                  )}
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder={
                    album?.is_locked
                      ? 'Enter new password to change'
                      : 'Enter password'
                  }
                  value={formData.password}
                  onChange={(e) =>
                    setFormData({ ...formData, password: e.target.value })
                  }
                  className={errors.password ? 'border-destructive' : ''}
                />
                {errors.password && (
                  <p className="text-destructive text-sm">{errors.password}</p>
                )}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending ? 'Saving...' : 'Save Changes'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
