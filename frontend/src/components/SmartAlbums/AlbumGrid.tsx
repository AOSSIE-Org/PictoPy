import React from 'react';
import { AlbumCard } from './AlbumCard';
import { Image } from 'lucide-react';
import type { SmartAlbum } from '@/api/api-functions/smart_albums';

interface AlbumGridProps {
  albums: SmartAlbum[];
  onRefresh: (albumId: string) => void;
  onEdit: (album: SmartAlbum) => void;
  onDelete: (albumId: string) => void;
  onAlbumClick: (album: SmartAlbum) => void;
}

export const AlbumGrid: React.FC<AlbumGridProps> = ({
  albums,
  onRefresh,
  onEdit,
  onDelete,
  onAlbumClick,
}) => {
  if (albums.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-gray-500">
        <Image className="w-20 h-20 mb-4 text-gray-300" />
        <h3 className="text-xl font-semibold mb-2">No Smart Albums Yet</h3>
        <p className="text-sm">Create your first smart album to organize your photos automatically</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
      {albums.map((album) => (
        <AlbumCard
          key={album.album_id}
          album={album}
          onRefresh={onRefresh}
          onEdit={onEdit}
          onDelete={onDelete}
          onClick={onAlbumClick}
        />
      ))}
    </div>
  );
};