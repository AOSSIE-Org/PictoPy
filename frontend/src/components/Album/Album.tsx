import React, { useState } from 'react';
import { useAllAlbums, useDeleteAlbum } from '../../hooks/AlbumService';
import AlbumList from './AlbumList';
import { Button } from '@/components/ui/button';
import CreateAlbumForm from './AlbumForm';
import EditAlbumDialog from './AlbumDialog';
import ErrorDialog from './Error';
import AlbumView from './Albumview';
import { Album } from '@/types/Album';
import { SquarePlus } from 'lucide-react';
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

  if (isLoading)
    return (
      <div className="container flex w-full items-center justify-center">
        <div>
          <svg
            aria-hidden="true"
            className="h-8 w-8 animate-spin fill-primary text-gray-200 dark:text-gray-600"
            viewBox="0 0 100 101"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z"
              fill="currentColor"
            />
            <path
              d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z"
              fill="currentFill"
            />
          </svg>
        </div>
      </div>
    );

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
    coverImage: album.image_paths[0] || ``,
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
    <div className="mx-auto w-full px-2 pb-4">
      {currentAlbum ? (
        <AlbumView
          albumName={currentAlbum}
          onBack={() => {
            setCurrentAlbum(null);
            refetch();
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
