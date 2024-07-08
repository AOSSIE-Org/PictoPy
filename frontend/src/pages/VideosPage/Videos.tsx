import VideoGallery from "@/components/Videos/VideoGallery";
import { usevideos } from "@/hooks/UseVideos";

const Videos: React.FC = () => {
  const localPath = localStorage.getItem("folderPath") || "";
  const { videos, loading } = usevideos(localPath);

  if (loading) {
    return <div>Loading images...</div>;
  }

  return (
    <div>
      <VideoGallery videos={videos} title={localPath} />
    </div>
  );
};

export default Videos;
