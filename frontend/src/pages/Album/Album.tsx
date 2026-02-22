import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate } from 'react-router';
import { Button } from '@/components/ui/button';
import {
  Plus,
  RefreshCw,
  ArrowDownUp,
  Grid2x2,
  ChevronDown,
  Check,
} from 'lucide-react';
import { AlbumCard } from '@/components/Albums/AlbumCard';
import { CreateAlbumDialog } from '@/components/Albums/CreateAlbumDialog';
import { EditAlbumDialog } from '@/components/Albums/EditAlbumDialog';
import { AlbumPasswordDialog } from '@/components/Albums/AlbumPasswordDialog';
import { DeleteConfirmDialog } from '@/components/Albums/DeleteConfirmDialog';
import { EmptyAlbumsState } from '@/components/EmptyStates/EmptyAlbumsState';
import { usePictoQuery, usePictoMutation } from '@/hooks/useQueryExtension';
import { getAllAlbums, deleteAlbum } from '@/api/api-functions';
import { setAlbums, removeAlbum } from '@/features/albumsSlice';
import { selectAlbums } from '@/features/albumSelectors';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { Album } from '@/types/Album';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

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
  const [sortBy, setSortBy] = useState<'name' | 'photoCount'>('name');

  const {
    data: albumsData,
    successData,
    isLoading,
    isSuccess,
    isError,
    refetch,
  } = usePictoQuery({
    queryKey: ['albums'],
    queryFn: () => getAllAlbums(),
  });

  const deleteAlbumMutation = usePictoMutation({
    mutationFn: deleteAlbum,
  });

  useMutationFeedback(deleteAlbumMutation, {
    loadingMessage: 'Deleting album...',
    successTitle: 'Success',
    successMessage: 'Album deleted successfully!',
    errorTitle: 'Error',
    errorMessage: 'Failed to delete album. Please try again.',
    onSuccess: () => {
      // Close dialog and clear state after successful deletion
      setIsDeleteDialogOpen(false);
      setAlbumToDelete(null);
    },
  });

  useEffect(() => {
    if (isLoading) {
      dispatch(showLoader('Loading albums...'));
    } else if (isError) {
      dispatch(hideLoader());
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
        created_at: album.created_at || new Date().toISOString(),
        updated_at: album.updated_at || new Date().toISOString(),
      })) as Album[];
      dispatch(setAlbums(albumsList));
      dispatch(hideLoader());
    }
  }, [albumsData, successData, isSuccess, isError, isLoading, dispatch]);

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
    if (albumToDelete) {
      const albumId = albumToDelete.id;
      dispatch(removeAlbum(albumId));
      deleteAlbumMutation.mutate(albumId);
    }
  };

  const handleRefresh = async () => {
    dispatch(showLoader('Refreshing albums...'));
    const result = await refetch();
    dispatch(hideLoader());

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
          <Button variant="outline" size="sm" onClick={handleRefresh}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm">
                <ArrowDownUp className="mr-2 h-4 w-4" />
                Sort by:
                <ChevronDown className="ml-2 h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onSelect={() => setSortBy('name')}>
                <Grid2x2 className="mr-2 h-4 w-4" />
                Name (A-Z){' '}
                {sortBy === 'name' ? <Check className="ml-2 h-4 w-4" /> : ''}
              </DropdownMenuItem>
              <DropdownMenuItem onSelect={() => setSortBy('photoCount')}>
                <Grid2x2 className="mr-2 h-4 w-4" />
                Photo Count{' '}
                {sortBy === 'photoCount' ? (
                  <Check className="ml-2 h-4 w-4" />
                ) : (
                  ''
                )}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          <Button size="sm" onClick={() => setIsCreateDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Create Album
          </Button>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto">
        {albums.length === 0 ? (
          <EmptyAlbumsState />
        ) : (
          <div className="grid grid-cols-1 gap-6 pb-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
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
