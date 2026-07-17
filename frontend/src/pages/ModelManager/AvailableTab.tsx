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
import { showInfoDialog } from '@/features/infoDialogSlice';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent } from '@/components/ui/card';
import {
  ModelTier,
  ModelStatusResponse,
  getModelTierDescription,
  SEMANTIC_BUNDLE_KEYS,
  SEMANTIC_BUNDLE_LABEL,
  SEMANTIC_BUNDLE_DESCRIPTION,
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

interface SemanticBundleInfo {
  tier: 'semantic';
  isPartial: boolean;
  combinedSize: number;
  isInstalledJustNow: boolean;
}

interface TierCardProps {
  tier: string;
  title?: string;
  description?: string;
  isPartial: boolean;
  combinedSize: number;
  isRecommended?: boolean;
  taskId: string | null;
  onInstall: (tier: string) => void;
  onComplete: (tier: string) => void;
  isInstalledJustNow: boolean;
}

const TierCard: React.FC<TierCardProps> = ({
  tier,
  title,
  description,
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
          <h3 className="text-lg font-medium">
            {title || formatTierLabel(tier as ModelTier)}
          </h3>
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
          {description || getModelTierDescription(tier as ModelTier)}
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

  const handleInstall = async (tier: string) => {
    try {
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
    (tier: string) => {
      if (tier === 'semantic' && !installedJustNow.has('semantic')) {
        // Existing photos are embedded by a backfill that starts post-install
        dispatch(
          showInfoDialog({
            title: 'Semantic Search Installed',
            message:
              'PictoPy is now getting your photos ready in the background. ' +
              'Once done, you can find photos by describing them in your ' +
              "own words (like 'beach sunset' or 'birthday party'). " +
              'You can keep using the app while it works.',
          }),
        );
      }
      setInstalledJustNow((prev) => {
        if (prev.has(tier)) return prev;
        return new Set(prev).add(tier);
      });
    },
    [dispatch, installedJustNow, setInstalledJustNow],
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

  const availableTiers = TIER_ORDER.map((tier) => {
    const objModel = Object.values(models).find(
      (m) => m.feature === 'object_detection' && m.tier === tier,
    );
    const faceModel = Object.values(models).find(
      (m) => m.feature === 'face_detection' && m.tier === tier,
    );

    if (!objModel || !faceModel) return null;

    const objInstalled = objModel.installed;
    const faceInstalled = faceModel.installed;

    if (objInstalled && faceInstalled && !installedJustNow.has(tier)) {
      return null;
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
      isInstalledJustNow: installedJustNow.has(tier),
    };
  }).filter(Boolean) as Array<{
    tier: ModelTier;
    isPartial: boolean;
    combinedSize: number;
    isInstalledJustNow: boolean;
  }>;

  const semanticModels = SEMANTIC_BUNDLE_KEYS.map((k) => models[k]).filter(
    Boolean,
  );
  const semanticInstalledCount = semanticModels.filter(
    (m) => m.installed,
  ).length;
  const semanticSize = semanticModels.reduce(
    (acc, m) => acc + (m.size_mb || 0),
    0,
  );
  const semanticInstalledJustNow = installedJustNow.has('semantic');

  let semanticBundle: SemanticBundleInfo | null = null;
  if (
    semanticModels.length === 3 &&
    (semanticInstalledCount < 3 || semanticInstalledJustNow)
  ) {
    semanticBundle = {
      tier: 'semantic',
      isPartial: semanticInstalledCount > 0 && semanticInstalledCount < 3,
      combinedSize: semanticSize,
      isInstalledJustNow: semanticInstalledJustNow,
    };
  }

  if (availableTiers.length === 0 && !semanticBundle) {
    return (
      <div className="flex items-center justify-center py-12">
        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center space-y-4 p-6 text-center">
            <div className="relative">
              <div className="bg-primary/10 flex h-16 w-16 items-center justify-center rounded-full">
                <CheckCircle2 className="text-primary h-8 w-8" />
              </div>
              <div className="absolute -top-1 -right-1">
                <Sparkles className="h-5 w-5 text-yellow-500" />
              </div>
            </div>
            <Badge variant="secondary" className="px-3 py-1">
              Up to Date
            </Badge>
            <h1 className="text-xl font-bold tracking-tight">
              All Tiers Installed
            </h1>
            <p className="text-muted-foreground text-sm">
              You have successfully downloaded and installed all available AI
              model tiers.
            </p>
            <div className="bg-muted/50 rounded-lg p-3">
              <p className="text-muted-foreground text-xs">
                Head over to the Installed tab to manage your models or change
                your active selection.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {availableTiers.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-semibold">Standard Tiers</h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {availableTiers.map((bundle) => {
              if (!bundle) return null;
              const isRecommended =
                hwData?.data?.recommended_tier === bundle.tier;
              return (
                <TierCard
                  key={bundle.tier}
                  tier={bundle.tier}
                  isPartial={bundle.isPartial}
                  combinedSize={bundle.combinedSize}
                  isRecommended={isRecommended}
                  taskId={downloadingTiers.get(bundle.tier) || null}
                  onInstall={handleInstall}
                  onComplete={handleComplete}
                  isInstalledJustNow={bundle.isInstalledJustNow}
                />
              );
            })}
          </div>
        </section>
      )}

      {semanticBundle && (
        <section>
          <h2 className="mb-4 text-lg font-semibold">Additional Features</h2>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            <TierCard
              tier={semanticBundle.tier}
              title={SEMANTIC_BUNDLE_LABEL}
              description={SEMANTIC_BUNDLE_DESCRIPTION}
              isPartial={semanticBundle.isPartial}
              combinedSize={semanticBundle.combinedSize}
              taskId={downloadingTiers.get('semantic') || null}
              onInstall={handleInstall}
              onComplete={handleComplete}
              isInstalledJustNow={semanticBundle.isInstalledJustNow}
            />
          </div>
        </section>
      )}
    </div>
  );
};
