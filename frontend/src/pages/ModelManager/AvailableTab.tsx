import React from 'react';
import { useDispatch } from 'react-redux';
import {
  DownloadCloud,
  CheckCircle2,
  Loader2,
  AlertTriangle,
  Check,
  Sparkles,
} from 'lucide-react';

import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchHardwareInfo, setupModelTier } from '@/api/api-functions';
import { formatTierLabel, getErrorMessage } from '@/lib/utils';
import { showGlobalAlert } from '@/features/globalAlertSlice';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent } from '@/components/ui/card';
import {
  ModelTier,
  ModelStatusResponse,
  getModelTierDescription,
} from '@/types/models';
import { useModelDownloadProgress } from '@/hooks/useModelDownloadProgress';

const TIER_ORDER: ModelTier[] = ['nano', 'small', 'medium'];

export interface AvailableTabProps {
  statusData?: ModelStatusResponse;
  isLoading: boolean;
  isError: boolean;
  downloadingTiers: Map<string, string>;
  setDownloadingTiers: React.Dispatch<
    React.SetStateAction<Map<string, string>>
  >;
  installedJustNow: Set<string>;
  setInstalledJustNow: React.Dispatch<React.SetStateAction<Set<string>>>;
}

interface TierCardProps {
  tier: ModelTier;
  isPartial: boolean;
  combinedSize: number;
  isRecommended: boolean;
  taskId: string | null;
  onInstall: (tier: ModelTier) => Promise<void>;
  onComplete: (tier: ModelTier) => void;
  isInstalledJustNow: boolean;
}

const TierCard: React.FC<TierCardProps> = ({
  tier,
  isPartial,
  combinedSize,
  isRecommended,
  taskId,
  onInstall,
  onComplete,
  isInstalledJustNow,
}) => {
  const { status, percent, modelKey } = useModelDownloadProgress(taskId);

  React.useEffect(() => {
    if (status === 'complete') {
      onComplete(tier);
    }
  }, [status, onComplete, tier]);

  const isDownloading = taskId !== null && !isInstalledJustNow;
  const displayPercent = isInstalledJustNow ? 100 : percent;

  return (
    <div
      className={`flex flex-col justify-between rounded-xl border p-5 shadow-sm ${
        isRecommended ? 'bg-primary/5' : 'bg-card'
      }`}
    >
      <div>
        {isRecommended && (
          <div className="mb-2 flex items-center justify-between">
            <p className="text-primary text-xs font-semibold tracking-wide uppercase">
              Recommended for your hardware
            </p>
            <CheckCircle2 className="text-primary h-5 w-5 shrink-0" />
          </div>
        )}
        <div
          className={`mb-2 flex items-center justify-between ${isRecommended ? 'mt-3' : ''}`}
        >
          <h3 className="text-lg font-medium">{formatTierLabel(tier)}</h3>
          {isPartial && (
            <Badge
              variant="secondary"
              className="flex items-center gap-1 bg-amber-100 text-amber-700 hover:bg-amber-100 dark:bg-amber-900/30 dark:text-amber-400"
            >
              <AlertTriangle className="h-3 w-3" /> Needs Repair
            </Badge>
          )}
        </div>
        <p className="text-muted-foreground mt-1 mb-2 text-sm leading-relaxed">
          {getModelTierDescription(tier)}
        </p>
        <p className="text-muted-foreground mb-4 text-xs">
          ~{Math.round(combinedSize)} MB total size
        </p>
      </div>

      <div className="mt-4 flex flex-col gap-4">
        <div className="flex items-center justify-between gap-2">
          <Button
            variant={isRecommended ? 'default' : 'outline'}
            className="flex-1"
            disabled={isInstalledJustNow || isDownloading}
            onClick={() => onInstall(tier)}
          >
            {isInstalledJustNow ? (
              <>
                <CheckCircle2 className="mr-2 h-4 w-4 text-green-500" />{' '}
                Installed
              </>
            ) : isDownloading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Installing...
              </>
            ) : isPartial ? (
              'Finish Install'
            ) : (
              <>
                <DownloadCloud className="mr-2 h-4 w-4" /> Install
              </>
            )}
          </Button>
        </div>

        {(status === 'downloading' || isInstalledJustNow) && (
          <div className="w-full space-y-2 px-1">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium">
                {isInstalledJustNow
                  ? 'Download complete'
                  : `Downloading ${modelKey || 'models'}…`}
              </span>
              <span
                className={
                  isInstalledJustNow
                    ? 'flex items-center gap-1 text-green-500 tabular-nums'
                    : 'text-muted-foreground tabular-nums'
                }
              >
                {isInstalledJustNow && <Check className="h-3 w-3" />}
                {displayPercent}%
              </span>
            </div>
            <Progress
              value={displayPercent}
              className="bg-muted"
              indicatorClassName={
                isInstalledJustNow ? 'bg-green-500' : 'bg-blue-500'
              }
            />
          </div>
        )}
      </div>
    </div>
  );
};

