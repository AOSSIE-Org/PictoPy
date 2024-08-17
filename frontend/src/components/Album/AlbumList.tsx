import React from "react";

import { AlbumListProps } from "@/types/Album";
import AlbumCard from "./AlbumCard";

const AlbumList: React.FC<AlbumListProps> = ({
  albums,
  albumsPerRow,
  onAlbumClick,
  onEditAlbum,
  onDeleteAlbum,
}) => {
  return (
    <div
      className={`grid gap-4 md:gap-6 ${
        albumsPerRow === 2
          ? "grid-cols-1 sm:grid-cols-2"
          : albumsPerRow === 3
          ? "grid-cols-1 sm:grid-cols-2 md:grid-cols-3"
          : "grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
      }`}
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
