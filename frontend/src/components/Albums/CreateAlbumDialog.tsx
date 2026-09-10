import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

/**
 * CreateAlbumDialog Component
 *
 * Provides a modal dialog interface for creating a new photo album.
 * Note: Albums in PictoPy currently only support photos (image organization).
 */

export interface CreateAlbumDialogProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  onCreateAlbum?: (name: string, description?: string) => void;
}

export const CreateAlbumDialog: React.FC<CreateAlbumDialogProps> = ({
  open,
  onOpenChange,
  onCreateAlbum,
}) => {
  const [internalOpen, setInternalOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);

  const isControlled = open !== undefined;
  const dialogOpen = isControlled ? open : internalOpen;

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      setName('');
      setDescription('');
      setError(null);
    }
    if (onOpenChange) {
      onOpenChange(newOpen);
    } else {
      setInternalOpen(newOpen);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Album name is required');
      return;
    }
    if (onCreateAlbum) {
      onCreateAlbum(name.trim(), description.trim());
    }
    handleOpenChange(false);
  };

  return (
    <Dialog open={dialogOpen} onOpenChange={handleOpenChange}>
      {!isControlled && (
        <DialogTrigger asChild>
          <Button variant="default">Create Album</Button>
        </DialogTrigger>
      )}
      <form onSubmit={handleSubmit}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Create Album</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-2">
            <div className="space-y-2">
              <Label htmlFor="album-name">Album Name</Label>
              <Input
                id="album-name"
                placeholder="e.g. Summer Vacation"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
              {error && <p className="text-sm text-destructive">{error}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="album-description">Description (optional)</Label>
              <Input
                id="album-description"
                placeholder="Add a brief description..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
          </div>
          <div className="flex justify-between items-center pt-4">
            <Button type="button" variant="outline" onClick={() => handleOpenChange(false)}>Cancel</Button>
            <Button type="submit">Create</Button>
          </div>
          <DialogDescription className="text-xs text-muted-foreground mt-2">
            Create a new album to organize your photos.
          </DialogDescription>
        </DialogContent>
      </form>
    </Dialog>
  );
};

export default CreateAlbumDialog;
