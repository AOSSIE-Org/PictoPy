import React, { useState } from 'react';
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
import { CreateAlbumDialogProps } from '@/types/Album';
import { usePictoMutation } from '@/hooks/useQueryExtension';
import { createAlbum } from '@/api/api-functions';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';

export const CreateAlbumDialog: React.FC<CreateAlbumDialogProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    is_locked: false,
    password: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const createAlbumMutation = usePictoMutation({
    mutationFn: createAlbum,
  });

  useMutationFeedback(createAlbumMutation, {
    loadingMessage: 'Creating album...',
    successTitle: 'Success',
    successMessage: 'Album created successfully!',
    errorTitle: 'Error',
    errorMessage: 'Failed to create album. Please try again.',
    onSuccess: () => {
      if (onSuccess) {
        onSuccess();
      }
      handleClose();
    },
  });

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Album name is required';
    }

    if (formData.is_locked && !formData.password.trim()) {
      newErrors.password = 'Password is required for locked albums';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const requestData = {
      name: formData.name.trim(),
      ...(formData.description.trim() && {
        description: formData.description.trim(),
      }),
      is_locked: formData.is_locked,
      ...(formData.is_locked && { password: formData.password }),
    };

    createAlbumMutation.mutate(requestData);
  };

  const handleClose = () => {
    setFormData({
      name: '',
      description: '',
      is_locked: false,
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
            <DialogTitle>Create New Album</DialogTitle>
            <DialogDescription>
              Create a new album to organize your photos and videos.
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

            {/* Password Field (shown only if locked) */}
            {formData.is_locked && (
              <div className="grid gap-2">
                <Label htmlFor="password">
                  Password <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter a password"
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
              disabled={createAlbumMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createAlbumMutation.isPending}>
              {createAlbumMutation.isPending ? 'Creating...' : 'Create Album'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
};
