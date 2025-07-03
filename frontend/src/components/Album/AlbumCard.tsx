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
import { extractThumbnailPath } from '@/hooks/useImages';
const AlbumCard: React.FC<AlbumCardProps> = ({
  album,
  onClick,
  onEdit,
  onDelete,
}) => {
  return (
    <div className="group dark:text-card-foreground relative h-64 overflow-hidden rounded-lg bg-slate-200 shadow-lg transition-transform duration-300 ease-in-out hover:-translate-y-2 hover:shadow-xl dark:bg-slate-800">
      <div onClick={onClick} className="h-full cursor-pointer">
        {album.isHidden && (
          <div className="absolute top-2 left-2 rounded bg-red-600 px-2 py-1 text-xs text-white">
            Hidden
          </div>
        )}
        {album.imageCount ? (
          <img
            src={convertFileSrc(extractThumbnailPath(album.coverImage))}
            alt={`Cover for ${album.title}`}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <Images className="h-16 w-16 text-slate-400" />
          </div>
        )}
        <div className="bg-opacity-40 absolute inset-0 flex items-end bg-black p-4 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
          <div className="text-white">
            <h3 className="text-lg font-semibold">{album.title}</h3>
            <p className="text-sm">
              {album.imageCount} image{album.imageCount !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
      </div>
      <div className="absolute top-2 right-2">
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
