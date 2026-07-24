import React, { useEffect, useCallback, useState } from 'react';
import {
  Cpu,
  ChevronDown,
  Zap,
  Trash2,
  Clapperboard,
  HardDrive,
} from 'lucide-react';

import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';

import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import { getCurrentWindow } from '@tauri-apps/api/window';

import { useUserPreferences } from '@/hooks/useUserPreferences';
import { purgeVideoFrameCache } from '@/api/api-functions';
import SettingsCard from './SettingsCard';
import { cn, formatTierLabel } from '@/lib/utils';
import { BACKEND_URL } from '@/config/Backend';
import {
  getInstalledModelTiers,
  MODEL_TIERS,
  type ModelStatusResponse,
  type ModelTier,
} from '@/types/models';

/**
 * Component for managing user preferences in settings
 */
// Coarse enough to be a meaningful cost tradeoff, fine enough to matter.
const FRAME_INTERVAL_OPTIONS = [2, 5, 10, 30];

const UserPreferencesCard: React.FC = () => {
  const {
    preferences,
    updateYoloModelSize,
    toggleGpuAcceleration,
    updateVideoFrameInterval,
    refetch,
  } = useUserPreferences();
  const [installedTiers, setInstalledTiers] = useState<ModelTier[]>([]);
  const [loadingTiers, setLoadingTiers] = useState(true);
  const [tierFetchError, setTierFetchError] = useState<string | null>(null);
  const [purgeState, setPurgeState] = useState<'idle' | 'purging' | 'done'>(
    'idle',
  );
  // Collapsed by default: video tagging is a niche setting, so it stays out
  // of the way until a user with videos goes looking for it.
  const [videoSettingsOpen, setVideoSettingsOpen] = useState(false);

  const handlePurgeFrameCache = useCallback(async () => {
    setPurgeState('purging');
    try {
      await purgeVideoFrameCache();
      setPurgeState('done');
    } catch (err) {
      console.error('Failed to purge video frame cache', err);
      setPurgeState('idle');
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    const fetchModelStatus = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/models/status`, {
          signal: controller.signal,
        });

        if (!res.ok) {
          throw new Error(`Failed to load models (${res.status})`);
        }

        const data: ModelStatusResponse = await res.json();

        if (controller.signal.aborted) {
          return;
        }

        if (data.success && data.data) {
          setInstalledTiers(getInstalledModelTiers(data.data));
          setTierFetchError(null);
        } else {
          setTierFetchError('Failed to load models');
        }
      } catch (err) {
        if (controller.signal.aborted) {
          return;
        }

        console.error('Failed to fetch model status', err);
        setTierFetchError(
          err instanceof Error ? err.message : 'Failed to load models',
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoadingTiers(false);
        }
      }
    };

    fetchModelStatus();

    return () => {
      controller.abort();
    };
  }, []);

  // Model Manager emits 'models-updated' on close to refresh installed-tiers and active preference.
  const refreshAfterModelManager = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/models/status`);
      if (res.ok) {
        const data: ModelStatusResponse = await res.json();
        if (data.success && data.data) {
          setInstalledTiers(getInstalledModelTiers(data.data));
        }
      }
    } catch (err) {
      console.error('Failed to refresh model status', err);
    }
    refetch().catch(console.error);
  }, [refetch]);

  useEffect(() => {
    const unlistenModelsPromise = listen(
      'models-updated',
      refreshAfterModelManager,
    );
    const unlistenFocusPromise = getCurrentWindow().onFocusChanged(
      ({ payload: focused }) => {
        if (focused) {
          refreshAfterModelManager();
        }
      },
    );

    return () => {
      unlistenModelsPromise.then((unlisten) => unlisten());
      unlistenFocusPromise.then((unlisten) => unlisten());
    };
  }, [refreshAfterModelManager]);

  return (
    <SettingsCard
      icon={Cpu}
      title="User Preferences"
      description="Configure AI model settings and performance options"
    >
      <div className="space-y-6">
        {/* YOLO Model Size Setting */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <Label
              htmlFor="yolo-model"
              className="text-foreground text-sm font-medium"
            >
              YOLO Model Size
            </Label>
            <p className="text-muted-foreground text-xs">
              Choose the AI model size for object detection (larger models are
              more accurate but slower)
            </p>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                className="w-32 cursor-pointer justify-between"
              >
                {formatTierLabel(preferences.YOLO_model_size)}
                <ChevronDown className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-32">
              {MODEL_TIERS.map((tier) =>
                installedTiers.includes(tier) ? (
                  <DropdownMenuItem
                    key={tier}
                    className="cursor-pointer"
                    onClick={() =>
                      updateYoloModelSize(tier).catch(console.warn)
                    }
                  >
                    {formatTierLabel(tier)}
                  </DropdownMenuItem>
                ) : null,
              )}
              {loadingTiers && (
                <DropdownMenuItem disabled>Loading models...</DropdownMenuItem>
              )}
              {!loadingTiers && tierFetchError && (
                <DropdownMenuItem disabled>
                  Failed to load models
                </DropdownMenuItem>
              )}
              {!loadingTiers &&
                !tierFetchError &&
                installedTiers.length === 0 && (
                  <DropdownMenuItem disabled>
                    No models installed
                  </DropdownMenuItem>
                )}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="hover:text-secondary cursor-pointer font-medium"
                onSelect={() => {
                  invoke('open_model_manager').catch(console.error);
                }}
              >
                Configure...
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* GPU Acceleration Setting */}
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <Label
              htmlFor="gpu-acceleration"
              className="text-foreground text-sm font-medium"
            >
              GPU Acceleration
            </Label>
            <p className="text-muted-foreground text-xs">
              Enable GPU acceleration for faster AI processing (requires
              compatible hardware)
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-gray-500" />
            <Switch
              className="cursor-pointer"
              id="gpu-acceleration"
              checked={preferences.GPU_Acceleration}
              onCheckedChange={() =>
                toggleGpuAcceleration().catch(console.warn)
              }
            />
          </div>
        </div>

        {/* Video Tagging: a collapsible group so these niche controls don't
            clutter the panel for users who only have photos. */}
        <div className="border-border rounded-lg border">
          <button
            type="button"
            aria-expanded={videoSettingsOpen}
            aria-controls="video-tagging-settings"
            onClick={() => setVideoSettingsOpen((open) => !open)}
            className="flex w-full cursor-pointer items-center justify-between gap-3 rounded-lg p-4 text-left transition-colors"
          >
            <div className="flex items-start gap-3">
              <Clapperboard className="text-muted-foreground mt-0.5 h-5 w-5 shrink-0" />
              <div className="space-y-1">
                <span className="text-foreground text-sm font-medium">
                  Video Tagging
                </span>
                <p className="text-muted-foreground text-xs">
                  Control how videos are sampled for AI tags and manage the
                  frames cached on disk.
                </p>
              </div>
            </div>
            <ChevronDown
              className={cn(
                'text-muted-foreground h-4 w-4 shrink-0 transition-transform',
                videoSettingsOpen && 'rotate-180',
              )}
            />
          </button>

          {videoSettingsOpen && (
            <div
              id="video-tagging-settings"
              className="border-border space-y-6 border-t p-4"
            >
              {/* Video Keyframe Interval Setting */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label
                    htmlFor="video-frame-interval"
                    className="text-foreground text-sm font-medium"
                  >
                    Keyframe Interval
                  </Label>
                  <p className="text-muted-foreground text-xs">
                    How often a frame is sampled from a video for tagging.
                    Shorter intervals catch more detail but take longer to
                    process. Applies to videos tagged from now on.
                  </p>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant="outline"
                      className="w-32 cursor-pointer justify-between"
                    >
                      {preferences.Video_Frame_Interval}s
                      <ChevronDown className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-32">
                    {FRAME_INTERVAL_OPTIONS.map((seconds) => (
                      <DropdownMenuItem
                        key={seconds}
                        className="cursor-pointer"
                        onClick={() =>
                          updateVideoFrameInterval(seconds).catch(console.warn)
                        }
                      >
                        {seconds} seconds
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>

              {/* Video Frame Cache */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <Label className="text-foreground text-sm font-medium">
                    Frame Cache
                  </Label>
                  <p className="text-muted-foreground text-xs">
                    Reclaim the disk space used by sampled video frames.
                    Existing tags and video search keep working.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <HardDrive className="h-4 w-4 text-gray-500" />
                  <Button
                    variant="outline"
                    className="cursor-pointer"
                    disabled={purgeState === 'purging'}
                    onClick={handlePurgeFrameCache}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    {purgeState === 'purging'
                      ? 'Clearing...'
                      : purgeState === 'done'
                        ? 'Cleared'
                        : 'Clear cache'}
                  </Button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </SettingsCard>
  );
};

export default UserPreferencesCard;
