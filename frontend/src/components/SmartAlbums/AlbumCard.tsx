import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { RefreshCw, Edit, Trash2, Image, Sparkles } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import type { SmartAlbum } from '@/api/api-functions/smart_albums';

interface AlbumCardProps {
  album: SmartAlbum;
  onRefresh: (albumId: string) => void;
  onEdit: (album: SmartAlbum) => void;
  onDelete: (albumId: string) => void;
  onClick: (album: SmartAlbum) => void;
}

export const AlbumCard: React.FC<AlbumCardProps> = ({
  album,
  onRefresh,
  onEdit,
  onDelete,
  onClick,
}) => {
  const handleRefreshClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onRefresh(album.album_id);
  };

  const handleEditClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onEdit(album);
  };

  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete(album.album_id);
  };

  const formatDate = (timestamp: number) => {
    return formatDistanceToNow(new Date(timestamp * 1000), { addSuffix: true });
  };

  return (
    <Card
      className="h-full flex flex-col cursor-pointer transition-all duration-200 hover:-translate-y-1 hover:shadow-lg"
      onClick={() => onClick(album)}
    >
      {/* Album Thumbnail */}
      <div className="relative h-48 bg-gray-200 flex items-center justify-center">
        {album.thumb_image_id ? (
          <img
            src={`/api/images/${album.thumb_image_id}/thumbnail`}
            alt={album.album_name}
            className="w-full h-full object-cover"
          />
        ) : (
          <Image className="w-20 h-20 text-gray-400" />
        )}

        {/* Image Count Badge */}
        <div className="absolute top-2 right-2 bg-black/60 text-white px-2 py-1 rounded text-sm font-bold">
          {album.image_count} photos
        </div>
      </div>

      {/* Album Content */}
      <CardContent className="grow p-4">
        {/* Album Name */}
        <h3 className="text-lg font-semibold mb-2 truncate">{album.album_name}</h3>

        {/* Tags */}
        <div className="flex gap-1 mb-2 flex-wrap">
          <Badge
            variant={album.album_type === 'object' ? 'default' : 'secondary'}
            className="capitalize"
          >
            {album.album_type}
          </Badge>
          {album.auto_update && (
            <Badge variant="outline" className="gap-1">
              <Sparkles className="w-3 h-3" />
              Auto-Update
            </Badge>
          )}
        </div>

        {/* Classes/Criteria */}
        {album.criteria.class_names && album.criteria.class_names.length > 0 && (
          <p className="text-sm text-gray-600 truncate">
            {album.criteria.class_names.join(', ')}
          </p>
        )}

        {/* Created Date */}
        <p className="text-xs text-gray-500 mt-2">Created {formatDate(album.created_at)}</p>
      </CardContent>

      {/* Action Buttons */}
      <TooltipProvider>
        <div className="flex justify-between px-4 pb-4">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRefreshClick}
                className="h-8 w-8 p-0"
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Refresh album</p>
            </TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="sm" onClick={handleEditClick} className="h-8 w-8 p-0">
                <Edit className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Edit album</p>
            </TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDeleteClick}
                className="h-8 w-8 p-0 text-red-600 hover:text-red-700"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Delete album</p>
            </TooltipContent>
          </Tooltip>
        </div>
      </TooltipProvider>
    </Card>
  );
};