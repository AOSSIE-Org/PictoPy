import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Alert } from '@/components/ui/alert';
import type { SmartAlbum } from '@/api/api-functions/smart_albums';

interface EditAlbumDialogProps {
  open: boolean;
  album: SmartAlbum | null;
  onClose: () => void;
  onUpdate: (albumId: string, name: string, autoUpdate: boolean) => Promise<void>;
}

export const EditAlbumDialog: React.FC<EditAlbumDialogProps> = ({
  open,
  album,
  onClose,
  onUpdate,
}) => {
  const [albumName, setAlbumName] = useState('');
  const [autoUpdate, setAutoUpdate] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (album) {
      setAlbumName(album.album_name);
      setAutoUpdate(album.auto_update);
    }
  }, [album]);

  const handleSubmit = async () => {
    if (!album) return;

    if (!albumName.trim()) {
      setError('Album name is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await onUpdate(album.album_id, albumName, autoUpdate);
      handleClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update album');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setError(null);
    onClose();
  };

  if (!album) return null;

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Edit Album</DialogTitle>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Album Type (Read-only) */}
          <div className="space-y-2">
            <Label>Album Type</Label>
            <Badge
              variant={album.album_type === 'object' ? 'default' : 'secondary'}
              className="capitalize"
            >
              {album.album_type}
            </Badge>
          </div>

          {/* Criteria (Read-only) */}
          {album.criteria.class_names && album.criteria.class_names.length > 0 && (
            <div className="space-y-2">
              <Label>Object Classes (cannot be edited)</Label>
              <div className="flex flex-wrap gap-2">
                {album.criteria.class_names.map((className) => (
                  <Badge key={className} variant="outline">
                    {className}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Album Name (Editable) */}
          <div className="space-y-2">
            <Label htmlFor="edit-album-name">Album Name</Label>
            <Input
              id="edit-album-name"
              value={albumName}
              onChange={(e) => setAlbumName(e.target.value)}
              placeholder="Enter album name"
              autoFocus
            />
          </div>

          {/* Auto Update (Editable) */}
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
            <div className="space-y-1">
              <Label>Auto-Update Album</Label>
              <p className="text-sm text-gray-600">Automatically add new matching images</p>
            </div>
            <Switch checked={autoUpdate} onCheckedChange={setAutoUpdate} />
          </div>

          {/* Image Count Info */}
          <div className="p-4 bg-gray-50 rounded-lg space-y-1">
            <p className="text-sm text-gray-600">
              Current Images: <strong>{album.image_count}</strong>
            </p>
            <p className="text-xs text-gray-500">
              Created: {new Date(album.created_at * 1000).toLocaleDateString()}
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <Alert variant="destructive">
              <p>{error}</p>
            </Alert>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={loading || !albumName.trim()}>
            {loading ? 'Updating...' : 'Update Album'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};