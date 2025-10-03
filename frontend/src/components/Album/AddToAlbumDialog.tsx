import { addImagesToAlbum, fetchAllAlbums } from '@/api/api-functions/albums';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
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
import { ScrollArea } from '@/components/ui/scroll-area';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { usePictoMutation, usePictoQuery } from '@/hooks/useQueryExtension';
import { Eye, EyeOff, Lock, Search } from 'lucide-react';
import { ChangeEvent, useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';

interface AddToAlbumDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  selectedImageIds: string[];
  onImagesAdded?: () => void;
}

export function AddToAlbumDialog({
  open,
  onOpenChange,
  selectedImageIds,
  onImagesAdded,
}: AddToAlbumDialogProps) {
  const dispatch = useDispatch();
  const [localAlbums, setLocalAlbums] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAlbumId, setSelectedAlbumId] = useState<string | null>(null);
  const [showHidden, setShowHidden] = useState(false);

  // Fetch albums
  const {
    data: albumsData,
    isLoading,
    isSuccess,
  } = usePictoQuery({
    queryKey: ['albums', showHidden],
    queryFn: () => fetchAllAlbums(showHidden),
    enabled: open,
  });

  // Add images to album mutation
  const addToAlbumMutation = usePictoMutation({
    mutationFn: ({
      albumId,
      imageIds,
    }: {
      albumId: string;
      imageIds: string[];
    }) => addImagesToAlbum(albumId, imageIds),
    onSuccess: (data: any) => {
      if (data.success) {
        // Resolve album name before any state mutations
        const selectedAlbum = localAlbums.find(
          (album: any) => album.album_id === selectedAlbumId,
        );
        const albumName = selectedAlbum?.album_name ?? 'selected album';

        dispatch(
          showInfoDialog({
            title: 'Success',
            message: `Added ${selectedImageIds.length} photo${
              selectedImageIds.length > 1 ? 's' : ''
            } to "${albumName}"`,
            variant: 'info',
          }),
        );

        onImagesAdded?.();
        handleClose();
      }
    },
    onError: () => {
      dispatch(
        showInfoDialog({
          title: 'Error',
          message: 'Failed to add photos to album. Please try again.',
          variant: 'error',
        }),
      );
    },
  });

  // Use mutation feedback
  useMutationFeedback(addToAlbumMutation, {
    loadingMessage: 'Adding photos to album...',
    showSuccess: false, // We handle success manually
    showError: false, // We handle errors manually
    errorTitle: 'Failed to Add Photos',
  });

  // Update local state when albums are fetched
  useEffect(() => {
    if (isSuccess && albumsData?.success) {
      setLocalAlbums(albumsData.albums);
    }
  }, [isSuccess, albumsData]);

  // Filter albums based on search term
  const filteredAlbums = localAlbums.filter(
    (album: any) =>
      album.album_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      album.description.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  const handleClose = () => {
    setSelectedAlbumId(null);
    setSearchTerm('');
    onOpenChange(false);
  };

  const handleAddToAlbum = () => {
    if (!selectedAlbumId) return;

    addToAlbumMutation.mutate({
      albumId: selectedAlbumId,
      imageIds: selectedImageIds,
    });
  };

  const handleToggleShowHidden = () => {
    setShowHidden(!showHidden);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] w-[95vw] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Add to Album</DialogTitle>
          <DialogDescription>
            Add {selectedImageIds.length} selected photo
            {selectedImageIds.length > 1 ? 's' : ''} to an existing album.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Search and filters */}
          <div className="space-y-2">
            <div className="relative">
              <Search className="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
              <Input
                placeholder="Search albums..."
                value={searchTerm}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setSearchTerm(e.target.value)
                }
                className="pl-9"
              />
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleToggleShowHidden}
                className="gap-2"
              >
                {showHidden ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
                {showHidden ? 'Hide Hidden Albums' : 'Show Hidden Albums'}
              </Button>
            </div>
          </div>

          {/* Albums list */}
          <div className="space-y-2">
            <Label>Select Album</Label>
            <ScrollArea className="h-60">
              <div className="space-y-2 pr-4">
                {isLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <p className="text-muted-foreground">Loading albums...</p>
                  </div>
                ) : filteredAlbums.length === 0 ? (
                  <div className="flex items-center justify-center py-8">
                    <p className="text-muted-foreground">
                      {searchTerm
                        ? 'No albums found matching your search.'
                        : 'No albums available.'}
                    </p>
                  </div>
                ) : (
                  filteredAlbums.map((album: any) => (
                    <Card
                      key={album.album_id}
                      className={`hover:bg-muted/50 cursor-pointer transition-colors ${
                        selectedAlbumId === album.album_id
                          ? 'bg-primary/10 ring-primary ring-2'
                          : ''
                      }`}
                      onClick={() => setSelectedAlbumId(album.album_id)}
                    >
                      <CardContent className="p-3">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <h3 className="font-medium">
                                {album.album_name}
                              </h3>
                              {album.is_hidden && (
                                <Lock className="text-muted-foreground h-4 w-4" />
                              )}
                            </div>
                            {album.description && (
                              <p className="text-muted-foreground mt-1 text-sm">
                                {album.description}
                              </p>
                            )}
                          </div>
                          {album.is_hidden && (
                            <Badge variant="secondary" className="ml-2">
                              Hidden
                            </Badge>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </ScrollArea>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            onClick={handleAddToAlbum}
            disabled={!selectedAlbumId || addToAlbumMutation.isPending}
          >
            Add to Album
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
