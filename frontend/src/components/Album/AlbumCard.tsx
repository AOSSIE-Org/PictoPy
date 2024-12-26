import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { MoreVertical, Images } from 'lucide-react';
import { convertFileSrc } from '@tauri-apps/api/core';
import { AlbumCardProps } from '@/types/Album';

const AlbumCard: React.FC<AlbumCardProps> = ({
  album,
  onClick,
  onEdit,
  onDelete,
}) => {
  return (
    <div className="group relative h-64 overflow-hidden rounded-lg bg-slate-200 shadow-lg transition-transform duration-300 ease-in-out hover:-translate-y-2 hover:shadow-xl dark:bg-slate-800 dark:text-card-foreground">
      <div onClick={onClick} className="h-full cursor-pointer">
        {album.imageCount ? (
          <img
            src={convertFileSrc(album.coverImage)}
            alt={`Cover for ${album.title}`}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <Images className="h-16 w-16 text-slate-400" />
          </div>
        )}
        <div className="absolute inset-0 flex items-end bg-black bg-opacity-40 p-4 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
          <div className="text-white">
            <h3 className="text-lg font-semibold">{album.title}</h3>
            <p className="text-sm">
              {album.imageCount} image{album.imageCount !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
      </div>
      <div className="absolute right-2 top-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={onEdit}>Edit</DropdownMenuItem>
            <DropdownMenuItem onClick={onDelete} className="text-red-600">
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  );
};
export default AlbumCard;
