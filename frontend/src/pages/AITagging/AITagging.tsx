import { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { FaceCollections } from '@/components/FaceCollections';
import { Image } from '@/types/Media';
import { setImages } from '@/features/imageSlice';
import {
  setCurrentViewIndex as setCurrentVideoViewIndex,
  setVideos,
} from '@/features/videoSlice';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { selectImages } from '@/features/imageSelectors';
import { selectIsVideoViewOpen, selectVideos } from '@/features/videoSelectors';
import { VideoCard } from '@/components/Media/VideoCard';
import { VideoPlayerOverlay } from '@/components/VideoPlayer/VideoPlayerOverlay';
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
import { formatPeopleTitle } from '@/utils/personUtils';
import { RankedGallery } from '@/components/Media/RankedGallery';
import {
  GALLERY_SORT_OPTIONS,
  GallerySortDropdown,
  type GallerySortValue,
} from '@/components/GallerySortDropdown';
import { usePersistedSort } from '@/hooks/usePersistedSort';

const AI_TAGGING_SORT_STORAGE_KEY = 'pictopy-ai-tagging-sort';

// Derived from the options above so a removed sort stops being restorable.
const GALLERY_SORT_VALUES = GALLERY_SORT_OPTIONS.map((option) => option.value);

export const AITagging = () => {
  const dispatch = useDispatch();
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);
  const [sortMode, setSortMode] = usePersistedSort<GallerySortValue>(
    AI_TAGGING_SORT_STORAGE_KEY,
    'best_match',
    GALLERY_SORT_VALUES,
  );
  const [searchState, setSearchState] = useState<{
    active: boolean;
    peopleNames: string[];
    matchMode: 'match_any' | 'match_all';
  }>({ active: false, peopleNames: [], matchMode: 'match_any' });
  const taggedImages = useSelector(selectImages);
  // Only while a people search is active: otherwise the slice still holds
  // whatever the videos page last loaded, which is not a result of this page.
  const searchVideos = useSelector(selectVideos);
  const isVideoViewOpen = useSelector(selectIsVideoViewOpen);
  const matchedVideos = searchState.active ? searchVideos : [];
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
      const images = (imagesData?.data ?? []) as Image[];
      dispatch(setImages(images));
      dispatch(hideLoader());
    }
  }, [imagesData, imagesSuccess, imagesError, imagesLoading, dispatch]);

  const handleSearchActivated = (
    names: string[],
    matchMode: 'match_any' | 'match_all',
  ) => {
    setSearchState({ active: true, peopleNames: names, matchMode });
  };

  const handleResetSearch = () => {
    setSortMode('best_match');
    setSearchState({ active: false, peopleNames: [], matchMode: 'match_any' });
    const images = imagesData?.data as Image[] | undefined;
    if (images) {
      dispatch(setImages(images));
    }
    dispatch(setVideos([]));
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
                {searchState.matchMode === 'match_any'
                  ? 'Filter by (Any):'
                  : 'Filter by (All):'}
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
            searchState.active && sortMode === 'best_match' ? (
              <RankedGallery
                images={taggedImages}
                title={formatPeopleTitle(
                  searchState.peopleNames,
                  searchState.matchMode,
                )}
                titleRight={
                  <GallerySortDropdown
                    value={sortMode}
                    onValueChange={setSortMode}
                  />
                }
              />
            ) : (
              <ChronologicalGallery
                images={taggedImages}
                showTitle={true}
                title={
                  searchState.active
                    ? formatPeopleTitle(
                        searchState.peopleNames,
                        searchState.matchMode,
                      )
                    : 'All Images'
                }
                titleRight={
                  searchState.active ? (
                    <GallerySortDropdown
                      value={sortMode}
                      onValueChange={setSortMode}
                    />
                  ) : undefined
                }
                onMonthOffsetsChange={setMonthMarkers}
                scrollContainerRef={scrollableRef}
              />
            )
          ) : matchedVideos.length === 0 ? (
            // A search can match only videos, which render below
            <EmptyAITaggingState />
          ) : null}

          {/* Videos the selected people appear in */}
          {matchedVideos.length > 0 && (
            <>
              <h2 className="mt-6 mb-4 text-xl font-semibold">Videos</h2>
              <div className="grid grid-cols-1 gap-4 pb-6 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
                {matchedVideos.map((video, index) => (
                  <div key={video.id} className="group relative">
                    <VideoCard
                      video={video}
                      className="w-full transition-transform duration-200 group-hover:scale-105"
                      onClick={() => dispatch(setCurrentVideoViewIndex(index))}
                    />
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
      {isVideoViewOpen && matchedVideos.length > 0 && (
        <VideoPlayerOverlay videos={matchedVideos} />
      )}
      {monthMarkers.length > 0 &&
        !(searchState.active && sortMode === 'best_match') && (
          <TimelineScrollbar
            scrollableRef={scrollableRef}
            monthMarkers={monthMarkers}
            className="absolute top-0 right-0 h-full w-4"
          />
        )}
    </div>
  );
};
