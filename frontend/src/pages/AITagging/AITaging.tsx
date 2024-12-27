import AIGallery from '@/components/AITagging/AIgallery';
import { LoadingScreen } from '@/components/ui/LoadingScreen/LoadingScreen';
import { usePictoQuery } from '@/hooks/useQueryExtensio';
import { getAllImageObjects } from '../../../api/api-functions/images';

const AITagging: React.FC = () => {
  const { isLoading: loading, successData: images } = usePictoQuery({
    queryFn: getAllImageObjects,
    queryKey: ['ai-tagging-images', 'ai'],
  });

  if (loading) {
    return (
      <div>
        <LoadingScreen />
      </div>
    );
  }

  return (
    <>
      <AIGallery
        mediaItems={images}
        title="Tagged images"
        type="image"
        folderPath=""
      />
    </>
  );
};

export default AITagging;
