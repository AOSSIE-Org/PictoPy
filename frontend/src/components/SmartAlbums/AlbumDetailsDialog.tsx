import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { X, RefreshCw, Sparkles } from 'lucide-react';
import { AlbumImageGrid } from './AlbumImageGrid';
import type { SmartAlbum } from '@/api/api-functions/smart_albums';

interface AlbumDetailsDialogProps {
  open: boolean;
  album: SmartAlbum | null;
  onClose: () => void;
  onRefresh?: (albumId: string) => void;
  onToggleFavorite?: (imageId: string, isFavorite: boolean) => void;
}

export const AlbumDetailsDialog: React.FC<AlbumDetailsDialogProps> = ({
  open,
  album,
  onClose,
  onRefresh,
  onToggleFavorite,
}) => {
  if (!album) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-7xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex justify-between items-start gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <DialogTitle className="text-2xl">{album.album_name}</DialogTitle>
                <Badge
                  variant={album.album_type === 'object' ? 'default' : 'secondary'}
                  className="capitalize"
                >
                  {album.album_type}
                </Badge>
                {album.auto_update && (
                  <Badge variant="outline" className="gap-1">
                    <Sparkles className="w-3 h-3" />
                    Auto-Update
                  </Badge>
                )}
              </div>
              <p className="text-sm text-gray-600">{album.image_count} images</p>
            </div>

            <div className="flex items-center gap-2">
              {onRefresh && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onRefresh(album.album_id)}
                  title="Refresh album"
                >
                  <RefreshCw className="h-4 w-4" />
                </Button>
              )}
              <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0">
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </DialogHeader>

        <div className="mt-6">
          <AlbumImageGrid albumId={album.album_id} onToggleFavorite={onToggleFavorite} />
        </div>
      </DialogContent>
    </Dialog>
  );
};