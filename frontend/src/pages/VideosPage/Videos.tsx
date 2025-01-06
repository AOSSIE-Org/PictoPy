import { LoadingScreen } from '@/components/ui/LoadingScreen/LoadingScreen';
import MediaGallery from '@/components/Media/MediaGallery';
import { useVideos } from '@/hooks/UseVideos';
import { useLocalStorage } from '@/hooks/LocalStorage';

const Videos: React.FC = () => {
  const [currentPaths] = useLocalStorage<string[]>('folderPaths', []);
  const { videos, loading } = useVideos(currentPaths);

  if (loading) {
    return <LoadingScreen />;
  }

  return (
    <>
      <MediaGallery mediaItems={videos} title="Video Gallery" type="video" />
    </>
  );
};

export default Videos;
