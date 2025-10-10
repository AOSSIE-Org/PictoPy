import { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Image } from '@/types/Media';
import { setImages } from '@/features/imageSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { selectImages, selectIsImageViewOpen } from '@/features/imageSelectors';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllClusters, fetchAllImages } from '@/api/api-functions';
import { RootState } from '@/app/store';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { useNavigate, useParams } from 'react-router';
import { setClusters } from '@/features/faceClustersSlice';
import { Cluster } from '@/types/Media';
import { Button } from '@/components/ui/button'; // Add this import
import { ArrowLeft } from 'lucide-react'; // Add this import
import { ROUTES } from '@/constants/routes'; // Add this import
import { ImageCard } from '@/components/Media/ImageCard';
import { MediaView } from '@/components/Media/MediaView';

export const SearchImages = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const isImageViewOpen = useSelector(selectIsImageViewOpen);
  const images = useSelector(selectImages);
  const searchState = useSelector((state: RootState) => state.search);
  const { clusters } = useSelector((state: RootState) => state.faceClusters);
  const query = useParams().query || '';
  const [showButton, setShowButton] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => {
      setShowButton(true);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  const { data: clustersData, isSuccess: clustersSuccess } = usePictoQuery({
    queryKey: ['clusters'],
    queryFn: fetchAllClusters,
  });

  // Check if query is a face name and redirect
  useEffect(() => {
    if (clusters && clusters.length > 0 && query) {
      // Find cluster with exact name match
      const matchedCluster = clusters.find(
        (cluster: Cluster) =>
          cluster.cluster_name?.toLowerCase().trim() ===
          query.toLowerCase().trim(),
      );

      if (matchedCluster) {
        // Query is a face name, redirect to person page
        navigate(`/person/${matchedCluster.cluster_id}`);
        return;
      }
    }
  }, [clusters, query, navigate]);

  useEffect(() => {
    if (clustersSuccess && clustersData?.data?.clusters) {
      const clusters = (clustersData.data.clusters || []) as Cluster[];
      dispatch(setClusters(clusters));
    }
  }, [clustersData, clustersSuccess, dispatch]);

  const isSearchActive = searchState.active;
  const searchResults = searchState.images;

  const { data, isLoading, isSuccess, isError } = usePictoQuery({
    queryKey: ['images'],
    queryFn: fetchAllImages,
    enabled: !isSearchActive, // Fixed typo here
  });

  // Handle fetching lifecycle
  useEffect(() => {
    if (!isSearchActive) {
      if (isLoading) {
        dispatch(showLoader('Loading images'))
      } else if (isError) {
        dispatch(hideLoader());
        dispatch(
          showInfoDialog({
            title: 'Error',
            message: 'Failed to load images. Please try again later.',
            variant: 'error',
          }),
        );
      } else if (isSuccess) {
        const images = data?.data as Image[];
        dispatch(setImages(images));
        dispatch(hideLoader());
      }
    }
  }, [data, isSuccess, isError, isLoading, dispatch, isSearchActive]);

  // Filter by month
  const filterImagesByMonthYear = (
    images: Image[],
    monthYearString: string | null,
  ) => {
    if (!monthYearString) return images;

    return images.filter((img) => {
      if (!img.metadata?.date_created) return false;

      const dateCreated = new Date(img.metadata.date_created);
      const imgMonthYear = dateCreated.toLocaleDateString('en-US', {
        month: 'long',
        year: 'numeric',
      });

      return imgMonthYear === monthYearString;
    });
  };

  // Format query
  const selectedMonthYear = query
    ? query
        .split(' ')
        .map(
          (word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase(),
        )
        .join(' ')
    : null;

  const baseImages = isSearchActive ? searchResults : images;
  const displayImages = filterImagesByMonthYear(baseImages, selectedMonthYear);

  const title = selectedMonthYear
    ? `${selectedMonthYear} (${displayImages.length} images)`
    : isSearchActive && searchResults.length > 0
      ? `Face Search Results (${searchResults.length} found)`
      : 'All Images';

  return (
    <div className="p-6">
      {showButton ? (
        <>
          <Button
            variant="outline"
            onClick={() => {
              navigate(`/${ROUTES.HOME}`);
            }}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Home
          </Button>
        </>
      ) : (
        <>
          <b className="text-2xl"> Loading ...</b>
        </>
      )}
      <br />
      <h1 className="mb-6 text-2xl font-bold">{title}</h1>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
        {displayImages.map((image, index) => (
          <ImageCard
            key={image.id}
            image={image}
            imageIndex={index}
            className="w-full"
          />
        ))}
      </div>

      {/* Media viewer modal */}
      {isImageViewOpen && <MediaView images={displayImages} />}
    </div>
  );
};
