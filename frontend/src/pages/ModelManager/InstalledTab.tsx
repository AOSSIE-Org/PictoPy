import React, { useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useDispatch } from 'react-redux';
import { Trash2, CheckCircle2, ShieldCheck, Loader2 } from 'lucide-react';

import { usePictoQuery } from '@/hooks/useQueryExtension';
import { fetchModelStatus, deleteModel } from '@/api/api-functions';
import { useUserPreferences } from '@/hooks/useUserPreferences';
import { formatTierLabel, getErrorMessage } from '@/lib/utils';
import { showGlobalAlert } from '@/features/globalAlertSlice';
import { ConfirmDialog } from '@/components/ConfirmDialog/ConfirmDialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ModelTier } from '@/types/models';

const TIER_ORDER: ModelTier[] = ['nano', 'small', 'medium'];

export const InstalledTab: React.FC = () => {
  const queryClient = useQueryClient();
  const dispatch = useDispatch();
  const { preferences, updateYoloModelSize } = useUserPreferences();

  const [confirmOpen, setConfirmOpen] = useState(false);
  const [uninstallingTier, setUninstallingTier] = useState<{
    tier: ModelTier;
    objectKey: string;
    faceKey: string;
  } | null>(null);

  const [activatingTier, setActivatingTier] = useState<string | null>(null);
  const [isUninstalling, setIsUninstalling] = useState(false);

  const { data, isLoading, isError } = usePictoQuery({
    queryKey: ['models', 'status'],
    queryFn: fetchModelStatus,
  });

  const handleSetActive = async (tier: ModelTier) => {
    setActivatingTier(tier);
    try {
      await updateYoloModelSize(tier);
    } catch (err: any) {
      dispatch(
        showGlobalAlert({
          title: 'Activation Failed',
          message: getErrorMessage(err),
        }),
      );
    } finally {
      setActivatingTier(null);
    }
  };

  const handleUninstallConfirm = async () => {
    if (!uninstallingTier) return;
    setIsUninstalling(true);

    try {
      const [objOutcome, faceOutcome] = await Promise.allSettled([
        deleteModel(uninstallingTier.objectKey),
        deleteModel(uninstallingTier.faceKey),
      ]);

      const objFailed = objOutcome.status === 'rejected';
      const faceFailed = faceOutcome.status === 'rejected';

      if (!objFailed && !faceFailed) {
        // Both succeeded
        await queryClient.invalidateQueries({ queryKey: ['models', 'status'] });
      } else if (objFailed && faceFailed) {
        // Both failed
        dispatch(
          showGlobalAlert({
            title: 'Uninstall Failed',
            message: getErrorMessage(
              (objOutcome as PromiseRejectedResult).reason,
            ), // Show first error
          }),
        );
      } else {
        // Split outcome
        const successHalf = !objFailed
          ? 'Object detection model'
          : 'Face detection model';
        const failedHalf = objFailed
          ? 'Object detection model'
          : 'Face detection model';
        const errorDetails = getErrorMessage(
          objFailed
            ? (objOutcome as PromiseRejectedResult).reason
            : (faceOutcome as PromiseRejectedResult).reason,
        );

        dispatch(
          showGlobalAlert({
            title: 'Partial Uninstall',
            message: `${successHalf} was removed, but ${failedHalf} failed: ${errorDetails}`,
          }),
        );
        await queryClient.invalidateQueries({ queryKey: ['models', 'status'] });
      }
    } finally {
      setIsUninstalling(false);
      setUninstallingTier(null);
      setConfirmOpen(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="text-muted-foreground h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (isError || !data?.data) {
    return (
      <div className="text-destructive flex h-64 items-center justify-center">
        Failed to load installed models.
      </div>
    );
  }

  const models = data.data;

  // Group standard tiers
  const standardTiers = TIER_ORDER.map((tier) => {
    const objectModelKey = Object.keys(models).find(
      (key) =>
        models[key].feature === 'object_detection' &&
        models[key].tier === tier &&
        models[key].installed,
    );
    const faceModelKey = Object.keys(models).find(
      (key) =>
        models[key].feature === 'face_detection' &&
        models[key].tier === tier &&
        models[key].installed,
    );

    if (objectModelKey && faceModelKey) {
      const objModel = models[objectModelKey];
      const faceModel = models[faceModelKey];
      const combinedSize = (objModel.size_mb || 0) + (faceModel.size_mb || 0);
      return {
        tier,
        objectModelKey,
        faceModelKey,
        combinedSize,
      };
    }
    return null;
  }).filter(Boolean) as Array<{
    tier: ModelTier;
    objectModelKey: string;
    faceModelKey: string;
    combinedSize: number;
  }>;

  // Group required tiers (like facenet)
  const requiredModels = Object.entries(models)
    .filter(([_, model]) => model.tier === 'required' && model.installed)
    .map(([key, model]) => ({ key, ...model }));

  return (
    <div className="space-y-8">
      {/* Standard Tiers */}
      <section>
        <h2 className="mb-4 text-lg font-semibold">Installed Tiers</h2>
        {standardTiers.length === 0 ? (
          <p className="text-muted-foreground text-sm">
            No standard tiers installed.
          </p>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {standardTiers.map(
              ({ tier, objectModelKey, faceModelKey, combinedSize }) => {
                const isActive = preferences.YOLO_model_size === tier;
                const isActivating = activatingTier === tier;

                return (
                  <div
                    key={tier}
                    className="bg-card flex flex-col justify-between rounded-xl border p-5 shadow-sm"
                  >
                    <div>
                      <div className="mb-2 flex items-center justify-between">
                        <h3 className="text-lg font-medium">
                          {formatTierLabel(tier)}
                        </h3>
                        {isActive && (
                          <Badge
                            variant="secondary"
                            className="flex items-center gap-1 bg-green-100 text-green-700 hover:bg-green-100 dark:bg-green-900/30 dark:text-green-400"
                          >
                            <CheckCircle2 className="h-3 w-3" /> Active
                          </Badge>
                        )}
                      </div>
                      <p className="text-muted-foreground mb-4 text-sm">
                        ~{Math.round(combinedSize)} MB total size
                      </p>
                    </div>

                    <div className="mt-4 flex items-center justify-between gap-2">
                      <Button
                        variant="outline"
                        className="flex-1"
                        disabled={isActive || isActivating || isUninstalling}
                        onClick={() => handleSetActive(tier)}
                      >
                        {isActivating ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          'Set active'
                        )}
                      </Button>
                      <Button
                        variant="destructive"
                        size="icon"
                        disabled={isUninstalling}
                        onClick={() => {
                          setUninstallingTier({
                            tier,
                            objectKey: objectModelKey,
                            faceKey: faceModelKey,
                          });
                          setConfirmOpen(true);
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                );
              },
            )}
          </div>
        )}
      </section>

      {/* Required Tiers */}
      {requiredModels.length > 0 && (
        <section>
          <h2 className="mb-4 text-lg font-semibold">Always Installed</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {requiredModels.map(({ key, name, size_mb }) => (
              <div
                key={key}
                className="bg-card flex flex-col rounded-xl border p-5 opacity-80 shadow-sm"
              >
                <div className="mb-2 flex items-center justify-between">
                  <h3 className="text-lg font-medium">{name || key}</h3>
                  <ShieldCheck className="text-primary h-4 w-4" />
                </div>
                <p className="text-muted-foreground text-sm">
                  {size_mb
                    ? `~${Math.round(size_mb)} MB`
                    : 'Required core model'}
                </p>
                <div className="border-border/50 text-muted-foreground mt-4 border-t pt-4 text-xs">
                  System dependency (cannot be removed)
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title={`Uninstall ${uninstallingTier ? formatTierLabel(uninstallingTier.tier) : ''} Tier?`}
        description="This will remove both the object detection and face detection models for this size. You can re-download them later from the Available tab."
        confirmLabel={isUninstalling ? 'Uninstalling...' : 'Uninstall'}
        onConfirm={handleUninstallConfirm}
      />
    </div>
  );
};
