import MediaGallery from '@/components/Media/MediaGallery';
import LoadingScreen from '@/components/ui/LoadingScreen/LoadingScreen';
import { useImages } from '@/hooks/useImages';
import { useLocalStorage } from '@/hooks/LocalStorage';

function Dashboard() {
  const [currentPaths] = useLocalStorage<string[]>('folderPaths', []);
  const { images, isCreating: loading } = useImages(currentPaths);
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
