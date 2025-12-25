import { useCallback, useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Image } from '@/types/Media';
import { setImages } from '@/features/imageSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { selectImages } from '@/features/imageSelectors';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllClusters, fetchAllImages } from '@/api/api-functions';
import { RootState } from '@/app/store';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { useNavigate, useParams } from 'react-router';
import { setClusters } from '@/features/faceClustersSlice';
import { Cluster } from '@/types/Media';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';
import { ROUTES } from '@/constants/routes';
import {
  ChronologicalGallery,
  MonthMarker,
} from '@/components/Media/ChronologicalGallery';
import { EmptyGalleryState } from '@/components/EmptyStates/EmptyGalleryState';
import TimelineScrollbar from '@/components/Timeline/TimelineScrollbar';

export const SearchImages = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const images = useSelector(selectImages);
  const searchState = useSelector((state: RootState) => state.search);
  const { clusters } = useSelector((state: RootState) => state.faceClusters);
  const query = useParams().query || '';

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

  const handleMonthOffsetsChange = useCallback((entries: MonthMarker[]) => {
    setMonthMarkers((prev) => {
      if (
        prev.length === entries.length &&
        prev.every(
          (m, i) =>
            m.offset === entries[i].offset &&
            m.month === entries[i].month &&
            m.year === entries[i].year,
        )
      ) {
        return prev;
      }
      return entries;
    });
  }, []);

  const fetchAllImagesWrapper = async ({
    queryKey,
  }: {
    queryKey: [string, boolean?];
  }) => {
    const [, tagged] = queryKey;
    return fetchAllImages(tagged);
  };
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);
  const { data, isLoading, isSuccess, isError } = usePictoQuery({
    queryKey: ['images'],
    queryFn: fetchAllImagesWrapper,
    enabled: !isSearchActive, // Fixed typo here
  });

  useEffect(() => {
    if (!isSearchActive) {
      if (isLoading) {
        dispatch(showLoader('Loading images'));
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
  const scrollableRef = useRef<HTMLDivElement>(null);

  // Format query
  const selectedMonthYear = query
    ? query
        .split(' ')
        .map(
          (word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase(),
        )
        .join(' ')
    : null;
  const displayImages = filterImagesByMonthYear(images, selectedMonthYear);
  const title = selectedMonthYear
    ? `${selectedMonthYear} (${displayImages.length} images)`
    : isSearchActive && searchResults.length > 0
      ? `Face Search Results (${searchResults.length} found)`
      : 'All Images';

  return (
    <div className="relative flex h-full flex-col pr-6">
      {/* Gallery Section */}
      <div
        ref={scrollableRef}
        className="hide-scrollbar flex-1 overflow-x-hidden overflow-y-auto"
      >
        <Button
          variant="outline"
          onClick={() => {
            navigate(`/${ROUTES.HOME}`);
          }}
          className="flex cursor-pointer items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Home
        </Button>
        {displayImages.length > 0 ? (
          <ChronologicalGallery
            images={displayImages}
            showTitle={true}
            title={title}
            onMonthOffsetsChange={handleMonthOffsetsChange}
            scrollContainerRef={scrollableRef}
          />
        ) : (
          <EmptyGalleryState />
        )}
      </div>

      {/* Timeline Scrollbar */}
      {monthMarkers.length > 0 && (
        <TimelineScrollbar
          scrollableRef={scrollableRef}
          monthMarkers={monthMarkers}
          className="absolute top-0 right-0 h-full w-4"
        />
      )}
    </div>
  );
};
