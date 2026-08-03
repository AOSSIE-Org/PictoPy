import React from 'react';
import { MoreVertical, Lock, Pencil, Trash2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { AlbumCardProps } from '@/types/Album';
import { useTheme } from '@/contexts/ThemeContext';
import { convertFileSrc } from '@tauri-apps/api/core';

export const AlbumCard: React.FC<AlbumCardProps> = ({
  album,
  onClick,
  onEdit,
  onDelete,
}) => {
  const handleMenuAction = (e: React.MouseEvent, action: () => void): void => {
    e.stopPropagation();
    action();
  };

  const { theme } = useTheme();

  const isLightMode = theme === 'light';

  const placeholderSrc = isLightMode
    ? '/placeholder-album-light.svg'
    : '/placeholder-album.svg';

  const coverImageSrc = album.cover_image_path
    ? convertFileSrc(album.cover_image_path)
    : placeholderSrc;

  return (
    <Card
      className="group relative cursor-pointer overflow-hidden py-0 transition-all"
      onClick={onClick}
    >
      <CardContent className="p-0">
        {/* Album Cover Image */}
        <div className="bg-muted relative aspect-4/5 overflow-hidden">
          <img
            src={coverImageSrc}
            alt={album.name}
            className="h-full w-full object-cover transition-transform ease-out group-hover:scale-110"
            onError={(e) => {
              const img = e.target as HTMLImageElement;
              img.onerror = null;
              img.src = placeholderSrc;
            }}
          />
          {/* Lock Icon for Locked Albums */}
          {album.is_locked && (
            <div className="bg-background/90 absolute top-3 left-3 rounded-full p-2.5 shadow-lg backdrop-blur-md">
              <Lock className="text-foreground h-5 w-5" />
            </div>
          )}
          {/* Actions Menu */}
          <div className="absolute top-3 right-3">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="bg-background/80 hover:bg-background/90 h-9 w-9 rounded-full backdrop-blur-sm"
                  onClick={(e) => e.stopPropagation()}
                >
                  <MoreVertical className="h-5 w-5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={(e) => handleMenuAction(e, onEdit)}>
                  <Pencil className="mr-2 h-4 w-4" />
                  Edit Album
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={(e) => handleMenuAction(e, onDelete)}
                  className="text-destructive focus:text-destructive"
                >
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete Album
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
        {/* Album Info */}
        <div className="space-y-1 p-4">
          <h3 className="truncate text-base font-semibold">{album.name}</h3>
          {album.description && (
            <p className="text-muted-foreground line-clamp-2 text-sm">
              {album.description}
            </p>
          )}

          <p className="text-muted-foreground text-sm">
            {album.image_count} {album.image_count === 1 ? 'photo' : 'photos'}
          </p>
        </div>
      </CardContent>
    </Card>
  );
};
