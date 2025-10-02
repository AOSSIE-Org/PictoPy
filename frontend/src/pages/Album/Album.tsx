import { AlbumList } from '@/components/Album/AlbumList';
import { CreateAlbumDialog } from '@/components/Album/CreateAlbumDialog';
import { DeleteAlbumDialog } from '@/components/Album/DeleteAlbumDialog';
import { EditAlbumDialog } from '@/components/Album/EditAlbumDialog';
import * as React from 'react';

function Album() {
  const [showCreateDialog, setShowCreateDialog] = React.useState(false);
  const [showEditDialog, setShowEditDialog] = React.useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = React.useState(false);
  const [selectedAlbumId, setSelectedAlbumId] = React.useState<string | null>(
    null,
  );
  const [selectedAlbumName, setSelectedAlbumName] = React.useState<string>('');

  const handleCreateAlbum = () => {
    setShowCreateDialog(true);
  };

  const handleEditAlbum = (albumId: string) => {
    setSelectedAlbumId(albumId);
    setShowEditDialog(true);
  };

  const handleDeleteAlbum = (albumId: string, albumName: string) => {
    setSelectedAlbumId(albumId);
    setSelectedAlbumName(albumName);
    setShowDeleteDialog(true);
  };

  const handleAlbumCreated = (albumId: string) => {
    console.log('Album created:', albumId);
    // Optionally navigate to the new album or refresh the list
  };

  const handleAlbumUpdated = () => {
    console.log('Album updated');
    // List will automatically refresh via Redux store update
  };

  const handleAlbumDeleted = () => {
    console.log('Album deleted');
    // List will automatically refresh via Redux store update
  };

  return (
    <div className="p-6">
      <AlbumList
        onCreateAlbum={handleCreateAlbum}
        onEditAlbum={handleEditAlbum}
        onDeleteAlbum={handleDeleteAlbum}
      />

      <CreateAlbumDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onAlbumCreated={handleAlbumCreated}
      />

      {selectedAlbumId && (
        <>
          <EditAlbumDialog
            open={showEditDialog}
            onOpenChange={setShowEditDialog}
            albumId={selectedAlbumId}
            onAlbumUpdated={handleAlbumUpdated}
          />

          <DeleteAlbumDialog
            open={showDeleteDialog}
            onOpenChange={setShowDeleteDialog}
            albumId={selectedAlbumId}
            albumName={selectedAlbumName}
            onAlbumDeleted={handleAlbumDeleted}
          />
        </>
      )}
    </div>
  );
}

export default Album;
