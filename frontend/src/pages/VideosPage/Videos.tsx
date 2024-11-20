import { LoadingScreen } from '@/components/ui/LoadingScreen/LoadingScreen';
import MediaGallery from '@/components/Media/MediaGallery';
import { useVideos } from '@/hooks/UseVideos';

const Videos: React.FC = () => {
  const localPath = localStorage.getItem('folderPath') || '';
  const { videos, loading } = useVideos(localPath);

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
