import MediaGallery from "@/components/Media/MediaGallery";
import LoadingScreen from "@/components/ui/LoadingScreen/LoadingScreen";
import { useImages } from "@/hooks/useImages";

function Dashboard() {
  const localPath = localStorage.getItem("folderPath") || "";
  const { images, loading } = useImages(localPath);

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
