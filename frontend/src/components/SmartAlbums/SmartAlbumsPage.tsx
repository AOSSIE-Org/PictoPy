import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Plus, RefreshCw, Sparkles } from 'lucide-react';
import { useSmartAlbums } from '@/hooks/useSmartAlbum';
import { AlbumGrid } from './AlbumGrid';
import { AlbumStatistics } from './AlbumStatistics';
import { CreateAlbumDialog } from './CreateAlbumDialog';
import { AlbumDetailsDialog } from './AlbumDetailsDialog';
import { EditAlbumDialog } from './EditAlbumDialog';
import type { SmartAlbum } from '@/api/api-functions/smart_albums';
import { Alert } from '@/components/ui/alert';
import { LoadingScreen } from '@/components/ui/LoadingScreen/LoadingScreen';
import { useToast } from '@/hooks/useToast';
import { ToastContainer } from '@/components/ToastContainer';

export const SmartAlbumsPage: React.FC = () => {
  const {
    albums,
    statistics,
    loading,
    error,
    fetchAlbums,
    createObjectAlbum,
    createPredefinedAlbums,
    refreshAlbum,
    refreshAllAlbums,
    updateAlbum,
    deleteAlbum,
    loadStatistics,
  } = useSmartAlbums();

  const { toasts, success, error: showError, dismissToast } = useToast();

  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [detailsDialogOpen, setDetailsDialogOpen] = useState(false);
  const [selectedAlbum, setSelectedAlbum] = useState<SmartAlbum | null>(null);
  const [albumToEdit, setAlbumToEdit] = useState<SmartAlbum | null>(null);
  const [activeTab, setActiveTab] = useState<'all' | 'object' | 'face'>('all');

  useEffect(() => {
    fetchAlbums();
    loadStatistics();
  }, [fetchAlbums, loadStatistics]);

  const filteredAlbums = React.useMemo(() => {
    if (activeTab === 'all') return albums;
    return albums.filter((a) => a.album_type === activeTab);
  }, [albums, activeTab]);

  const handleCreateAlbum = async (name: string, classes: string[], autoUpdate: boolean) => {
    try {
      await createObjectAlbum({
        album_name: name,
        object_classes: classes,
        auto_update: autoUpdate,
      });
      success(`Album "${name}" created successfully!`);
    } catch (err) {
      showError('Failed to create album');
      throw err;
    }
  };

  const handleCreatePredefined = async () => {
    try {
      const result = await createPredefinedAlbums();
      success(`Created ${result.created_count} predefined albums!`);
    } catch (err) {
      showError('Failed to create predefined albums');
    }
  };

  const handleRefreshAlbum = async (albumId: string) => {
    try {
      const result = await refreshAlbum(albumId);
      success(`Added ${result.updated_image_count} images`);
    } catch (err) {
      showError('Failed to refresh album');
    }
  };

  const handleRefreshAll = async () => {
    try {
      const result = await refreshAllAlbums();
      success(`Refreshed ${result.album_count} albums`);
    } catch (err) {
      showError('Failed to refresh albums');
    }
  };

  const handleUpdateAlbum = async (albumId: string, name: string, autoUpdate: boolean) => {
    try {
      await updateAlbum(albumId, { album_name: name, auto_update: autoUpdate });
      success('Album updated successfully!');
    } catch (err) {
      showError('Failed to update album');
      throw err;
    }
  };

  const handleDeleteAlbum = async (albumId: string) => {
    if (!window.confirm('Are you sure you want to delete this album?')) {
      return;
    }

    try {
      await deleteAlbum(albumId);
      success('Album deleted successfully');
    } catch (err) {
      showError('Failed to delete album');
    }
  };

  const handleAlbumClick = (album: SmartAlbum) => {
    setSelectedAlbum(album);
    setDetailsDialogOpen(true);
  };

  const handleEditAlbum = (album: SmartAlbum) => {
    setAlbumToEdit(album);
    setEditDialogOpen(true);
  };

  if (loading && albums.length === 0) {
    return <LoadingScreen />;
  }

  return (
    <>
      {/* Toast Container */}
      <ToastContainer toasts={toasts} onDismiss={dismissToast} />

      <div className="container mx-auto py-8 px-4 max-w-7xl">
        {/* Header */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-3xl font-bold">Smart Albums</h1>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={handleRefreshAll} disabled={loading}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh All
              </Button>
              <Button variant="outline" onClick={handleCreatePredefined} disabled={loading}>
                <Sparkles className="w-4 h-4 mr-2" />
                Create Predefined
              </Button>
              <Button onClick={() => setCreateDialogOpen(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Create Album
              </Button>
            </div>
          </div>

          {/* Statistics */}
          <AlbumStatistics statistics={statistics} />

          {/* Tabs */}
          <div className="flex gap-2 border-b">
            <button
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === 'all'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              onClick={() => setActiveTab('all')}
            >
              All Albums ({albums.length})
            </button>
            <button
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === 'object'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              onClick={() => setActiveTab('object')}
            >
              Object Albums ({albums.filter((a) => a.album_type === 'object').length})
            </button>
            <button
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === 'face'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
              onClick={() => setActiveTab('face')}
            >
              Face Albums ({albums.filter((a) => a.album_type === 'face').length})
            </button>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            {error}
          </Alert>
        )}

        {/* Albums Grid */}
        <AlbumGrid
          albums={filteredAlbums}
          onRefresh={handleRefreshAlbum}
          onEdit={handleEditAlbum}
          onDelete={handleDeleteAlbum}
          onAlbumClick={handleAlbumClick}
        />

        {/* Dialogs */}
        <CreateAlbumDialog
          open={createDialogOpen}
          onClose={() => setCreateDialogOpen(false)}
          onCreate={handleCreateAlbum}
        />

        <EditAlbumDialog
          open={editDialogOpen}
          album={albumToEdit}
          onClose={() => {
            setEditDialogOpen(false);
            setAlbumToEdit(null);
          }}
          onUpdate={handleUpdateAlbum}
        />

        <AlbumDetailsDialog
          open={detailsDialogOpen}
          album={selectedAlbum}
          onClose={() => {
            setDetailsDialogOpen(false);
            setSelectedAlbum(null);
          }}
          onRefresh={handleRefreshAlbum}
          onToggleFavorite={(imageId, isFavorite) => {
            console.log('Toggle favorite:', imageId, isFavorite);
          }}
        />
      </div>
    </>
  );
};