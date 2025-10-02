import { fetchAllAlbums } from '@/api/api-functions/albums';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { selectAlbums } from '@/features/albumSelectors';
import { setAlbums } from '@/features/albumSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { hideLoader, showLoader } from '@/features/loaderSlice';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import {
  Edit3,
  Eye,
  EyeOff,
  FolderOpen,
  Lock,
  MoreHorizontal,
  Plus,
  Trash2,
} from 'lucide-react';
import * as React from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';

interface AlbumListProps {
  onCreateAlbum?: () => void;
  onEditAlbum?: (albumId: string) => void;
  onDeleteAlbum?: (albumId: string, albumName: string) => void;
}

export function AlbumList({
  onCreateAlbum,
  onEditAlbum,
  onDeleteAlbum,
}: AlbumListProps) {
  const dispatch = useDispatch();
  const albums = useSelector(selectAlbums);
  const [showHidden, setShowHidden] = React.useState(false);

  // Fetch albums
  const { data, isLoading, isSuccess, isError } = usePictoQuery({
    queryKey: ['albums', showHidden],
    queryFn: () => fetchAllAlbums(showHidden),
  });

  // Handle loading states
  React.useEffect(() => {
    if (isLoading) {
      dispatch(showLoader('Loading albums...'));
    } else if (isError) {
      dispatch(hideLoader());
      dispatch(
        showInfoDialog({
          title: 'Error',
          message: 'Failed to load albums. Please try again later.',
          variant: 'error',
        }),
      );
    } else if (isSuccess && data?.success) {
      dispatch(setAlbums(data.albums));
      dispatch(hideLoader());
    }
  }, [data, isSuccess, isError, isLoading, dispatch]);

  const handleToggleShowHidden = () => {
    setShowHidden(!showHidden);
  };

  if (albums.length === 0 && !isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <FolderOpen className="text-muted-foreground mb-4 h-16 w-16" />
        <h2 className="mb-2 text-xl font-semibold">No albums yet</h2>
        <p className="text-muted-foreground mb-6 max-w-md text-center">
          Create your first album to organize your photos into collections.
        </p>
        <Button onClick={onCreateAlbum} className="gap-2">
          <Plus className="h-4 w-4" />
          Create Album
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Albums</h1>
          <p className="text-muted-foreground">
            {albums.length} album{albums.length !== 1 ? 's' : ''}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleToggleShowHidden}
            className="gap-2"
          >
            {showHidden ? (
              <EyeOff className="h-4 w-4" />
            ) : (
              <Eye className="h-4 w-4" />
            )}
            {showHidden ? 'Hide Hidden' : 'Show Hidden'}
          </Button>
          <Button onClick={onCreateAlbum} className="gap-2">
            <Plus className="h-4 w-4" />
            New Album
          </Button>
        </div>
      </div>

      {/* Album Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {albums.map((album: any) => (
          <Card
            key={album.album_id}
            className="group transition-shadow hover:shadow-md"
          >
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <CardTitle className="truncate">
                      {album.album_name}
                    </CardTitle>
                    {album.is_hidden && (
                      <Lock className="text-muted-foreground h-4 w-4 flex-shrink-0" />
                    )}
                  </div>
                  {album.description && (
                    <CardDescription className="mt-1 line-clamp-2">
                      {album.description}
                    </CardDescription>
                  )}
                </div>

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 opacity-0 transition-opacity group-hover:opacity-100"
                    >
                      <MoreHorizontal className="h-4 w-4" />
                      <span className="sr-only">Album options</span>
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                      onClick={() => onEditAlbum?.(album.album_id)}
                    >
                      <Edit3 className="mr-2 h-4 w-4" />
                      Edit Album
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() =>
                        onDeleteAlbum?.(album.album_id, album.album_name)
                      }
                      className="text-red-600"
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete Album
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardHeader>

            <CardContent>
              {/* Album preview placeholder */}
              <div className="bg-muted mb-3 flex aspect-square items-center justify-center rounded-lg">
                <FolderOpen className="text-muted-foreground h-8 w-8" />
              </div>

              {/* Album badges */}
              <div className="flex items-center gap-2">
                {album.is_hidden && (
                  <Badge variant="secondary" className="text-xs">
                    Hidden
                  </Badge>
                )}
                {/* Photo count badge */}
                <Badge variant="outline" className="text-xs">
                  0 photos
                </Badge>
              </div>
            </CardContent>

            <CardFooter>
              <Link to={`/albums/${album.album_id}`} className="w-full">
                <Button variant="outline" className="w-full">
                  View Album
                </Button>
              </Link>
            </CardFooter>
          </Card>
        ))}
      </div>
    </div>
  );
}
