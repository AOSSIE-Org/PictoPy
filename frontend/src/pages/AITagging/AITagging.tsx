import { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { FaceCollections } from "@/components/FaceCollections";
import { Image } from "@/types/Media";
import { setImages } from "@/features/imageSlice";
import { showLoader, hideLoader } from "@/features/loaderSlice";
import { selectImages } from "@/features/imageSelectors";
import { usePictoQuery } from "@/hooks/useQueryExtension";
import { fetchAllImages } from "@/api/api-functions";
import {
  ChronologicalGallery,
  MonthMarker,
} from "@/components/Media/ChronologicalGallery";
import TimelineScrollbar from "@/components/Timeline/TimelineScrollbar";
import { EmptyAITaggingState } from "@/components/EmptyStates/EmptyAITaggingState";
import { CollageMaker } from "@/components/Collage/CollageMaker";

export const AITagging = () => {
  const [openCollage, setOpenCollage] = useState(false);
  const dispatch = useDispatch();
  const scrollableRef = useRef<HTMLDivElement>(null);
  const [monthMarkers, setMonthMarkers] = useState<MonthMarker[]>([]);
  const taggedImages = useSelector(selectImages);

  const {
    data: imagesData,
    isLoading: imagesLoading,
    isSuccess: imagesSuccess,
    isError: imagesError,
  } = usePictoQuery({
    queryKey: ["images", { tagged: true }],
    queryFn: () => fetchAllImages(true),
  });

  useEffect(() => {
    if (imagesLoading) {
      dispatch(showLoader("Loading AI tagging data"));
    } else if (imagesError) {
      dispatch(hideLoader());
    } else if (imagesSuccess) {
      const images = imagesData?.data as Image[];
      dispatch(setImages(images));
      dispatch(hideLoader());
    }
  }, [imagesData, imagesSuccess, imagesError, imagesLoading, dispatch]);

  return (
    <div className="relative flex h-full flex-col pr-6">
      <div
        ref={scrollableRef}
        className="hide-scrollbar flex-1 overflow-x-hidden overflow-y-auto"
      >
        {/* Header and Button Container */}
        <div className="mt-6 mb-6 flex items-center justify-between border-b pb-3">
          <h1 className="text-2xl font-bold">AI Tagging</h1>
          <button
            onClick={() => setOpenCollage(true)}
            className="rounded-lg bg-blue-600 text-white px-4 py-2 text-sm font-semibold shadow-lg hover:bg-blue-700 transition-all duration-200"
          >
            🖼️ Create Photo Collage
          </button>
        </div>

        {/* Face Collections */}
        <div className="mb-8">
          <FaceCollections />
        </div>

        {/* Gallery Section */}
        <div className="flex-1">
          {taggedImages.length > 0 ? (
            <ChronologicalGallery
              images={taggedImages}
              showTitle={true}
              title="All Images"
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

      {/* Collage Modal */}
      {openCollage && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[2000] flex justify-center items-center p-4">
          <div className="bg-white dark:bg-neutral-900 rounded-xl p-4 w-[95%] max-w-5xl shadow-xl relative">
            <button
              // FIX APPLIED: Added cursor-pointer to display the hand icon immediately on hover
              className="absolute top-3 right-4 text-xl font-bold hover:text-red-500 cursor-pointer"
              onClick={() => setOpenCollage(false)}
            >
              ✕
            </button>

            <CollageMaker images={taggedImages} />
          </div>
        </div>
      )}
    </div>
  );
};
