import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router';
import { Button } from '@/components/ui/button';
import { Plus, RefreshCw, ArrowDownAZ, Images } from 'lucide-react';
import { AlbumCard } from '@/components/Albums/AlbumCard';
import { CreateAlbumDialog } from '@/components/Albums/CreateAlbumDialog';
import { EditAlbumDialog } from '@/components/Albums/EditAlbumDialog';
import { AlbumPasswordDialog } from '@/components/Albums/AlbumPasswordDialog';
import { DeleteConfirmDialog } from '@/components/Albums/DeleteConfirmDialog';
import { EmptyAlbumsState } from '@/components/EmptyStates/EmptyAlbumsState';
import { usePictoQuery, usePictoMutation } from '@/hooks/useQueryExtension';
import { getAllAlbums, deleteAlbum } from '@/api/api-functions';
import { setAlbums } from '@/features/albumsSlice';
import { selectAlbums } from '@/features/albumSelectors';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { Album } from '@/types/Album';
import {
  GallerySortDropdown,
  type SortOption,
} from '@/components/GallerySortDropdown';

type AlbumSortValue = 'name' | 'photoCount';

const ALBUM_SORT_OPTIONS: SortOption<AlbumSortValue>[] = [
  { value: 'name', label: 'Name (A-Z)', icon: ArrowDownAZ },
  { value: 'photoCount', label: 'Photo Count', icon: Images },
];

// Mirrors an AlbumCard: the same 4/5 cover as a memory tile, plus the name and
// count bars, so the grid does not jump when the real cards arrive.
const AlbumCardSkeleton: React.FC = () => (
  <div className="animate-pulse" data-testid="album-card-skeleton">
    <div className="bg-muted aspect-4/5 w-full rounded-xl" />
    <div className="space-y-2 p-4">
      <div className="bg-muted h-4 w-2/3 rounded" />
      <div className="bg-muted h-3 w-1/3 rounded" />
    </div>
  </div>
);

function Albums() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const albums = useSelector(selectAlbums);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [selectedAlbum, setSelectedAlbum] = useState<Album | null>(null);
  const [albumToAccess, setAlbumToAccess] = useState<Album | null>(null);
  const [isPasswordDialogOpen, setIsPasswordDialogOpen] = useState(false);
  const [albumToDelete, setAlbumToDelete] = useState<Album | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [sortBy, setSortBy] = useState<AlbumSortValue>('name');

  const {
    data: albumsData,
    successData,
    isLoading,
    isFetching,
    isSuccess,
    isError,
    refetch,
  } = usePictoQuery({
    queryKey: ['albums'],
    queryFn: () => getAllAlbums(),
  });

  const deleteAlbumMutation = usePictoMutation({
    mutationFn: deleteAlbum,
    autoInvalidateTags: ['albums'],
  });

  useMutationFeedback(deleteAlbumMutation, {
    loadingMessage: 'Deleting album...',
    successTitle: 'Success',
    successMessage: 'Album deleted successfully!',
    errorTitle: 'Error',
    errorMessage: 'Failed to delete album. Please try again.',
  });

  useEffect(() => {
    if (isError) {
      dispatch(
        showInfoDialog({
          title: 'Error',
          message: 'Failed to load albums. Please try again later.',
          variant: 'error',
        }),
      );
    } else if (isSuccess && albumsData) {
      const responseData = albumsData as any;
      const backendAlbums = (responseData?.albums || []) as any[];
      const albumsList = backendAlbums.map((album: any) => ({
        id: album.album_id,
        name: album.album_name,
        description: album.description || '',
        is_locked: Boolean(album.is_locked),
        cover_image_path: album.cover_image_path,
        image_count: album.image_count || 0,
      })) as Album[];
      dispatch(setAlbums(albumsList));
    }
  }, [albumsData, successData, isSuccess, isError, dispatch]);

  const handleAlbumClick = (album: Album) => {
    if (album.is_locked) {
      setAlbumToAccess(album);
      setIsPasswordDialogOpen(true);
    } else {
      navigate(`/albums/${album.id}`);
    }
  };

  const handlePasswordSubmit = (password: string) => {
    if (albumToAccess) {
      navigate(`/albums/${albumToAccess.id}`, { state: { password } });
    }
  };

  const handleEditAlbum = (album: Album) => {
    setSelectedAlbum(album);
    setIsEditDialogOpen(true);
  };

  const handleDeleteAlbum = (album: Album) => {
    setAlbumToDelete(album);
    setIsDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    if (!albumToDelete) return;
    const albumId = albumToDelete.id;
    // Close on confirm rather than on success: a failed delete would otherwise
    // leave this dialog stacked underneath the error dialog.
    setIsDeleteDialogOpen(false);
    setAlbumToDelete(null);
    deleteAlbumMutation.mutate(albumId);
  };

  const handleRefresh = async () => {
    const result = await refetch();

    if (result.isError || result.error) {
      dispatch(
        showInfoDialog({
          title: 'Error',
          message: 'Failed to refresh albums. Please try again.',
          variant: 'error',
        }),
      );
    }
  };

  const sortedAlbums = [...albums].sort((a, b) => {
    if (sortBy === 'name') {
      return a.name.localeCompare(b.name);
    } else if (sortBy === 'photoCount') {
      return b.image_count - a.image_count;
    }
    return 0;
  });

  return (
    <div className="flex h-full flex-col">
      <div className="mt-1 mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Albums</h1>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={isFetching}
          >
            <RefreshCw
              className={`mr-2 h-4 w-4 ${isFetching ? 'animate-spin' : ''}`}
            />
            {isFetching ? 'Refreshing…' : 'Refresh'}
          </Button>
          <GallerySortDropdown
            value={sortBy}
            onValueChange={setSortBy}
            options={ALBUM_SORT_OPTIONS}
          />
          <Button size="sm" onClick={() => setIsCreateDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Create Album
          </Button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="grid grid-cols-2 gap-4 pb-6 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {Array.from({ length: 10 }).map((_, index) => (
              <AlbumCardSkeleton key={index} />
            ))}
          </div>
        ) : albums.length === 0 ? (
          <EmptyAlbumsState />
        ) : (
          <div className="grid grid-cols-2 gap-4 pb-6 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {sortedAlbums.map((album) => (
              <AlbumCard
                key={album.id}
                album={album}
                onClick={() => handleAlbumClick(album)}
                onEdit={() => handleEditAlbum(album)}
                onDelete={() => handleDeleteAlbum(album)}
              />
            ))}
          </div>
        )}
      </div>
      {/* Dialogs */}
      <CreateAlbumDialog
        isOpen={isCreateDialogOpen}
        onClose={() => setIsCreateDialogOpen(false)}
        onSuccess={refetch}
      />
      <EditAlbumDialog
        album={selectedAlbum}
        isOpen={isEditDialogOpen}
        onClose={() => {
          setIsEditDialogOpen(false);
          setSelectedAlbum(null);
        }}
        onSuccess={refetch}
      />
      <AlbumPasswordDialog
        isOpen={isPasswordDialogOpen}
        onClose={() => {
          setIsPasswordDialogOpen(false);
          setAlbumToAccess(null);
        }}
        onSubmit={handlePasswordSubmit}
        albumName={albumToAccess?.name || ''}
      />
      <DeleteConfirmDialog
        isOpen={isDeleteDialogOpen}
        onClose={() => {
          setIsDeleteDialogOpen(false);
          setAlbumToDelete(null);
        }}
        onConfirm={confirmDelete}
        albumName={albumToDelete?.name || ''}
      />
    </div>
  );
}

export default Albums;
