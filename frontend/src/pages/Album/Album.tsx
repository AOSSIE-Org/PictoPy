import * as React from 'react';
import { AlbumList } from '@/components/Album/AlbumList';
import { CreateAlbumDialog } from '@/components/Album/CreateAlbumDialog';


function Album() {
  const [showCreateDialog, setShowCreateDialog] = React.useState(false);
  const [showEditDialog, setShowEditDialog] = React.useState(false);
  const [selectedAlbumId, setSelectedAlbumId] = React.useState<string | null>(null);

  const handleCreateAlbum = () => {
    setShowCreateDialog(true);
  };

  const handleEditAlbum = (albumId: string) => {
    setSelectedAlbumId(albumId);
    setShowEditDialog(true);
  };

  const handleDeleteAlbum = (albumId: string) => {
    // TODO: Implement delete confirmation dialog
    console.log('Delete album:', albumId);
  };

  const handleAlbumCreated = (albumId: string) => {
    console.log('Album created:', albumId);
    // Optionally navigate to the new album or refresh the list
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

      {/* TODO: Add EditAlbumDialog */}
      {showEditDialog && selectedAlbumId && (
        <div>Edit Album Dialog Placeholder</div>
      )}
    </div>
  );
}

export default Album;
