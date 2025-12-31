import { useState } from 'react';
import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchAllMemories } from '@/api/api-functions';
import { Memory } from '@/types/Memory';
import { MemoryCard } from '@/components/Memories/MemoryCard';
import { MemoryDetailView } from '@/components/Memories/MemoryDetailView';
import { EmptyMemoriesState } from '@/components/EmptyStates/EmptyMemoriesState';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

const Memories = () => {
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);

  const { data, isLoading, isSuccess, isError, error } = usePictoQuery({
    queryKey: ['memories'],
    queryFn: () => fetchAllMemories(),
  });

  useMutationFeedback(
    { isPending: isLoading, isSuccess, isError, error },
    {
      loadingMessage: 'Loading memories',
      showSuccess: false,
      errorTitle: 'Error',
      errorMessage: 'Failed to load memories. Please try again later.',
    },
  );

  const memories = (data?.data as Memory[]) || [];

  // If memory detail view is open, show that
  if (selectedMemory) {
    return (
      <MemoryDetailView
        memory={selectedMemory}
        onClose={() => setSelectedMemory(null)}
      />
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="flex h-full flex-col overflow-y-auto p-6">
        <h1 className="mb-6 text-2xl font-bold">Memories</h1>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="overflow-hidden">
              <CardContent className="p-0">
                <Skeleton className="h-48 w-full" />
                <div className="p-4">
                  <Skeleton className="mb-2 h-6 w-3/4" />
                  <Skeleton className="h-4 w-1/2" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  // Empty state
  if (memories.length === 0) {
    return <EmptyMemoriesState />;
  }

  // Main memories grid
  return (
    <div className="flex h-full flex-col overflow-y-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">Memories</h1>
        <p className="text-muted-foreground mt-2 text-sm">
          Auto-generated photo memories based on time and location
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {memories.map((memory) => (
          <MemoryCard
            key={memory.id}
            memory={memory}
            onClick={() => setSelectedMemory(memory)}
          />
        ))}
      </div>
    </div>
  );
};

export default Memories;
