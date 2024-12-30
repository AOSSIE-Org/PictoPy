import AIGallery from '@/components/AITagging/AIgallery';

const AITagging: React.FC = () => {
  return (
    <>
      <AIGallery title="Tagged images" type="image" folderPath="./images" />
    </>
  );
};

export default AITagging;
