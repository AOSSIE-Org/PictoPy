import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  createAlbum,
  getAlbums,
  getAlbumImages,
  fetchAllImages,
  updateAlbum,
  removeImageFromAlbum,
  deleteAlbum,
  Album as AlbumType,
} from '@/api/api-functions';
import {
  ChronologicalGallery,
  MonthMarker,
} from '@/components/Media/ChronologicalGallery';
import TimelineScrollbar from '@/components/Timeline/TimelineScrollbar';
import { Image } from '@/types/Media';
import {
  ArrowLeft,
  CheckIcon,
  PencilIcon,
  XIcon,
  TrashIcon,
} from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useDispatch } from 'react-redux';
import { setImages } from '@/features/imageSlice';
import { convertFileSrc } from '@tauri-apps/api/core';

function Album() {
  const [albumName, setAlbumName] = useState('');
  const [albums, setAlbums] = useState<AlbumType[]>([]);
  const [loading, setLoading] = useState(false);
  const [albumCovers, setAlbumCovers] = useState<Record<string, string | null>>(
    {},
  );

  // Navigation State
  const [selectedAlbum, setSelectedAlbum] = useState<AlbumType | null>(null);
  const [albumImages, setAlbumImages] = useState<Image[]>([]);

  // Gallery Props
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);
  const dispatch = useDispatch();

  // Fetch all images for lookup (could be optimized)
  const { data: allImagesData } = useQuery({
    queryKey: ['images'],
    queryFn: () => fetchAllImages(),
    staleTime: 5 * 60 * 1000,
  });

  const fetchAlbums = async () => {
    try {
      const response = await getAlbums();
      if (response.success) {
        setAlbums(response.albums);
      }
    } catch (error) {
      console.error('Failed to fetch albums:', error);
    }
  };

  useEffect(() => {
    fetchAlbums();
  }, []);

  // Fetch covers for albums
  useEffect(() => {
    const fetchCovers = async () => {
      if (!allImagesData?.data || albums.length === 0) return;

      const covers: Record<string, string | null> = {};
      const allImages = allImagesData.data as Image[];
      const imageMap = new Map(allImages.map((img) => [img.id, img]));

      for (const album of albums) {
        if (album.is_hidden) continue;

        try {
          // We only need one image, but the API returns all IDs
          // This is not efficient for large albums but satisfies "no backend changes"
          const response = await getAlbumImages(album.album_id);
          if (response.success && response.image_ids.length > 0) {
            const firstImageId = response.image_ids[0];
            const image = imageMap.get(firstImageId);
            if (image) {
              covers[album.album_id] = image.thumbnailPath || image.path;
            }
          }
        } catch (error) {
          console.error(
            `Failed to fetch cover for album ${album.album_name}`,
            error,
          );
        }
      }
      setAlbumCovers((prev) => ({ ...prev, ...covers }));
    };

    fetchCovers();
  }, [albums, allImagesData]);

  // Fetch album images when an album is selected
  useEffect(() => {
    const loadAlbumImages = async () => {
      if (!selectedAlbum || !allImagesData) return;

      try {
        const response = await getAlbumImages(selectedAlbum.album_id);
        if (response.success && allImagesData.data) {
          const allImages = allImagesData.data as Image[];
          const filtered = allImages.filter((img) =>
            response.image_ids.includes(img.id),
          );
          setAlbumImages(filtered);
          dispatch(setImages(filtered));
        }
      } catch (error) {
        console.error('Failed to load album images', error);
        alert('Failed to load album images');
      }
    };

    if (selectedAlbum) {
      loadAlbumImages();
    }
  }, [selectedAlbum, allImagesData, dispatch]);

  const handleCreateAlbum = async () => {
    if (!albumName.trim()) {
      alert('Please enter an album name');
      return;
    }

    try {
      setLoading(true);
      await createAlbum({ name: albumName });
      alert('Album created successfully!');
      setAlbumName('');
      fetchAlbums();
    } catch (error: any) {
      console.error('Failed to create album:', error);
      alert(error.response?.data?.message || 'Failed to create album');
    } finally {
      setLoading(false);
    }
  };

  const [isEditingName, setIsEditingName] = useState(false);
  const [newAlbumName, setNewAlbumName] = useState('');

  const handleUpdateAlbum = async () => {
    if (!selectedAlbum || !newAlbumName.trim()) return;

    try {
      await updateAlbum(selectedAlbum.album_id, {
        name: newAlbumName,
        is_hidden: selectedAlbum.is_hidden,
        description: selectedAlbum.description,
      });

      // Update local state
      setSelectedAlbum({ ...selectedAlbum, album_name: newAlbumName });
      setIsEditingName(false);

      // Refresh list in background
      fetchAlbums();
    } catch (error) {
      console.error('Failed to update album:', error);
      alert('Failed to update album name');
    }
  };

  const startEditing = () => {
    if (selectedAlbum) {
      setNewAlbumName(selectedAlbum.album_name);
      setIsEditingName(true);
    }
  };

  const cancelEditing = () => {
    setIsEditingName(false);
    setNewAlbumName('');
  };

  const handleRemoveImage = async (imageId: string) => {
    if (!selectedAlbum) return;
    try {
      await removeImageFromAlbum(selectedAlbum.album_id, imageId);
      setAlbumImages((prev) => prev.filter((img) => img.id !== imageId));

      // Update covers if needed, but for now we just remove from view
    } catch (error) {
      console.error('Failed to remove image from album', error);
      alert('Failed to remove image from album');
    }
  };

  const handleDeleteAlbum = async () => {
    if (!selectedAlbum) return;

    try {
      await deleteAlbum(selectedAlbum.album_id);
      setSelectedAlbum(null);
      fetchAlbums();
    } catch (error) {
      console.error('Failed to delete album', error);
      alert('Failed to delete album');
    }
  };

  if (selectedAlbum) {
    return (
      <div className="relative flex h-full flex-col pr-6">
        {/* Simple Header */}
        <div className="bg-background z-10 flex items-center gap-4 p-4">
          <Button variant="ghost" onClick={() => setSelectedAlbum(null)}>
            <ArrowLeft className="mr-2 h-5 w-5" />
            Back to Albums
          </Button>

          {isEditingName ? (
            <div className="flex items-center gap-2">
              <Input
                value={newAlbumName}
                onChange={(e) => setNewAlbumName(e.target.value)}
                className="h-8 w-48"
                autoFocus
              />
              <Button
                size="icon"
                variant="ghost"
                className="h-8 w-8 text-green-600"
                onClick={handleUpdateAlbum}
              >
                <CheckIcon className="h-4 w-4" />
              </Button>
              <Button
                size="icon"
                variant="ghost"
                className="h-8 w-8 text-red-600"
                onClick={cancelEditing}
              >
                <XIcon className="h-4 w-4" />
              </Button>
            </div>
          ) : (
            <div className="group flex items-center gap-2">
              <h1 className="text-2xl font-bold">{selectedAlbum.album_name}</h1>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6 opacity-0 transition-opacity group-hover:opacity-100"
                onClick={startEditing}
              >
                <PencilIcon className="h-3 w-3" />
              </Button>
            </div>
          )}

          <div className="ml-auto flex items-center gap-4">
            <span className="text-muted-foreground">
              {albumImages.length} images
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-red-500 hover:bg-red-50 hover:text-red-700"
              onClick={handleDeleteAlbum}
              title="Delete Album"
            >
              <TrashIcon className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <div
          ref={scrollableRef}
          className="hide-scrollbar flex-1 overflow-x-hidden overflow-y-auto"
        >
          {albumImages.length > 0 ? (
            <ChronologicalGallery
              images={albumImages}
              showTitle={false}
              onMonthOffsetsChange={setMonthMarkers}
              scrollContainerRef={scrollableRef}
              albumId={selectedAlbum.album_id}
              onRemoveFromAlbum={handleRemoveImage}
            />
          ) : (
            <div className="text-muted-foreground p-10 text-center">
              No images in this album yet.
            </div>
          )}
        </div>

        {monthMarkers.length > 0 && (
          <TimelineScrollbar
            scrollableRef={scrollableRef}
            monthMarkers={monthMarkers}
            className="absolute top-0 right-0 h-full w-4"
          />
        )}
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-8 flex items-center gap-4">
        <Input
          placeholder="New Album Name"
          value={albumName}
          onChange={(e) => setAlbumName(e.target.value)}
          className="max-w-xs"
        />
        <Button onClick={handleCreateAlbum} disabled={loading}>
          {loading ? 'Creating...' : 'Create Album'}
        </Button>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
        {albums.map((album) => (
          <div
            key={album.album_id}
            className="bg-card text-card-foreground cursor-pointer overflow-hidden rounded-lg border transition-shadow hover:shadow-lg"
            onClick={() => setSelectedAlbum(album)}
          >
            {/* Cover Image */}
            <div className="bg-muted relative aspect-square w-full">
              {albumCovers[album.album_id] ? (
                <img
                  src={convertFileSrc(albumCovers[album.album_id]!)}
                  alt={album.album_name}
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="bg-secondary/30 text-muted-foreground flex h-full w-full items-center justify-center">
                  <span className="text-4xl text-gray-300 select-none">🖼️</span>
                </div>
              )}

              {album.is_hidden && (
                <div className="absolute top-2 right-2 rounded bg-black/50 px-2 py-1 text-xs font-medium text-white backdrop-blur-sm">
                  Hidden
                </div>
              )}
            </div>

            <div className="p-4">
              <h3
                className="truncate text-lg font-semibold"
                title={album.album_name}
              >
                {album.album_name}
              </h3>
              <p className="text-muted-foreground line-clamp-2 h-10 text-sm">
                {album.description || 'No description'}
              </p>
            </div>
          </div>
        ))}
        {albums.length === 0 && (
          <p className="text-muted-foreground col-span-full text-center">
            No albums found. Create one to get started!
          </p>
        )}
      </div>
    </div>
  );
}

export default Album;
