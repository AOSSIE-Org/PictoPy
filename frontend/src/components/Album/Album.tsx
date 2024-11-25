import React, { useState } from 'react';
import { useAllAlbums, useDeleteAlbum } from '../../hooks/AlbumService';
import AlbumList from './AlbumList';
import { Button } from '@/components/ui/button';
import CreateAlbumForm from './AlbumForm';
import EditAlbumDialog from './AlbumDialog';
import ErrorDialog from './Error';
import AlbumView from './Albumview';
import { Album } from '@/types/Album';

const AlbumsView: React.FC = () => {
  const { albums, isLoading, refetch } = useAllAlbums();
  const { deleteAlbum } = useDeleteAlbum();
  const [isCreateFormOpen, setIsCreateFormOpen] = useState(false);
  const [editingAlbum, setEditingAlbum] = useState<Album | null>(null);
  const [currentAlbum, setCurrentAlbum] = useState<string | null>(null);
  const [errorDialogContent, setErrorDialogContent] = useState<{
    title: string;
    description: string;
  } | null>(null);

  if (isLoading) return <div>Loading albums...</div>;

  const showErrorDialog = (title: string, err: unknown) => {
    setErrorDialogContent({
      title,
      description:
        err instanceof Error ? err.message : 'An unknown error occurred',
    });
  };

  const transformedAlbums = albums.map((album: Album) => ({
    id: album.album_name,
    title: album.album_name,
    coverImage: album.image_paths[0] || `D:/Data/Pictopy/PictoPy/frontend/public/tauri.svg`,
    imageCount: album.image_paths.length,
  }));

  const handleAlbumClick = (albumId: string) => {
    setCurrentAlbum(albumId);
  };

  const handleDeleteAlbum = async (albumId: string) => {
    try {
      await deleteAlbum(albumId);
      refetch();
    } catch (err) {
      showErrorDialog('Error Deleting Album', err);
    }
  };
  if (albums.length === 0) {
    return (
      <div className="container mx-auto p-4">
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold">Albums</h1>
          <Button onClick={() => setIsCreateFormOpen(true)} variant="outline">
            Create New Album
          </Button>
        </div>
        <div className="text-center">No albums found.</div>
        <CreateAlbumForm
          isOpen={isCreateFormOpen}
          onClose={() => setIsCreateFormOpen(false)}
          onSuccess={() => {
            setIsCreateFormOpen(false);
            refetch();
          }}
          onError={showErrorDialog}
        />
        <ErrorDialog
          content={errorDialogContent}
          onClose={() => setErrorDialogContent(null)}
        />
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      {currentAlbum ? (
        <AlbumView
          albumName={currentAlbum}
          onBack={() => setCurrentAlbum(null)}
          onError={showErrorDialog}
        />
      ) : (
        <>
          <div className="mb-4 flex items-center justify-between">
            <h1 className="text-2xl font-bold">Albums</h1>
            <Button onClick={() => setIsCreateFormOpen(true)} variant="outline">
              Create New Album
            </Button>
          </div>
          <AlbumList
            albums={transformedAlbums}
            albumsPerRow={3}
            onAlbumClick={handleAlbumClick}
            onEditAlbum={(albumId) => {
              const album = albums.find((a) => a.album_name === albumId);
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
          refetch();
        }}
        onError={showErrorDialog}
      />

      <EditAlbumDialog
        album={editingAlbum}
        onClose={() => setEditingAlbum(null)}
        onSuccess={() => {
          setEditingAlbum(null);
          refetch();
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
