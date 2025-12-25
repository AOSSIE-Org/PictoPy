import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  createAlbum,
  getAlbums,
  getAlbumImages,
  fetchAllImages,
  Album as AlbumType,
} from '@/api/api-functions';
import {
  ChronologicalGallery,
  MonthMarker,
} from '@/components/Media/ChronologicalGallery';
import TimelineScrollbar from '@/components/Timeline/TimelineScrollbar';
import { Image } from '@/types/Media';
import { ArrowLeft } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { useDispatch } from 'react-redux';
import { setImages } from '@/features/imageSlice';

function Album() {
  const [albumName, setAlbumName] = useState('');
  const [albums, setAlbums] = useState<AlbumType[]>([]);
  const [loading, setLoading] = useState(false);

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

  if (selectedAlbum) {
    return (
      <div className="relative flex h-full flex-col pr-6">
        {/* Simple Header */}
        <div className="bg-background z-10 flex items-center gap-4 p-4">
          <Button variant="ghost" onClick={() => setSelectedAlbum(null)}>
            <ArrowLeft className="mr-2 h-5 w-5" />
            Back to Albums
          </Button>
          <h1 className="text-2xl font-bold">{selectedAlbum.album_name}</h1>
          <span className="text-muted-foreground">
            {albumImages.length} images
          </span>
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
            className="bg-card text-card-foreground cursor-pointer rounded-lg border p-4 transition-shadow hover:shadow-lg"
            onClick={() => setSelectedAlbum(album)}
          >
            <h3 className="mb-2 text-lg font-semibold">{album.album_name}</h3>
            <p className="text-muted-foreground text-sm">
              {album.description || 'No description'}
            </p>
            {album.is_hidden && (
              <span className="bg-secondary text-secondary-foreground mt-2 inline-block rounded px-2 py-1 text-xs">
                Hidden
              </span>
            )}
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
