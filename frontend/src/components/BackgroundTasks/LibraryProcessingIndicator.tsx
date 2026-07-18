import React, { useState } from 'react';
import { useLocation } from 'react-router';
import { BackgroundTaskAlert } from './BackgroundTaskAlert';
import {
  useLibraryProcessingStatus,
  LibraryProcessingPhase,
} from '@/hooks/useLibraryProcessingStatus';
import { ROUTES } from '@/constants/routes';

interface Dismissal {
  phase: LibraryProcessingPhase;
  totalImages: number;
}

/**
 * App-wide alert showing the current background pass (tagging → indexing).
 * Hidden on Settings, which has its own bars. Needs router context.
 */
export const LibraryProcessingIndicator: React.FC = () => {
  const { phase, percentage, totalImages, semanticAvailable } =
    useLibraryProcessingStatus();
  const location = useLocation();

  // Dismissal is per-phase and invalidated when the library grows, so the
  // alert resurfaces when indexing starts or new photos appear.
  const [dismissal, setDismissal] = useState<Dismissal | null>(null);
  const dismissed =
    dismissal !== null &&
    dismissal.phase === phase &&
    totalImages <= dismissal.totalImages;

  const onSettingsPage = location.pathname.includes(`/${ROUTES.SETTINGS}`);

  if (phase === 'idle' || dismissed || onSettingsPage) return null;

  const step = (n: number) => (semanticAvailable ? `Step ${n} of 2: ` : '');
  const description =
    phase === 'tagging'
      ? `${step(1)}Looking through your photos to recognize what's in them.`
      : 'Step 2 of 2: Making your photos searchable, so you can find them by describing them in your own words.';

  return (
    <BackgroundTaskAlert
      title="Getting your photos ready"
      description={`${description} You can keep using the app.`}
      percentage={percentage}
      onDismiss={() => setDismissal({ phase, totalImages })}
    />
  );
};
