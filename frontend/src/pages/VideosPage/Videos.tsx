import { LoadingScreen } from '@/components/ui/LoadingScreen/LoadingScreen';
import MediaGallery from '@/components/Media/MediaGallery';
import { useVideos } from '@/hooks/UseVideos';
import { useLocalStorage } from '@/hooks/LocalStorage';

const Videos: React.FC = () => {
  const [currentPaths] = useLocalStorage<string[]>('folderPaths', []);
  const { videos, loading } = useVideos(currentPaths);

  if (loading)
    <div className="flex h-full w-full items-center justify-center">
      <LoadingScreen />
    </div>;

  return (
    <>
      <MediaGallery mediaItems={videos} title="Video Gallery" type="video" />
    </>
  );
};

export default Videos;
