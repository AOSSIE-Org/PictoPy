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
  totalItems: number;
}

/**
 * App-wide alert showing the current background pass (tagging → indexing).
 * Hidden on Settings, which has its own bars. Needs router context.
 */
export const LibraryProcessingIndicator: React.FC = () => {
  const { phase, percentage, totalItems, semanticAvailable } =
    useLibraryProcessingStatus();
  const location = useLocation();

  // Dismissal is per-phase and invalidated when the library grows, so the
  // alert resurfaces when indexing starts or new media appears.
  const [dismissal, setDismissal] = useState<Dismissal | null>(null);
  const dismissed =
    dismissal !== null &&
    dismissal.phase === phase &&
    totalItems <= dismissal.totalItems;

  const onSettingsPage = location.pathname.includes(`/${ROUTES.SETTINGS}`);

  if (phase === 'idle' || dismissed || onSettingsPage) return null;

  const step = (n: number) => (semanticAvailable ? `Step ${n} of 2: ` : '');
  const description =
    phase === 'tagging'
      ? `${step(1)}Looking through your photos and videos to recognize what's in them.`
      : 'Step 2 of 2: Making your photos and videos searchable, so you can find them by describing them in your own words.';

  return (
    <BackgroundTaskAlert
      title="Getting your library ready"
      description={`${description} You can keep using the app.`}
      percentage={percentage}
      onDismiss={() => setDismissal({ phase, totalItems })}
    />
  );
};
