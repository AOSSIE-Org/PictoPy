import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { getAlbums, addImagesToAlbum, Album } from '@/api/api-functions';

interface AddToAlbumDialogProps {
  isOpen: boolean;
  onClose: () => void;
  imageIds: string[];
}

export function AddToAlbumDialog({
  isOpen,
  onClose,
  imageIds,
}: AddToAlbumDialogProps) {
  const [albums, setAlbums] = useState<Album[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchAlbums();
    }
  }, [isOpen]);

  const fetchAlbums = async () => {
    try {
      const response = await getAlbums();
      if (response.success) {
        setAlbums(response.albums);
      }
    } catch (error) {
      console.error('Failed to fetch albums:', error);
    }
  };

  const handleAddToAlbum = async (albumId: string) => {
    try {
      setLoading(true);
      await addImagesToAlbum(albumId, imageIds);
      // alert('Images added to album successfully!');
      onClose();
    } catch (error) {
      console.error('Failed to add images to album:', error);
      alert('Failed to add images to album');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Add to Album</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          {albums.length === 0 ? (
            <p className="text-muted-foreground text-center">
              No albums found.
            </p>
          ) : (
            <div className="grid gap-2">
              {albums.map((album) => (
                <Button
                  key={album.album_id}
                  variant="outline"
                  className="justify-start text-left"
                  onClick={() => handleAddToAlbum(album.album_id)}
                  disabled={loading}
                >
                  <div className="flex flex-col items-start gap-1">
                    <span className="font-semibold">{album.album_name}</span>
                    {album.description && (
                      <span className="text-muted-foreground text-xs">
                        {album.description}
                      </span>
                    )}
                  </div>
                </Button>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
