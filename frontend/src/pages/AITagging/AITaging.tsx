import AIGallery from "@/components/Photos/AIgallery";

import useAIImage from "@/hooks/AI_Image";

const AITagging: React.FC = () => {
  const localPath = localStorage.getItem("folderPath") || "";
  const { images, loading } = useAIImage(localPath);

  if (loading) {
    return <div>Loading images...</div>;
  }

  return (
    <div>
      <AIGallery images={images} title={localPath} />
    </div>
  );
};

export default AITagging;
