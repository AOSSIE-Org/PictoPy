import MediaGallery from '@/components/Media/MediaGallery';
import LoadingScreen from '@/components/ui/LoadingScreen/LoadingScreen';
import { useImages } from '@/hooks/useImages';

function Dashboard() {
  const localPath = localStorage.getItem('folderPath') || '';
  const { images, isCreating: loading } = useImages(localPath);

  const mappedImages = images.map(image => ({
    imagePath: image.original,
    ...image
  }));

  if (loading) {
    return <LoadingScreen />;
  }

  return (
    <>
      <MediaGallery mediaItems={mappedImages} title="Image Gallery" type="image" />
    </>
  );
}

export default Dashboard;
