import { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { MemoryCard } from '@/components/Memories/MemoryCard';
import { MemorySection } from '@/components/Memories/MemorySection';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllMemories } from '@/api/api-functions';
import { showLoader, hideLoader } from '@/features/loaderSlice';
import { showInfoDialog } from '@/features/infoDialogSlice';
import { AllMemoriesData } from '@/types/Memory';
import { Sparkles } from 'lucide-react';

const Memories = () => {
  const dispatch = useDispatch();

  const { data, isLoading, isSuccess, isError } = usePictoQuery({
    queryKey: ['memories'],
    queryFn: () => fetchAllMemories(),
  });

  useEffect(() => {
    if (isLoading) {
      dispatch(showLoader('Loading your memories...'));
    } else if (isError) {
      dispatch(hideLoader());
      dispatch(
        showInfoDialog({
          title: 'Error',
          message: 'Failed to load memories. Please try again later.',
          variant: 'error',
        }),
      );
    } else if (isSuccess) {
      dispatch(hideLoader());
    }
  }, [isLoading, isError, isSuccess, dispatch]);

  const memoriesData = data?.data as AllMemoriesData | undefined;

  return (
    <div className="h-full overflow-y-auto px-6 py-6">
      {/* Page Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3">
          <div className="rounded-full bg-gradient-to-br from-gray-500 to-gray-500 p-3">
            <Sparkles className="h-6 w-6 text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              Memories
            </h1>
            <p className="mt-1 text-gray-600 dark:text-gray-400">
              Relive your special moments
            </p>
          </div>
        </div>
      </div>

      {/* On This Day Section */}
      {memoriesData?.on_this_day && memoriesData.on_this_day.length > 0 && (
        <MemorySection
          title="On This Day"
          description="Photos from this day in previous years"
          isEmpty={memoriesData.on_this_day.length === 0}
          emptyMessage="No memories from this day in previous years"
        >
          {memoriesData.on_this_day.map((memory) => (
            <MemoryCard
              key={memory.year}
              title={`${memory.years_ago} ${memory.years_ago === 1 ? 'year' : 'years'} ago`}
              subtitle={memory.date}
              images={memory.images}
              icon="calendar"
              imageCount={memory.images.length}
            />
          ))}
        </MemorySection>
      )}

      {/* Recent Memories Section */}
      {memoriesData?.recent && memoriesData.recent.length > 0 && (
        <MemorySection
          title="Recent Highlights"
          description="Days when you captured many moments"
          isEmpty={memoriesData.recent.length === 0}
          emptyMessage="No recent highlights found"
        >
          {memoriesData.recent.map((memory) => (
            <MemoryCard
              key={memory.iso_date}
              title={memory.date}
              images={memory.images}
              icon="clock"
              imageCount={memory.images.length}
            />
          ))}
        </MemorySection>
      )}

      {/* People Memories Section */}
      {memoriesData?.people && memoriesData.people.length > 0 && (
        <MemorySection
          title="People"
          description="Memories with the people you care about"
          isEmpty={memoriesData.people.length === 0}
          emptyMessage="No people memories found. Enable AI tagging to detect faces."
        >
          {memoriesData.people.map((memory) => (
            <MemoryCard
              key={memory.cluster_id}
              title={memory.person_name}
              subtitle={`${memory.image_count} ${memory.image_count === 1 ? 'photo' : 'photos'} total`}
              images={memory.images}
              icon="users"
              imageCount={memory.images.length}
            />
          ))}
        </MemorySection>
      )}

      {/* Tags/Themes Memories Section */}
      {memoriesData?.tags && memoriesData.tags.length > 0 && (
        <MemorySection
          title="Themes"
          description="Collections based on what's in your photos"
          isEmpty={memoriesData.tags.length === 0}
          emptyMessage="No theme memories found. Enable AI tagging to detect objects."
        >
          {memoriesData.tags.map((memory) => (
            <MemoryCard
              key={memory.tag_name}
              title={
                memory.tag_name.charAt(0).toUpperCase() +
                memory.tag_name.slice(1)
              }
              subtitle={`${memory.image_count} ${memory.image_count === 1 ? 'photo' : 'photos'} total`}
              images={memory.images}
              icon="tag"
              imageCount={memory.images.length}
            />
          ))}
        </MemorySection>
      )}

      {/* Empty State */}
      {memoriesData &&
        !memoriesData.on_this_day?.length &&
        !memoriesData.recent?.length &&
        !memoriesData.people?.length &&
        !memoriesData.tags?.length && (
          <div className="flex h-96 items-center justify-center">
            <div className="text-center">
              <Sparkles className="mx-auto h-16 w-16 text-gray-400" />
              <h3 className="mt-4 text-xl font-semibold text-gray-900 dark:text-gray-100">
                No Memories Yet
              </h3>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Add photos and enable AI tagging to create memories
              </p>
            </div>
          </div>
        )}
    </div>
  );
};

export default Memories;
