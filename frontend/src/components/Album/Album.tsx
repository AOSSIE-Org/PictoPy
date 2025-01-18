import React, { useState } from 'react';
import AlbumList from './AlbumList';
import { Button } from '@/components/ui/button';
import CreateAlbumForm from './AlbumForm';
import EditAlbumDialog from './AlbumDialog';
import ErrorDialog from './Error';
import AlbumView from './Albumview';
import { Album } from '@/types/Album';
import { SquarePlus } from 'lucide-react';
import { LoadingScreen } from '@/components/ui/LoadingScreen/LoadingScreen';
import { usePictoMutation, usePictoQuery } from '@/hooks/useQueryExtensio';
import {
  deleteAlbums,
  fetchAllAlbums,
} from '../../../api/api-functions/albums';

const AlbumsView: React.FC = () => {
  const {
    successData: albums,
    isLoading,
  } = usePictoQuery({
    queryFn: fetchAllAlbums,
    queryKey: ['all-albums'],
  });

  const { mutate: deleteAlbum } = usePictoMutation({
    mutationFn: deleteAlbums,
    autoInvalidateTags: ['all-albums'],
  });

  const [isCreateFormOpen, setIsCreateFormOpen] = useState(false);
  const [editingAlbum, setEditingAlbum] = useState<Album | null>(null);
  const [currentAlbum, setCurrentAlbum] = useState<string | null>(null);
  const [errorDialogContent, setErrorDialogContent] = useState<{
    title: string;
    description: string;
  } | null>(null);

  if (isLoading) {
    return <LoadingScreen />;
  }
  const showErrorDialog = (title: string, err: unknown) => {
    setErrorDialogContent({
      title,
      description:
        err instanceof Error ? err.message : 'An unknown error occurred',
    });
  };

  if (!albums || albums.length === 0) {
    return (
      <div className="container mx-auto pb-4">
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold">Albums</h1>
          <Button
            onClick={() => setIsCreateFormOpen(true)}
            variant="outline"
            className="border-gray-500 dark:hover:bg-white/10"
          >
            Create New Album
          </Button>
        </div>
        <div className="text-center">No albums found.</div>
        <CreateAlbumForm
          isOpen={isCreateFormOpen}
          onClose={() => setIsCreateFormOpen(false)}
          onSuccess={() => {
            setIsCreateFormOpen(false);
          }}
          onError={(err) => showErrorDialog('Error', err)}
        />
        <ErrorDialog
          content={errorDialogContent}
          onClose={() => setErrorDialogContent(null)}
        />
      </div>
    );
  }
  //these funcion works when there are albums
  const transformedAlbums = albums.map((album: Album) => ({
    id: album.album_name,
    title: album.album_name,
    coverImage: album.image_paths[0] || '',
    imageCount: album.image_paths.length,
  }));

  const handleAlbumClick = (albumId: string) => {
    setCurrentAlbum(albumId);
  };

  const handleDeleteAlbum = async (albumId: string) => {
    try {
      await deleteAlbum({ name: albumId });
    } catch (err) {
      showErrorDialog('Error Deleting Album', err);
    }
  };

  return (
    <div className="mx-auto w-full px-2 pb-4">
      {currentAlbum ? (
        <AlbumView
          albumName={currentAlbum}
          onBack={() => {
            setCurrentAlbum(null);
          }}
          onError={showErrorDialog}
        />
      ) : (
        <>
          <div className="mb-4 flex items-center justify-between">
            <h1 className="text-2xl font-bold">Albums</h1>
            <Button
              onClick={() => setIsCreateFormOpen(true)}
              variant="outline"
              className="flex items-center border-gray-500 dark:hover:bg-white/10"
            >
              <SquarePlus className="h-[18px] w-[18px]" />
              <p className="mb-[1px] ml-1">Create New Album</p>
            </Button>
          </div>
          <AlbumList
            albums={transformedAlbums}
            albumsPerRow={3}
            onAlbumClick={handleAlbumClick}
            onEditAlbum={(albumId) => {
              const album = albums.find((a: any) => a.album_name === albumId);
              if (album) {
                setEditingAlbum(album);
              }
            }}
            onDeleteAlbum={handleDeleteAlbum}
          />
        </>
      )}

      <CreateAlbumForm
        isOpen={isCreateFormOpen}
        onClose={() => setIsCreateFormOpen(false)}
        onSuccess={() => {
          setIsCreateFormOpen(false);
        }}
        onError={(err) => showErrorDialog('Error', err)}
      />

      <EditAlbumDialog
        album={editingAlbum}
        onClose={() => setEditingAlbum(null)}
        onSuccess={() => {
          setEditingAlbum(null);
        }}
        onError={showErrorDialog}
      />

      <ErrorDialog
        content={errorDialogContent}
        onClose={() => setErrorDialogContent(null)}
      />
    </div>
  );
};

export default AlbumsView;
