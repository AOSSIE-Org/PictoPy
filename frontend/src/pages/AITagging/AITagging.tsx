import { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { FaceCollections } from '@/components/FaceCollections';
import { Image } from '@/types/Media';
import { setImages } from '@/features/imageSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { selectImages } from '@/features/imageSelectors';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllImages } from '@/api/api-functions';
import {
  ChronologicalGallery,
  MonthMarker,
} from '@/components/Media/ChronologicalGallery';
import TimelineScrollbar from '@/components/Timeline/TimelineScrollbar';
import { EmptyAITaggingState } from '@/components/EmptyStates/EmptyAITaggingState';
import { X } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

export const AITagging = () => {
  const dispatch = useDispatch();
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);
  const [searchState, setSearchState] = useState<{
    active: boolean;
    peopleNames: string[];
  }>({ active: false, peopleNames: [] });
  const taggedImages = useSelector(selectImages);
  const {
    data: imagesData,
    isLoading: imagesLoading,
    isSuccess: imagesSuccess,
    isError: imagesError,
  } = usePictoQuery({
    queryKey: ['images', { tagged: true }],
    queryFn: () => fetchAllImages(true),
  });

  useEffect(() => {
    if (imagesLoading) {
      dispatch(showLoader('Loading AI tagging data'));
    } else if (imagesError) {
      dispatch(hideLoader());
    } else if (imagesSuccess) {
      const images = imagesData?.data as Image[];
      dispatch(setImages(images));
      dispatch(hideLoader());
    }
  }, [imagesData, imagesSuccess, imagesError, imagesLoading, dispatch]);

  const handleSearchActivated = (names: string[]) => {
    setSearchState({ active: true, peopleNames: names });
  };

  const handleResetSearch = () => {
    setSearchState({ active: false, peopleNames: [] });
    const images = imagesData?.data as Image[] | undefined;
    if (images) {
      dispatch(setImages(images));
    }
  };

  const formatSearchTitle = (names: string[]): string => {
    if (names.length === 1) return names[0];
    if (names.length === 2) return `${names[0]} & ${names[1]}`;
    return `${names.slice(0, -1).join(', ')} & ${names[names.length - 1]}`;
  };

  return (
    <div className="relative flex h-full flex-col pr-6">
      <div
        ref={scrollableRef}
        className="hide-scrollbar flex-1 overflow-x-hidden overflow-y-auto"
      >
        <h1 className="mt-6 mb-6 text-2xl font-bold">AI Tagging</h1>

        {/* Face Collections Section */}
        <div className="mb-8">
          <FaceCollections onSearchActivated={handleSearchActivated} />
        </div>

        {searchState.active && (
          <div className="border-primary/20 bg-primary/5 mb-4 flex items-center justify-between rounded-lg border px-4 py-2.5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-muted-foreground text-sm">
                Filtered by:
              </span>
              {searchState.peopleNames.map((name) => (
                <Badge key={name} variant="secondary" className="text-xs">
                  {name}
                </Badge>
              ))}
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleResetSearch}
              className="h-7 shrink-0 gap-1.5 text-xs"
            >
              <X className="h-3 w-3" />
              View all images
            </Button>
          </div>
        )}

        {/* Gallery Section */}
        <div className="flex-1">
          {taggedImages.length > 0 ? (
            <ChronologicalGallery
              images={taggedImages}
              showTitle={true}
              title={
                searchState.active
                  ? formatSearchTitle(searchState.peopleNames)
                  : 'All Images'
              }
              onMonthOffsetsChange={setMonthMarkers}
              scrollContainerRef={scrollableRef}
            />
          ) : (
            <EmptyAITaggingState />
          )}
        </div>
      </div>
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
