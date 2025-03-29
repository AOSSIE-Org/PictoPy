import { useEffect } from 'react';
import MediaGallery from '@/components/Media/MediaGallery';
import { useLocalStorage } from '@/hooks/LocalStorage';
import { deleteCache } from '@/services/cacheService';
import { useLoaderData } from 'react-router-dom';
import LoadingScreen from '@/components/ui/LoadingScreen/LoadingScreen';


function Dashboard() {
  const [currentPaths] = useLocalStorage<string[]>('folderPaths', []);
  const images:any = useLoaderData();
  
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


  if (!images)
    <div className="flex h-full w-full items-center justify-center">
      <LoadingScreen />;
    </div>;
  return (
    <>
      <MediaGallery mediaItems={images} title="Image Gallery" type="image" />
    </>
  );
}

export default Dashboard;
