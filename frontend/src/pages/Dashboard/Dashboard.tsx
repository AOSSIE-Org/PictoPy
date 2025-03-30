import { useEffect, useState } from 'react';
import MediaGallery from '@/components/Media/MediaGallery';
import { useLocalStorage } from '@/hooks/LocalStorage';
import { deleteCache } from '@/services/cacheService';
import { useLoaderData } from 'react-router-dom';
import LoadingScreen from '@/components/ui/LoadingScreen/LoadingScreen';
import { useImages } from '@/hooks/useImages';

function Dashboard() {
  const [currentPaths] = useLocalStorage<string[]>('folderPaths', []);
  const fetchedImageData: any = useLoaderData();
  const [images, setImages] = useState(fetchedImageData ?? []);
  const { images: createdImages, isCreating: loading } = useImages(currentPaths);

  useEffect(() => {
    if (images.length === 0 && loading) {
      setImages(createdImages);
    }
  }, [createdImages, loading, images]);

  useEffect(() => {
    const func = async () => {
      try {
        const result = await deleteCache();
        if (result) {
          console.log('Cache deleted');
        }
      } catch (error) {
        console.error('Error deleting cache:', error);
      }
    };
    func();
  }, [currentPaths]);

  if (loading) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <LoadingScreen />
      </div>
    );
  }

  return <MediaGallery mediaItems={images} title="Image Gallery" type="image" />;
}

export default Dashboard;
