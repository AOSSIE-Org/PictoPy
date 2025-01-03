import React from 'react';

import { AlbumListProps } from '@/types/Album';
import AlbumCard from './AlbumCard';

const AlbumList: React.FC<AlbumListProps> = ({
  albums,
  onAlbumClick,
  onEditAlbum,
  onDeleteAlbum,
}) => {
  return (
    <div
      className="grid grid-cols-[repeat(auto-fill,_minmax(272px,_1fr))] gap-4"
    >
      {albums.map((album) => (
        <AlbumCard
          key={album.id}
          album={album}
          onClick={() => onAlbumClick(album.id)}
          onEdit={() => onEditAlbum(album.id)}
          onDelete={() => onDeleteAlbum(album.id)}
        />
      ))}
    </div>
  );
};

export default AlbumList;