export const AvailableTab: React.FC<AvailableTabProps> = ({
  statusData,
  isLoading,
  isError,
  downloadingTiers,
  setDownloadingTiers,
  installedJustNow,
  setInstalledJustNow,
}) => {
  const dispatch = useDispatch();

  const { data: hwData } = usePictoQuery({
    queryKey: ['models', 'hardware'],
    queryFn: fetchHardwareInfo,
  });

  const handleInstall = async (tier: ModelTier) => {
    try {
      // Empty string is an intentional sentinel meaning "install triggered, awaiting real task_id from POST /setup"
      setDownloadingTiers((prev) => new Map(prev).set(tier, ''));
      const data = await setupModelTier(tier);
      setDownloadingTiers((prev) =>
        new Map(prev).set(tier, data.task_id || ''),
      );
    } catch (err) {
      setDownloadingTiers((prev) => {
        const next = new Map(prev);
        next.delete(tier);
        return next;
      });
      dispatch(
        showGlobalAlert({
          title: 'Install Failed',
          message: getErrorMessage(err),
        }),
      );
    }
  };

  const handleComplete = React.useCallback(
    (tier: ModelTier) => {
      setInstalledJustNow((prev) => {
        if (prev.has(tier)) return prev;
        return new Set(prev).add(tier);
      });
    },
    [setInstalledJustNow],
  );

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="text-muted-foreground h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (isError || !statusData?.data) {
    return (
      <div className="text-destructive flex h-64 items-center justify-center">
        Failed to load available models.
      </div>
    );
  }

  const models = statusData.data;

  // Group and classify tiers
  const availableTiers = TIER_ORDER.map((tier) => {
    const objModel = Object.values(models).find(
      (m) => m.feature === 'object_detection' && m.tier === tier,
    );
    const faceModel = Object.values(models).find(
      (m) => m.feature === 'face_detection' && m.tier === tier,
    );

    if (!objModel || !faceModel) return null; // Should never happen unless registry is broken

    const objInstalled = objModel.installed;
    const faceInstalled = faceModel.installed;

    if (objInstalled && faceInstalled && !installedJustNow.has(tier)) {
      return null; // Fully installed and not just completed, handled by InstalledTab
    }

    const isPartial =
      (objInstalled || faceInstalled) &&
      !downloadingTiers.has(tier) &&
      !installedJustNow.has(tier);
    const combinedSize = (objModel.size_mb || 0) + (faceModel.size_mb || 0);

    return {
      tier,
      isPartial,
      combinedSize,
    };
  }).filter(Boolean) as Array<{
    tier: ModelTier;
    isPartial: boolean;
    combinedSize: number;
  }>;

  return (
    <div className="space-y-8">
      <section>
        <h2 className="mb-4 text-lg font-semibold">Available Tiers</h2>
        {availableTiers.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <Card className="w-full max-w-md">
              <CardContent className="flex flex-col items-center space-y-4 p-6 text-center">
                {/* Icon */}
                <div className="relative">
                  <div className="bg-primary/10 flex h-16 w-16 items-center justify-center rounded-full">
                    <CheckCircle2 className="text-primary h-8 w-8" />
                  </div>
                  <div className="absolute -top-1 -right-1">
                    <Sparkles className="h-5 w-5 text-yellow-500" />
                  </div>
                </div>

                {/* Badge */}
                <Badge variant="secondary" className="px-3 py-1">
                  Up to Date
                </Badge>

                {/* Title */}
                <h1 className="text-xl font-bold tracking-tight">
                  All Tiers Installed
                </h1>

                {/* Message */}
                <p className="text-muted-foreground text-sm">
                  You have successfully downloaded and installed all available
                  AI model tiers.
                </p>

                {/* Additional Info */}
                <div className="bg-muted/50 rounded-lg p-3">
                  <p className="text-muted-foreground text-xs">
                    Head over to the Installed tab to manage your models or
                    change your active selection.
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {availableTiers.map(({ tier, isPartial, combinedSize }) => {
              const taskId = downloadingTiers.has(tier)
                ? downloadingTiers.get(tier) || ''
                : null;
              const isRecommended = hwData?.data?.recommended_tier === tier;

              return (
                <TierCard
                  key={tier}
                  tier={tier}
                  isPartial={isPartial}
                  combinedSize={combinedSize}
                  isRecommended={isRecommended}
                  taskId={taskId}
                  onInstall={handleInstall}
                  onComplete={handleComplete}
                  isInstalledJustNow={installedJustNow.has(tier)}
                />
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
};
