import MediaGallery from '@/components/Media/MediaGallery';
import LoadingScreen from '@/components/ui/LoadingScreen/LoadingScreen';
import { useImages } from '@/hooks/useImages';
import { useLocalStorage } from '@/hooks/LocalStorage';
import { useEffect } from 'react';
import { deleteCache } from '@/services/cacheService';

function Dashboard() {
  const [currentPaths] = useLocalStorage<string[]>('folderPaths', []);
  const { images, isCreating: loading } = useImages(currentPaths);
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
    return <LoadingScreen />;
  }
  return (
    <>
      <MediaGallery mediaItems={images} title="Image Gallery" type="image" />
    </>
  );
}

export default Dashboard;
