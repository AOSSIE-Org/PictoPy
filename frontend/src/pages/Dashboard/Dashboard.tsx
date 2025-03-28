import MediaGallery from '@/components/Media/MediaGallery';
// import LoadingScreen from '@/components/ui/LoadingScreen/LoadingScreen';
// import { useImages } from '@/hooks/useImages';
// import { useLocalStorage } from '@/hooks/LocalStorage';
// import { useEffect } from 'react';
// import { deleteCache } from '@/services/cacheService';
import { useLoaderData } from 'react-router-dom';

function Dashboard() {
  // const [currentPaths] = useLocalStorage<string[]>('folderPaths', []);
  // const { images, isCreating: loading } = useImages(currentPaths);
  const images:any = useLoaderData();
  console.log("Yes Images = ",images);
  // console.log("Data during fetching = ",data);
  
  // useEffect(() => {
  //   const func = async () => {
  //     try {
  //       const result = await deleteCache();
  //       if (result) {
  //         console.log('Cache deleted');
  //       }
  //     } catch (error) {
  //       console.error('Error deleting cache:', error);
  //     }
  //   };
  //   func();
  // }, [currentPaths]);


  // if (!data || loading)
  //   <div className="flex h-full w-full items-center justify-center">
  //     <LoadingScreen />;
  //   </div>;
  return (
    <>
      <MediaGallery mediaItems={images} title="Image Gallery" type="image" />
    </>
  );
}

export default Dashboard;
