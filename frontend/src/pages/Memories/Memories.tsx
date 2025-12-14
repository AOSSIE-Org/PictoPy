// src/pages/Memories/Memories.tsx

import { useState } from 'react';
import { useNavigate } from 'react-router';
import { Sparkles, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { MemoryCard } from '@/components/Media/MemoryCard';
import { EmptyMemoriesState } from '@/components/EmptyStates/EmptyMemoriesState';
import { usePictoQuery, usePictoMutation } from '@/hooks/useQueryExtension';
import { getAllMemories, generateMemories } from '@/api/api-functions/memories';
import { useMutationFeedback } from '@/hooks/useMutationFeedback';
import { useQueryClient } from '@tanstack/react-query';

export const Memories = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isGenerating, setIsGenerating] = useState(false);

  // Fetch all memories
  const {
    data: memoriesData,
    isLoading,
    isSuccess,
    isError,
    error,
  } = usePictoQuery({
    queryKey: ['memories'],
    queryFn: getAllMemories,
  });

  // Generate memories mutation
  const generateMutation = usePictoMutation({
    mutationFn: (forceRegenerate: boolean) =>
      generateMemories({ force_regenerate: forceRegenerate }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['memories'] });
      setIsGenerating(false);
    },
    onError: () => {
      setIsGenerating(false);
    },
  });

  useMutationFeedback(
    { isPending: isLoading, isSuccess, isError, error },
    {
      loadingMessage: 'Loading memories',
      showSuccess: false,
      errorTitle: 'Error',
      errorMessage: 'Failed to load memories. Please try again.',
    },
  );

  useMutationFeedback(
    {
      isPending: generateMutation.isPending,
      isSuccess: generateMutation.isSuccess,
      isError: generateMutation.isError,
      error: generateMutation.error,
    },
    {
      loadingMessage: 'Generating memories...',
      successTitle: 'Success',
      successMessage: 'Memories generated successfully!',
      errorTitle: 'Error',
      errorMessage: 'Failed to generate memories. Please try again.',
    },
  );

  const handleGenerate = (forceRegenerate: boolean = false) => {
    setIsGenerating(true);
    generateMutation.mutate(forceRegenerate);
  };

  const handleMemoryClick = (memoryId: string) => {
    navigate(`/memories/${memoryId}`);
  };

  const memories = memoriesData?.data || [];
  const hasMemories = memories.length > 0;

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-muted-foreground">Loading memories...</div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      {hasMemories && (
        <div className="flex items-center justify-between border-b p-6">
          <div>
            <h1 className="text-3xl font-bold">Memories</h1>
            <p className="mt-1 text-muted-foreground">
              Relive your favorite moments • {memories.length}{' '}
              {memories.length === 1 ? 'memory' : 'memories'}
            </p>
          </div>

          <Button
            onClick={() => handleGenerate(true)}
            disabled={isGenerating}
            className="gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isGenerating ? 'animate-spin' : ''}`} />
            Refresh Memories
          </Button>
        </div>
      )}

      {/* Content */}
      <div className="hide-scrollbar flex-1 overflow-y-auto p-6">
        {hasMemories ? (
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {memories.map((memory) => (
              <MemoryCard
                key={memory.id}
                memory={memory}
                onClick={() => handleMemoryClick(memory.id)}
              />
            ))}
          </div>
        ) : (
          <EmptyMemoriesState
            onGenerate={() => handleGenerate(false)}
            isGenerating={isGenerating}
          />
        )}
      </div>
    </div>
  );
};

export default Memories;