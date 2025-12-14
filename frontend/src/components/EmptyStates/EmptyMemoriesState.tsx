// src/components/EmptyStates/EmptyMemoriesState.tsx

import { Album, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface EmptyMemoriesStateProps {
  onGenerate: () => void;
  isGenerating: boolean;
}

export const EmptyMemoriesState = ({
  onGenerate,
  isGenerating,
}: EmptyMemoriesStateProps) => {
  return (
    <div className="flex h-full flex-col items-center justify-center px-4 text-center">
      <div className="mb-6 rounded-full bg-primary/10 p-6">
        <Album className="h-16 w-16 text-primary" />
      </div>

      <h2 className="mb-2 text-2xl font-semibold">No Memories Yet</h2>

      <p className="mb-6 max-w-md text-muted-foreground">
        Memories are automatically created from your photos based on dates and
        locations. Generate memories to see your photo journey come to life!
      </p>

      <Button
        onClick={onGenerate}
        disabled={isGenerating}
        size="lg"
        className="gap-2"
      >
        <Sparkles className="h-5 w-5" />
        {isGenerating ? 'Generating Memories...' : 'Generate Memories'}
      </Button>

      <div className="mt-8 rounded-lg bg-muted/50 p-4 text-sm text-muted-foreground">
        <p className="font-medium">💡 Tip:</p>
        <p className="mt-1">
          For best results, make sure your photos have date information in their
          metadata. Photos with location data will create even better memories!
        </p>
      </div>
    </div>
  );
};